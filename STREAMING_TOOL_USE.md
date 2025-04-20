# Claude DC Streaming with Tool Use Implementation

This document explains the implementation of streaming responses with tool use in Claude DC.

## Core Components

### 1. Streaming Configuration

Streaming is implemented as a core feature, separate from beta flags:

```python
# In __init__.py
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to enabled
```

This allows streaming to be configured independently from beta features, which was important for stability.

### 2. API Configuration

The streaming parameter is set in the API call parameters in `loop.py`:

```python
# Configure streaming based on environment variable
try:
    from computer_use_demo import ENABLE_STREAMING
    
    # Enable streaming if configured (default is True)
    stream_enabled = ENABLE_STREAMING
    api_params["stream"] = stream_enabled
    
    if stream_enabled:
        logger.info("Response streaming is ENABLED")
    else:
        logger.info("Response streaming is DISABLED")
except ImportError:
    # Fallback if import fails
    api_params["stream"] = True  # Default to enabled
```

### 3. Stream Processing

The core function that handles streaming is in `loop.py`:

```python
# Process the stream
content_blocks = []
signature_map = {}  # Map to track signatures for thinking blocks

# Stream and process results
for event in stream:
    if hasattr(event, "type"):
        if event.type == "content_block_start":
            # New content block started
            current_block = event.content_block
            content_blocks.append(current_block)
            output_callback(current_block)
        
        elif event.type == "content_block_delta":
            # Content block delta received
            if hasattr(event, "index") and event.index < len(content_blocks):
                # Handle text delta
                if hasattr(event.delta, "text") and event.delta.text:
                    content_blocks[event.index].text += event.delta.text
                    delta_block = {
                        "type": "text",
                        "text": event.delta.text,
                        "is_delta": True,
                    }
                    output_callback(delta_block)
```

### 4. Tool Integration with Streaming

When Claude starts to use a tool, the output callback receives a tool_use block:

```python
# In streamlit.py - _streaming_output_callback function
elif content_block.get("type") == "tool_use":
    # Tool use notification
    tool_name = content_block.get("name", "unknown")
    tool_input = content_block.get("input", {})
    # Add to current message 
    st.session_state.current_message_text += f"\n\nUsing tool: {tool_name}"
    if st.session_state.current_message_placeholder:
        st.session_state.current_message_placeholder.markdown(
            st.session_state.current_message_text
        )
```

### 5. Tool Execution with Streaming

Tools can also stream their own output as they execute:

```python
# In streaming_tool.py
class StreamingToolMixin:
    """
    Mixin class to add streaming capabilities to tools.
    """
    
    def set_stream_callback(self, callback: Optional[Callable[[str, str], None]] = None):
        """Set a callback function to receive streaming outputs."""
        self._stream_callback = callback
    
    async def _stream_output(self, output_chunk: str, tool_id: str):
        """Stream an output chunk to the callback if one is set."""
        if hasattr(self, '_stream_callback') and self._stream_callback:
            try:
                self._stream_callback(output_chunk, tool_id)
            except Exception as e:
                print(f"Error in streaming callback: {e}")
```

## Testing

A dedicated test script (`test_streaming_tool_use.sh`) is provided to verify that streaming with tool use is working correctly:

```bash
# Inside the container
cd github/palios-taey-nova
./test_streaming_tool_use.sh
```

This script runs a minimal test that asks Claude to use a tool while streaming its response, which helps verify that both streaming and tool use are functioning properly.

## Common Issues

1. **Beta Flag Conflicts**: Some beta flags can interfere with streaming functionality
2. **Prompt Caching**: When prompt caching is enabled with streaming, tool usage can sometimes be affected
3. **Token Efficient Tools**: This beta feature can cause streaming issues and is disabled by default

## Recommended Configuration

For the most reliable streaming with tool use:

```bash
export ENABLE_STREAMING=true
export ENABLE_THINKING=true
export ENABLE_PROMPT_CACHING=false  # Or true for more efficiency
export ENABLE_EXTENDED_OUTPUT=false
export ENABLE_TOKEN_EFFICIENT=false
```

This configuration provides stable streaming of responses with tools while maintaining good performance.