# XML Function Call Race Condition Fix

This document summarizes the approach used to fix the race condition issue with Claude DC's function calls during streaming.

## Problem Description

During streaming, Claude DC was experiencing a race condition where:

1. Claude DC would begin constructing a function call (JSON or XML format)
2. Before the function call was complete, the partial function call got processed prematurely
3. This caused errors like "Command 'in' is not in the whitelist of read-only commands"

Claude DC described the issue as: _"The streaming nature of my response generation appears to be interfering with my ability to complete the full function call structure before it gets processed...the streaming behavior is essentially 'cutting me off' mid-construction of the function call."_

## Fix Implementation

Our implementation combines several approaches to fix this issue:

### 1. Direct Implementation from Parallel Version

We adopted the working implementation from `/computer_use_demo_parallel/streaming/unified_streaming_loop_fixed.py`, which:

- Handles tool calls at the CONTENT_BLOCK_START level instead of attempting to accumulate partial JSON/XML
- Uses a very precise tool_use_id tracking approach
- Disables thinking when tool use is involved (due to API limitation)
- Makes deep copies of parameters to avoid modifying originals
- Uses a list to accumulate text chunks rather than a single string

### 2. XML-Specific System Prompt

Added an XML system prompt (`xml_system_prompt.py`) that:

- Instructs Claude DC to use XML format for function calls
- Provides explicit examples of the correct format
- Emphasizes the importance of completing the ENTIRE XML structure before submitting
- Includes detailed instructions on required parameters for each tool

### 3. Integration with Existing Code

- Updated imports to use the XML system prompt when available
- Modified API parameters to use the XML system prompt when available
- Added detailed logging around function call processing

## Key Insights from Research

1. **API Limitations**: The Claude API has specific requirements about thinking and tool use
2. **Tool Use ID Tracking**: Proper tool_use_id tracking is essential for conversation history
3. **Stream Resumption**: After a tool call, the stream must be resumed with proper conversation history
4. **XML Format**: XML format for function calls allows Claude DC to be more precise with tool usage

## Testing

The implementation can be tested with the `test_xml_fixed.py` script, which:

- Uses a simple bash command that forces Claude DC to use a tool call
- Sets up the API with the XML system prompt
- Disables thinking as per the fix
- Uses real adapters for actual execution

## Future Considerations

1. **More Robust Error Handling**: The implementation could be enhanced with more detailed error handling
2. **Advanced Parameter Validation**: More comprehensive parameter validation could be added
3. **Expanded XML Support**: Additional XML validation and formatting could be added