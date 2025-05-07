# Streaming Implementation for Claude DC

This document provides information about the streaming implementation for Claude DC, including how to use it, test it, and troubleshoot issues.

## Overview

The streaming implementation enhances Claude DC with the following capabilities:

1. **Token-by-Token Streaming**: Responses are streamed token-by-token for a more responsive user experience.
2. **Tool Execution During Streaming**: Tools can be executed while streaming is in progress.
3. **Thinking Integration**: Claude's thinking process can be displayed during streaming.

## Implementation Structure

The implementation consists of the following components:

1. **Unified Streaming Loop** (`streaming/unified_streaming_loop.py`):
   - Main agent loop with streaming support
   - Handles token-by-token streaming
   - Manages tool execution during streaming

2. **Enhanced Streaming Session** (`streaming/streaming_enhancements.py`):
   - Better handling of streaming interruptions
   - Improved thinking integration
   - Stream resumption capability

3. **Streaming-Compatible Tools**:
   - Streaming Bash Tool (`streaming/tools/dc_bash.py`)
   - Streaming File Tool (`streaming/tools/dc_file.py`)

4. **Integration Module** (`streaming_integration.py`):
   - Bridges between original implementation and streaming
   - Controls feature deployment through toggles
   - Provides fallback mechanisms

## Using the Streaming Implementation

The streaming implementation is controlled by feature toggles, which allow for gradual deployment and testing of functionality.

### Feature Toggles

The feature toggles are defined in `streaming/feature_toggles.json`:

```json
{
  "use_streaming_bash": true,
  "use_streaming_file": true,
  "use_streaming_screenshot": false,
  "use_unified_streaming": true,
  "use_streaming_thinking": true,
  "max_thinking_tokens": 4000,
  "log_level": "INFO"
}
```

- `use_unified_streaming`: Master toggle for the streaming implementation
- `use_streaming_bash`: Toggle for streaming-compatible bash tool
- `use_streaming_file`: Toggle for streaming-compatible file operations
- `use_streaming_screenshot`: Toggle for streaming-compatible screenshots (not recommended)
- `use_streaming_thinking`: Toggle for thinking tokens during streaming
- `max_thinking_tokens`: Budget for thinking tokens

### Testing the Implementation

A test script is provided to test the streaming implementation:

```bash
# Test with streaming enabled
python test_streaming.py

# Test with streaming disabled for comparison
python test_streaming.py --no-streaming

# Use a specific model
python test_streaming.py --model claude-3-haiku-20240307
```

### Using the Implementation in Production

The streaming implementation is integrated through `streaming_integration.py`, which provides a transparent bridge to the original implementation.

To use it:

1. Import the streaming integration instead of the original loop:
   ```python
   from streaming_integration import async_sampling_loop
   ```

2. Use `async_sampling_loop` exactly as you would use the original `sampling_loop`:
   ```python
   messages = await async_sampling_loop(
       model=model,
       provider=APIProvider.ANTHROPIC,
       system_prompt_suffix="",
       messages=messages,
       output_callback=output_callback,
       tool_output_callback=tool_output_callback,
       api_response_callback=api_response_callback,
       api_key=api_key,
       max_tokens=4096,
       tool_version=ToolVersion.VERSION_1,
       thinking_budget=4000
   )
   ```

## Troubleshooting

If issues occur with the streaming implementation:

1. Check the logs in `streaming/logs/`
2. Set `use_unified_streaming` to `false` to fall back to the original implementation
3. Disable specific features (e.g., `use_streaming_bash`) to isolate issues
4. Verify API parameters are correctly set

## Critical Guidelines

1. **DO NOT** modify image handling settings (keep default value of 3)
2. **MAINTAIN** default token limits (64000 for Claude-3-7-Sonnet)
3. **PRESERVE** existing configuration values unless explicitly needed
4. **USE** feature toggles for controlled deployment

## Implementation Notes

1. The maximum token limit for Claude-3-7-Sonnet is 64000, not 65536
2. Beta parameters must be handled with care as they can cause API errors
3. Tools require specific parameters (e.g., bash needs 'command', computer needs 'action')
4. Parameter validation needs to happen before tool execution
5. Feature toggles should be used for controlled deployment

By following these guidelines, the streaming implementation can be used effectively in Claude DC.