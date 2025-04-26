# Claude 3.7 Computer Use - Streaming Implementation

This directory contains a completely redesigned implementation of Claude DC (Computer Use) based on the latest research and best practices. The focus is on creating a stable, reliable foundation that properly supports streaming with tool use.

## Key Features

- **True streaming for all interactions** - No cutoff at token limits, supports up to 128K token output using the `output-128k-2025-02-19` beta header
- **Integrated tool usage during streaming** - The AI can call functions without breaking the stream
- **Live "thinking" notes** - Chain-of-thought reasoning is streamed to the UI in real-time
- **Modular architecture** - Separate agent loop, tools, and UI modules for flexibility
- **Performance optimizations** - Uses prompt caching and efficient API calls
- **Robust error handling** - Graceful handling of API errors, timeouts, and tool failures

## Architecture

The implementation follows a clean, modular design:

- `tools.py` - Tool definitions and execution logic
- `loop.py` - Agent loop with Claude API client and streaming handling
- `streamlit_app.py` - Streamlit UI for chat interface
- `launch.sh` - Launcher script for easy startup

## Usage

To run the application:

1. Set your Anthropic API key (optional for development mode):
```
export ANTHROPIC_API_KEY=your_api_key_here
```

2. Run the launcher script:
```
./launch.sh
```

3. Select the launch option:
   - Option 1: Launch the Streamlit UI
   - Option 2: Run a CLI test with a sample query

## Implementation Details

### API Configuration

- **Model**: `claude-3-7-sonnet-20250219` (latest date format)
- **Beta Features**:
  - `output-128k-2025-02-19` - Enables 128K token output limit
  - `computer-use-2025-01-24` - Enables Computer Use features
  - `token-efficient-tools-2025-02-19` - More efficient tool usage
  - `prompt-caching-2024-07-31` - Enables prompt caching for efficiency

### Streaming Implementation

The implementation properly handles all SSE events from Claude's streaming API:
- `content_block_start` - Detects the start of text, thinking, or tool_use blocks
- `content_block_delta` - Accumulates deltas for text, thinking, and tool input
- `content_block_stop` - Handles the end of content blocks
- `message_stop` - Detects the end of Claude's response

### Tool Use Flow

1. Claude streams its response until it decides to use a tool
2. The tool is executed asynchronously while the UI remains responsive
3. The result is sent back to Claude, which continues its response
4. This loop continues until Claude completes its answer

## Available Tools

- **bash** - Execute shell commands and view the output
- **screenshot** - Take screenshots of the screen (mock implementation)
- **mouse** - Control the mouse with various operations (mock implementation)
- **keyboard** - Type text or press special keys (mock implementation)

## Error Handling

The implementation includes robust error handling for:
- API errors with retry logic
- Tool execution failures
- Timeouts for long-running operations
- User interruption via the Stop button

## UI Features

- Real-time streaming of Claude's responses
- Expandable thinking/reasoning section
- Clear visualization of tool usage
- Tool result display with success/error states
- System prompt editor in the sidebar
- Configuration options for model settings

## Development and Testing

- CLI test mode for quick verification
- Verbose logging for debugging
- Modular design for easy extension or modification

## References

This implementation is based on the latest research on Claude 3.7 Sonnet's streaming capabilities, drawing from:
- Anthropic's official documentation
- Proven implementation patterns from the developer community
- Best practices for streaming with tool use