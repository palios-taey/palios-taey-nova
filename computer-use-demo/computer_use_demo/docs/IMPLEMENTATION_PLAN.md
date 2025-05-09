# Implementation Plan: Fixing Race Condition in Claude DC Function Calls

## Problem Summary

Claude DC experiences a race condition during streaming where:
1. Claude DC begins constructing a function call using XML structure
2. Before the function call is complete, the partial XML/JSON gets processed prematurely
3. This causes errors like "Command 'in' is not in the whitelist of read-only commands"

## Solution Approach

Our approach to fixing this issue involves several components:

1. **Buffer Pattern Implementation**: Create a robust buffer that accumulates partial XML/JSON until complete
2. **Type-Specific Processing**: Handle XML and JSON formats differently with proper validation
3. **Enhanced System Prompts**: Guide Claude DC to generate proper XML structures
4. **Detailed Error Feedback**: Provide clear guidance when function calls fail

## Key Implementation Components

### 1. Buffer Pattern

We've implemented a `ToolCallBuffer` class in `buffer_pattern.py` that:
- Accumulates partial XML/JSON content during streaming
- Validates complete function calls before execution
- Provides detailed error feedback for malformed calls
- Handles both XML and JSON formats with proper type identification

### 2. Streaming Loop Integration

We've integrated the buffer pattern into `unified_streaming_loop.py`:
- Replaced `SimpleToolBuffer` with our new `ToolCallBuffer`
- Added comprehensive logging for buffer operations
- Enhanced error feedback for malformed function calls
- Added parameter validation before execution

### 3. XML System Prompt

We've enhanced the XML system prompt in `xml_system_prompt.py`:
- Added explicit warnings about the streaming race condition
- Provided more detailed examples of proper XML structure
- Emphasized the need to complete the entire XML structure before proceeding

## Testing Approach

1. **Simple Function Calls**: Test basic XML function calls to ensure buffer accumulation works
2. **Partial XML Handling**: Test partial XML to ensure it's accumulated correctly
3. **Error Handling**: Verify that error messages are helpful when XML is malformed
4. **Parameter Validation**: Test parameter validation for various tools

## Implementation Steps

1. ✅ Create `buffer_pattern.py` with `ToolCallBuffer` class 
2. ✅ Update `unified_streaming_loop.py` to use the new buffer implementation
3. ✅ Enhance XML system prompt to help Claude DC avoid the race condition
4. ✅ Add comprehensive logging for buffer events
5. ✅ Implement parameter validation for function calls
6. ✅ Add detailed error feedback for malformed function calls

## Next Steps

1. Test with actual Claude DC interactions
2. Monitor logs for any remaining issues
3. Consider implementing the two-phase approach if needed (separating tool identification from streaming)
4. Add more examples to the system prompt based on specific error patterns observed

## References

This implementation is based on the approach documented in:
- BUFFER_PATTERN_IMPLEMENTATION.md
- TOOL_STREAMING_RESEARCH-response.md
- TOOL_STREAMING_CLAUDE_DC_FEEDBACK.md

## Implementation Notes

We've taken a minimal approach to avoid introducing complex abstractions or creating separate files that might complicate the implementation. The changes directly address the race condition by ensuring complete function calls before execution, while providing helpful feedback when errors occur.