# Claude DC Streaming Implementation

This is a production-ready implementation of Claude with streaming capabilities, tool use, thinking parameters, and other advanced features. It is based on extensive research and testing to ensure compatibility with the latest Anthropic API and SDK.

## Key Features

1. **Streaming with Tool Use**: Real-time, token-by-token streaming with seamless tool integration
2. **Proper Parameter Handling**: Correct implementation of thinking as a parameter (not a beta flag)
3. **Beta Flags Configuration**: Proper header-based beta flag configuration
4. **Event-Based Processing**: Comprehensive handling of all streaming event types
5. **Tool Validation**: Parameter validation for all tools before execution
6. **Error Handling**: Robust error recovery with proper exception handling
7. **Streamlit UI**: Real-time UI updates with state persistence

## Requirements

- Python 3.11+
- Anthropic SDK v0.50.0
- Streamlit 1.31.0+
- Pydantic 2.5.2+
- PyAutoGUI (optional, for computer control)

## Project Structure

- `loop.py` - Core implementation with streaming and tool use
- `streamlit_app.py` - Streamlit UI for interacting with Claude
- `tools/` - Tool implementations:
  - `bash.py` - Execute shell commands
  - `computer.py` - Control the computer (mouse/keyboard)
  - `edit.py` - File operations (read/write/append)
- `run_streamlit.sh` - Script to launch the Streamlit UI

## API Implementation Details

### Beta Flags Setup

Beta flags are correctly set in the client headers, not as parameters:

```python
client = AsyncAnthropic(
    api_key=api_key,
    default_headers={"anthropic-beta": "output-128k-2025-02-19,tools-2024-05-16"}
)
```

### Thinking Parameter Configuration

Thinking is implemented as a parameter, not a beta flag:

```python
# Add thinking parameter (if provided)
if thinking_budget:
    params["thinking"] = {
        "type": "enabled", 
        "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
    }
```

### Streaming Event Handling

Comprehensive event handling for all streaming events:

- `content_block_start` - For detecting new content blocks
- `content_block_delta` - For processing streaming content updates
- `content_block_stop` - For finalizing tool inputs and processing
- `message_stop` - For detecting message completion

### Tool Input Processing

Proper accumulation and validation of tool inputs:

```python
if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
    tool_input_acc += event.delta.partial_json

elif event.type == "content_block_stop":
    # We have a complete tool input
    tool_input = json.loads(tool_input_acc)
    # Validate and execute the tool...
```

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key**:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Run the Streamlit App**:
   ```bash
   ./run_streamlit.sh
   ```

## Configuration Options

The Streamlit UI provides several configuration options:

- **Model Selection**: Choose between Claude models
- **Thinking**: Enable/disable thinking and adjust budget
- **Prompt Caching**: Enable/disable prompt caching
- **Extended Output**: Enable/disable 128k output
- **Debug Mode**: View detailed event information

## Implementation Notes

- This implementation is based on the latest research and API documentation
- Uses Anthropic SDK v0.50.0 to ensure compatibility
- Beta flags are properly handled in headers
- Thinking parameters are correctly implemented in the request body
- Full event handling for streaming responses

## Troubleshooting

If you encounter issues:

1. Verify the Anthropic SDK version: `pip show anthropic`
2. Check API key: Ensure it's correctly set in the environment
3. Enable debug mode: Add `--debug` to see detailed events
4. Check logs: Review `streamlit_app.log` for errors

## Production Considerations

- Add retries for transient errors
- Implement rate limiting to stay within API constraints
- Add authentication for multi-user environments
- Consider containerizing for consistent deployment