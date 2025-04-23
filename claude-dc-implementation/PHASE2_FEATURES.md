# Claude DC Phase 2 Features Documentation

This document provides comprehensive documentation for all Phase 2 features implemented in Claude DC.

## Overview

Phase 2 enhances Claude DC with six major capabilities:

1. **Streaming Responses**: Real-time, token-by-token output from Claude
2. **Tool Integration in Stream**: Seamless tool use during streaming
3. **Prompt Caching**: Efficient token usage with Anthropic's prompt caching beta
4. **128K Extended Output**: Support for very long responses (up to ~128k tokens)
5. **Stability Fixes**: Improved reliability with full conversation context
6. **Real-Time Tool Output**: Live streaming of tool results as they execute

## 1. Streaming Responses

Streaming displays Claude's responses token-by-token in real time, providing a more interactive experience and faster perceived response times.

### Implementation

The streaming implementation is in `loop.py` and uses the `stream=True` parameter in the Anthropic API call. Key components:

```python
# In sampling_loop function
api_params = {
    "max_tokens": max_tokens,
    "messages": messages,
    "model": model,
    "system": [system],
    "tools": tool_collection.to_params(),
    "stream": ENABLE_STREAMING  # Enable streaming (default: True)
}
```

The streaming process handles different event types:
- `content_block_start`: New content (text, thinking, or tool use)
- `content_block_delta`: Incremental content updates
- `message_stop`: End of the message

### UI Integration

The Streamlit UI (`streamlit.py`) processes streamed content with the `_streaming_output_callback` function:

```python
def _streaming_output_callback(content_block):
    # Handle streamed content from Claude API
    if isinstance(content_block, dict) and content_block.get("is_delta", False):
        if content_block["type"] == "text":
            # Update text message with delta
            delta_text = content_block.get("text", "")
            st.session_state.current_message_text += delta_text
            if st.session_state.current_message_placeholder:
                st.session_state.current_message_placeholder.markdown(
                    st.session_state.current_message_text
                )
```

## 2. Tool Integration in Stream

Claude can use tools mid-response without disrupting the streaming flow. The text already displayed remains visible, the tool executes, and then Claude continues the response.

### Implementation

Tool integration during streaming is handled by carefully processing tool use events in the stream:

```python
# In sampling_loop function, when processing a content_block_start event
if event_type == "content_block_start":
    # New content block started
    current_block = event.content_block
    content_blocks.append(current_block)
    
    # Convert block to dict for callback
    block_dict = {"type": getattr(current_block, "type", "unknown")}
    
    # Handle tool use blocks
    if hasattr(current_block, "name") and getattr(current_block, "type", None) == "tool_use":
        block_dict["name"] = current_block.name
        block_dict["input"] = getattr(current_block, "input", {})
        block_dict["id"] = getattr(current_block, "id", "unknown")
    
    # Send to output callback
    output_callback(block_dict)
```

Tools are executed after the response is processed, but their activation is displayed in real-time during the stream.

## 3. Prompt Caching

Prompt caching avoids recomputing repeated context, significantly reducing token usage and improving response speed for longer conversations.

### Implementation

Prompt caching uses Anthropic's beta feature and marks appropriate messages as ephemeral:

```python
# In sampling_loop function
if ENABLE_PROMPT_CACHING:
    # Mark the last few user messages as ephemeral for caching
    processed_messages = []
    user_messages_count = sum(1 for msg in messages if msg.get("role") == "user")
    ephemeral_count = min(2, max(0, user_messages_count - 1))  # Mark up to 2 recent messages
    
    if ephemeral_count > 0:
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                # Create a copy of the message
                msg_copy = msg.copy()
                # Check if this is one of the last few user messages (but not the very last)
                if i >= len(messages) - (ephemeral_count + 1) and i < len(messages) - 1:
                    # Add cache_control: ephemeral to this message
                    msg_copy["cache_control"] = "ephemeral"
                    logger.info(f"Marked message {i} as ephemeral for caching")
                processed_messages.append(msg_copy)
            else:
                processed_messages.append(msg)
        
        messages = processed_messages
```

The beta flag is added to the API call:
```python
# Add prompt caching beta flag if enabled
if ENABLE_PROMPT_CACHING:
    beta_flags.append(PROMPT_CACHING_BETA_FLAG)
    logger.info(f"Added prompt caching beta flag: {PROMPT_CACHING_BETA_FLAG}")
```

## 4. 128K Extended Output

Extended output allows Claude to generate very long responses (up to ~128k tokens), which is useful for complex questions requiring detailed explanations.

### Implementation

Extended output uses Anthropic's beta feature with appropriate token allocation:

```python
# Constants for token limits
DEFAULT_MAX_TOKENS = 65536  # ~64k max output
DEFAULT_THINKING_BUDGET = 32768  # ~32k thinking budget

# In sampling_loop function
# Add extended output beta flag if enabled
if ENABLE_EXTENDED_OUTPUT:
    beta_flags.append(OUTPUT_128K_BETA_FLAG)
    logger.info(f"Added extended output beta flag: {OUTPUT_128K_BETA_FLAG}")
```

Thinking budget is allocated to optimize token usage:
```python
# Add thinking budget if enabled
if ENABLE_THINKING and thinking_budget:
    api_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    logger.info(f"Added thinking budget: {thinking_budget}")
```

## 5. Stability Fixes

Various stability improvements ensure reliable operation even with large context windows and complex tools.

### Key Fixes

1. **Beta Flag Management**: Robust error handling for beta flags with fallback options
   ```python
   try:
       # First try with all parameters
       stream = client.messages.create(**api_params)
   except TypeError as e:
       # If 'beta' parameter is causing issues, remove it and try again
       if "got an unexpected keyword argument 'beta'" in str(e):
           logger.warning("Beta parameter not supported, removing it and retrying")
           api_params.pop('beta', None)
           # Try API call again without the unsupported parameters
           stream = client.messages.create(**api_params)
   ```

2. **Token-Efficient Tools**: Disabled by default for stability
   ```python
   # Token-efficient tools beta is disabled by default
   ENABLE_TOKEN_EFFICIENT = get_bool_env('ENABLE_TOKEN_EFFICIENT', False)
   ```

3. **Streamlined Error Handling**: Better recovery from errors during streaming

4. **Version Compatibility**: Works with different versions of the Anthropic SDK
   ```python
   if hasattr(current_block, "model_dump"):
       # New SDK versions
       block_dict = current_block.model_dump()
   else:
       # Create a dict with minimal properties for older versions
       block_dict = {"type": getattr(current_block, "type", "unknown")}
   ```

## 6. Real-Time Tool Output

Tool outputs (like command results) are streamed to the UI in real-time, providing immediate feedback during longer operations.

### Implementation

Tool streaming is implemented with a callback system:

```python
# Configure tool collection for streaming if supported
for tool in tool_collection.tools:
    if hasattr(tool, 'set_stream_callback'):
        tool.set_stream_callback(
            lambda chunk, tid=tool_id: tool_output_callback(
                ToolResult(output=chunk, error=None),
                tid
            )
        )
```

The UI handles streaming tool output with placeholders:
```python
def _tool_output_callback(tool_output, tool_id, tool_state):
    """Handle tool execution results including streaming chunks."""
    # Check if this is a streaming chunk or final result
    is_streaming = (
        hasattr(tool_output, 'output') and 
        tool_output.output and 
        not tool_output.base64_image and
        not tool_output.error
    )
    
    # For streaming output, update existing tool output if possible
    if is_streaming:
        # Get or create placeholder for streaming content
        if tool_id not in st.session_state.tools:
            # First chunk for this tool - create placeholder
            with st.chat_message(Sender.TOOL.value):
                placeholder = st.empty()
                # Update placeholder with latest content
                placeholder.code(tool_output.output, language="bash")
```

## Configuration and Feature Flags

All features can be controlled with environment variables defined in `__init__.py`:

```python
# Feature flags - control which features are enabled
# Read from environment with fallbacks
ENABLE_PROMPT_CACHING = get_bool_env('ENABLE_PROMPT_CACHING', True)
ENABLE_EXTENDED_OUTPUT = get_bool_env('ENABLE_EXTENDED_OUTPUT', True)
ENABLE_THINKING = get_bool_env('ENABLE_THINKING', True)
ENABLE_TOKEN_EFFICIENT = get_bool_env('ENABLE_TOKEN_EFFICIENT', False)
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)
```

## Testing and Validation

A comprehensive test script is available at `test_phase2_features.py`. This script tests all Phase 2 features in sequence:

1. **Test 1**: Basic streaming and tool use
2. **Test 2**: Tool integration and prompt caching
3. **Test 3**: Extended output with thinking budget

To run the tests:
```bash
python claude-dc-implementation/computeruse/current_experiment/test_phase2_features.py
```

## Deployment

To deploy these features to production:

1. Back up the current production code
2. Run the integration script:
   ```bash
   python claude-dc-implementation/computeruse/current_experiment/integrate_phase2.py
   ```
3. Restart Claude DC:
   ```bash
   ./claude_dc_launch.sh
   ```
4. Verify all features are working correctly

## Troubleshooting

Common issues and solutions:

1. **API Errors with Beta Flags**: If you encounter errors related to beta flags, try removing specific flags or updating the Anthropic SDK.

2. **Memory Issues with Extended Output**: If you experience memory issues with very long outputs, try reducing the `max_tokens` parameter or disabling the extended output beta.

3. **Performance Issues with Prompt Caching**: If prompt caching seems to degrade performance, ensure you're only marking appropriate messages as ephemeral.

4. **Streaming Interruptions**: If streaming doesn't work properly, check for network issues or conflicts with other beta features.

## Best Practices

1. **Prompt Caching**: Mark only non-essential context as ephemeral; keep the latest user message as non-ephemeral.

2. **Extended Output**: Use with caution - very long outputs can consume significant resources.

3. **Feature Flags**: Toggle features on/off based on your specific needs:
   ```bash
   # Enable only specific features
   export ENABLE_STREAMING=true
   export ENABLE_PROMPT_CACHING=true
   export ENABLE_EXTENDED_OUTPUT=false
   ```

4. **Thinking Budget**: Allocate approximately half of your max_tokens to the thinking budget for optimal performance.

## Conclusion

Phase 2 features significantly enhance Claude DC's capabilities, making it more interactive, efficient, and powerful. These features work together to provide a more responsive and capable agent, able to handle complex tasks with longer context and generate detailed responses.