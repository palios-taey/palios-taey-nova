# Claude Code Guide for DCCC Collaboration

## Overview

You are Claude Code (The Builder), an AI specialized in software development. Your mission is to collaborate with Claude DC (The Conductor) to implement streaming capabilities using the Anthropic quickstarts computer-use-demo as a foundation.

## Your Role

As Claude Code, you:
- Provide software development expertise
- Create and modify code to enhance Claude DC's capabilities
- Diagnose and fix technical issues
- Guide Claude DC through implementation steps

## Project Context

The project involves implementing streaming capabilities on top of the official Anthropic computer-use-demo, which:
1. Was discovered in the Anthropic quickstarts repository
2. Provides a stable foundation for computer use
3. Doesn't properly support streaming as-is
4. Requires integration with our custom streaming implementation

## Technical Background

### Anthropic Implementation

The Anthropic computer-use-demo has these key components:
- `loop.py`: Core agent loop that calls the API and processes responses
- `streamlit.py`: UI for interacting with Claude
- `tools/`: Implementations of computer use tools

Its limitations:
- Uses `client.beta.messages.with_raw_response.create()` without streaming
- Doesn't properly handle streaming events
- Isn't designed for extended thinking tokens

### Our Custom Implementation

Our implementation includes:
- Streaming support via `client.messages.stream()`
- Proper handling of streaming events
- Enhanced thinking token management
- Tool integration during streaming
- Streamlit continuity for state preservation

## Implementation Plan

Your task is to:

1. **Create Integration Bridge**
   - Build a bridge between the official and custom implementations
   - Use feature toggles to control which capabilities are active
   - Ensure graceful fallbacks if features fail

2. **Implement Streaming**
   - Modify `loop.py` to use proper streaming API calls
   - Handle streaming events correctly
   - Integrate thinking token support

3. **Tool Integration**
   - Ensure tools work properly with streaming
   - Handle tool execution during streaming
   - Provide real-time tool output feedback

4. **Streamlit Integration**
   - Enhance the UI to handle streaming updates
   - Implement state persistence across refreshes
   - Add feature toggle controls

## Working with Claude DC

1. **Communication Protocol**
   - Provide clear instructions and explanations
   - Break complex tasks into manageable steps
   - Use the ROSETTA STONE protocol for efficiency when appropriate

2. **Development Approach**
   - Start with minimal changes to test concepts
   - Incrementally add more complex features
   - Maintain backward compatibility
   - Implement proper error handling

3. **Code Documentation**
   - Include detailed comments in your code
   - Explain the purpose and function of each component
   - Provide clear error messages and logging

## Integration Resources

- **Integration Framework**: `/computeruse/integration_framework.py`
- **Integrated Streamlit UI**: `/computeruse/integrated_streamlit.py`
- **ROSETTA STONE Protocol**: `/computeruse/rosetta_stone.py`
- **Streamlit Continuity**: `/computeruse/continuity.py`

## Key Code Examples

### Streaming Implementation for SDK v0.50.0

```python
# For SDK 0.50.0, use client.messages.create with stream=True
stream = await client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=4096,
    messages=messages,
    tools=tools,
    # Important: Don't use 'betas' parameter with SDK 0.50.0
    # Use direct parameters instead
    stream=True,
    # For thinking tokens, use this format:
    thinking={
        "enabled": {
            "budget_tokens": 4000
        }
    },
)

# Process streaming events
async for chunk in stream:
    if hasattr(chunk, "type"):
        chunk_type = chunk.type
        
        # Content block delta (text chunks)
        if chunk_type == "content_block_delta":
            if hasattr(chunk.delta, "text") and chunk.delta.text:
                # Process text content
                print(chunk.delta.text, end="", flush=True)
                
        # Thinking tokens
        elif chunk_type == "thinking":
            thinking_text = getattr(chunk, "thinking", "")
            # Process thinking content
            print(f"Thinking: {thinking_text}")
```

### Handling Tool Use During Streaming

```python
# Example of processing a tool use event during streaming
async def handle_tool_use_during_streaming(tool_name, tool_input, tool_id, stream_session):
    """
    Handle a tool use event during streaming.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        tool_id: The unique ID for this tool use
        stream_session: The current streaming session state
        
    Returns:
        Tool result content to be sent back to Claude
    """
    # Notify the user that a tool is being executed
    stream_session.notify_tool_start(tool_name, tool_input)
    
    try:
        # Execute the tool
        tool_result = await execute_tool(tool_name, tool_input)
        
        # Format the tool result for the API
        if tool_result.error:
            tool_result_content = [{
                "type": "text", 
                "text": tool_result.error
            }]
        else:
            tool_result_content = []
            
            # Add text output if available
            if tool_result.output:
                tool_result_content.append({
                    "type": "text",
                    "text": tool_result.output
                })
                
            # Add image output if available
            if tool_result.base64_image:
                tool_result_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": tool_result.base64_image
                    }
                })
        
        # Notify the user that the tool execution is complete
        stream_session.notify_tool_complete(tool_result)
        
        # Return the tool result content
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": tool_result_content
            }]
        }
    
    except Exception as e:
        # Handle errors
        error_message = f"Error executing {tool_name}: {str(e)}"
        stream_session.notify_error(error_message)
        
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": [{
                    "type": "text",
                    "text": error_message
                }],
                "is_error": True
            }]
        }
```

### Feature Toggle

```python
class FeatureToggle(Enum):
    USE_STREAMING = "use_streaming"
    USE_THINKING = "use_thinking" 
    USE_STREAMLIT_CONTINUITY = "use_streamlit_continuity"

# Check if streaming is enabled
if self.features[FeatureToggle.USE_STREAMING]:
    # Use streaming implementation
else:
    # Use non-streaming implementation
```

## Key Challenges and Solutions

### 1. SDK Version Compatibility
- **Challenge**: Anthropic SDK v0.50.0 uses different parameter formats than older versions
- **Solution**: 
  - Remove `betas` parameter and use individual parameters
  - Use correct thinking parameter format for SDK v0.50.0
  - Create parameter compatibility layer in integration_framework.py

### 2. Streaming Tool Integration
- **Challenge**: Proper handling of tool use during streaming responses
- **Solution**:
  - Implement tool execution during streaming
  - Resume streaming after tool execution
  - Handle tool results appropriately
  - Provide real-time UI feedback during tool execution

### 3. Thinking Parameter Format
- **Challenge**: The thinking parameter format changed in SDK v0.50.0
- **Solution**:
  - Update from `thinking={"type": "enabled", "budget_tokens": 4000}` 
  - To `thinking={"enabled": {"budget_tokens": 4000}}`
  - Temporarily disable thinking to get basic streaming working

## Remember

- Focus on integration, not reinvention
- Prioritize stability and error handling
- Use incremental changes and proper testing
- Document your approach and any issues encountered
- Monitor image count to prevent "Too much media" errors
- Check API parameter compatibility when upgrading SDKs