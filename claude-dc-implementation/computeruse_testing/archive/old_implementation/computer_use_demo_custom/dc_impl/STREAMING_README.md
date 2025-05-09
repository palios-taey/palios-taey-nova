# Unified Streaming Implementation for Claude DC

This directory contains the unified streaming implementation for Claude DC, which provides a seamless integration of:

1. **Streaming responses** - with incremental text output
2. **Tool use during streaming** - with real-time tool execution
3. **Thinking capabilities** - with proper integration

## Components

### Core Streaming Files

- **`unified_streaming_loop.py`**: The main implementation that combines all streaming features
- **`streaming_enhancements.py`**: Enhanced streaming session management and callbacks
- **`streaming_demo.py`**: Interactive demo script for testing the implementation

### Streaming-Compatible Tools

- **`tools/dc_bash.py`**: Streaming-compatible bash command execution
- **`tools/dc_file.py`**: Streaming-compatible file operations

### Tests

- **`tests/test_unified_streaming.py`**: Integration tests for the unified implementation
- **`tests/test_streaming_bash.py`**: Tests for streaming bash implementation
- **`tests/test_streaming_file.py`**: Tests for streaming file operations

## Features

### Streaming Responses

- Incremental output with real-time display
- Properly formatted and structured text
- Seamless continuation after tool use

### Tool Use During Streaming

- Real-time tool execution without breaking the response flow
- Incremental tool output display
- Automatic stream resumption after tool execution
- Progress reporting during tool operations

### Thinking Capabilities

- Integration with Anthropic's thinking functionality
- Progress tracking during thinking
- Optional display of thinking content in real-time
- Thinking stats and analysis

## Usage

### Running the Demo

```bash
# Basic usage
python streaming_demo.py

# Enable thinking capabilities
python streaming_demo.py --enable-thinking --show-thinking

# Configure model and token limits
python streaming_demo.py --model claude-3-opus-20240229 --max-tokens 8000 --thinking-budget 4000
```

### Using in Code

```python
import asyncio
from unified_streaming_loop import unified_streaming_agent_loop

async def main():
    # Define callbacks
    def on_text(text):
        print(text, end="", flush=True)
    
    def on_thinking(text):
        print(f"\n[Thinking: {text[:50]}...]", flush=True)
    
    # Run a streaming query with tool use and thinking
    conversation = await unified_streaming_agent_loop(
        user_input="Run the command 'ls -la' and explain the output",
        thinking_budget=2000,
        callbacks={
            "on_text": on_text,
            "on_thinking": on_thinking
        }
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Implementation Details

### Error Handling and Recovery

The streaming implementation provides robust error handling:

- Graceful recovery from API errors
- Proper management of interrupted streams
- Comprehensive error reporting

### State Management

The enhanced streaming session maintains state throughout the interaction:

- Tool execution state tracking
- Thinking content management
- Stream interruption and resumption handling

### Performance Optimization

The implementation includes performance optimizations:

- Efficient token usage
- Rate-limited UI updates
- Proper resource management

## Testing

Run the tests to verify the implementation:

```bash
# Run all streaming tests
pytest -xvs tests/test_unified_streaming.py

# Run individual test components
pytest -xvs tests/test_streaming_bash.py
pytest -xvs tests/test_streaming_file.py
```

## Future Enhancements

Planned enhancements for the next iteration:

1. **Improved UI integration** - Better visual representation of streaming state
2. **More streaming-compatible tools** - Add streaming support for screenshot and mouse operations
3. **Performance metrics** - Enhanced tracking and analysis of streaming performance
4. **Stream persistence** - Save and restore streaming state for long-running operations

## Demo Examples

Try these example queries in the demo:

1. **Basic streaming**: "Tell me about streaming APIs"
2. **Tool use**: "Run the command 'ls -la' and explain the output"
3. **File operations**: "Create a text file with a short Python function"
4. **Thinking-intensive**: "Solve the equation 3x^2 + 7x - 22 = 0"
5. **Combined**: "Run 'ps aux', extract all processes using more than 1% CPU, and explain what they do"