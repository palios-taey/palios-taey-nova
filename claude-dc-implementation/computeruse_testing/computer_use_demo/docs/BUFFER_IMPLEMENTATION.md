# Buffer Implementation for Streaming Tool Calls

This document explains the buffer implementation in Claude DC that solves the race condition during streaming where partial function calls are processed prematurely.

## Problem Statement

During streaming, Claude DC's tool calls are delivered via `content_block_delta` events with a delta type of `input_json_delta`. These partial JSON strings arrive incrementally, but if processed immediately, they lead to incomplete function calls being executed, causing errors like:

```
Error: Command 'in' is not in the whitelist of read-only commands
```

## Solution: The Buffer Pattern

The solution implements a buffer pattern that accumulates partial JSON/XML until a complete function call is formed:

1. **Accumulate:** Store partial JSON/XML during `content_block_delta` events
2. **Process:** Only process complete tool calls at `content_block_stop` events
3. **Validate:** Ensure all required parameters are present before execution
4. **Execute:** Run the tool with proper parameters and track its result
5. **Resume:** Continue the response after tool execution

## Core Components

### 1. ToolUseBuffer Class

The `ToolUseBuffer` class is a lightweight implementation that:

- Accumulates partial JSON/XML for each content block index
- Tracks tool_use_id values for proper API integration
- Validates parameters before execution
- Prevents infinite loops with safety mechanisms
- Supports both JSON and XML function call formats

```python
class ToolUseBuffer:
    def __init__(self):
        self.json_buffers = {}  # Maps indices to accumulated JSON/XML
        self.tool_ids = {}      # Maps indices to tool use IDs
        self.attempt_count = 0  # Count of tool use attempts
        self.max_attempts = 3   # Maximum number of attempts
        
    def handle_content_block_delta(self, index, content, tool_id=None):
        # Initialize buffer if needed
        if index not in self.json_buffers:
            self.json_buffers[index] = ""
            
        # Store tool ID if provided
        if tool_id is not None:
            self.tool_ids[index] = tool_id
            
        # Accumulate content
        self.json_buffers[index] += content
        return True
        
    def handle_content_block_stop(self, index):
        # Process complete content (XML or JSON)
        # Returns tool call info if complete or None if still accumulating
        ...
```

### 2. XML Function Prompt

The XML-focused system prompt guides Claude DC to use XML format for function calls, which helps prevent the race condition:

```python
XML_SYSTEM_PROMPT = """
When using tools, ALWAYS use XML format function calls with the following structure:

<function_calls>
<invoke name="TOOL_NAME">
<parameter name="PARAM_NAME">PARAM_VALUE</parameter>
<!-- Additional parameters as needed -->
</invoke>
</function_calls>

⚠️ IMPORTANT: Always construct the COMPLETE XML structure before submitting.
"""
```

### 3. Unified Streaming Loop Integration

Key changes in the unified streaming loop:

- Use `ToolUseBuffer` to accumulate partial function calls
- Use XML system prompt to guide Claude DC
- Add deliberate delays before processing to ensure complete function calls
- Reset buffer state after tool execution
- Properly structure conversation history with tool use and tool result messages
- Disable thinking during streaming to avoid API conflicts
- Set correct max_tokens limit (64000 for Claude-3-7-Sonnet)

## Implementation Features

1. **Dual Format Support:** Handles both XML and JSON function calls
2. **Parameter Validation:** 3-stage validation to ensure complete parameters
3. **Proper Tool ID Tracking:** Maintains tool_use_id through the conversation
4. **Response Chunking:** Allows continued responses after tool execution
5. **Safety Mechanisms:** Prevents infinite loops during tool execution
6. **Buffer State Reset:** Properly resets after tool execution for subsequent commands
7. **Configurable Features:** Toggles for various features via feature_toggles.json

## Testing the Implementation

1. **Basic Testing:** Use bash commands that require parameters
2. **Multiple Command Testing:** Test executing multiple commands in a single response
3. **Response Continuation:** Verify that Claude DC can continue responding after tool execution
4. **Error Handling:** Test with invalid or incomplete parameters

## Known Limitations

1. The implementation may not handle extremely large token outputs effectively
2. Multiple nested tool calls can sometimes cause confusion
3. Very complex XML structures may be challenging to parse correctly

## Future Improvements

1. Enhanced error reporting for tool validation failures
2. Visual feedback during function call construction
3. More robust parsing for complex JSON and XML
4. Additional safety checks for API parameters
5. Performance optimizations for large streams