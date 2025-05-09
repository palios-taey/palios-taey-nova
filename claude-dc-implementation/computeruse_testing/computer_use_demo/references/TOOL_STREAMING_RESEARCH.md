# Claude DC Tool Streaming Research Request

## Background

We're implementing a streaming interface for Claude DC, a custom implementation of Claude with computer use tools. The streaming implementation works for regular text responses but fails when executing tools during streaming. This document outlines our current implementation, the issues we're facing, and the information needed to fix these problems.

## Current Implementation

Our implementation consists of:

1. **Streamlit UI** (`/streamlit_streaming.py`): Provides UI controls for output and thinking budgets, with real-time display of token-by-token streaming.

2. **Unified Streaming Agent Loop** (`/streaming/unified_streaming_loop.py`): Manages conversation with the Claude API, handles streaming events, and coordinates tool execution.

3. **Streaming Tools**:
   - `/streaming/tools/dc_bash.py`: Streaming-compatible bash command execution
   - `/streaming/tools/dc_file.py`: Streaming-compatible file operations

4. **Streaming Enhancements** (`/streaming/streaming_enhancements.py`): Provides session management and callback handling.

## Critical Issues with Tool Execution During Streaming

When Claude attempts to use tools during streaming, we encounter these errors:

1. **Generator to AsyncIterator Conversion Error**:
   ```
   File "/home/computeruse/computer_use_demo/streaming/unified_streaming_loop.py", line 141, in execute_streaming_tool
     (chunk for chunk in output_chunks).__aiter__()
   AttributeError: 'generator' object has no attribute '__aiter__'
   ```

2. **API Error with Tool ID Tracking**:
   ```
   Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.2.content.3: unexpected `tool_use_id` found in `tool_result` blocks: toolu_01Dxwgsdq3TbECGATskN6oKR. Each `tool_result` block must have a corresponding `tool_use` block in the previous message.'}}
   ```

## Key Issues to Research

1. **Proper AsyncIterator Implementation**: How to correctly implement async generators and iterators for streaming tool output?

2. **Tool Use ID Tracking**: How to correctly structure conversation history with proper tool_use_id references when resuming a stream after tool execution?

3. **Resuming Streaming After Tool Use**: What's the correct approach to resume the API stream after executing a tool during streaming?

4. **Parameter Validation**: How to ensure tools receive required parameters during streaming?

## Relevant Code Snippets

### 1. Tool Execution During Streaming (Key Problem Area)

From `unified_streaming_loop.py`, lines 90-250:

```python
async def execute_streaming_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_id: str,
    session: EnhancedStreamingSession,
    enhanced_callbacks: EnhancedStreamingCallbacks
) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Execute a tool with streaming support, handling different tools appropriately.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        tool_id: The ID of the tool use in the conversation
        session: The enhanced streaming session
        enhanced_callbacks: The enhanced callbacks
        
    Returns:
        Tuple of (tool_result, tool_result_content)
    """
    logger.info(f"Executing streaming tool: {tool_name}")
    
    # Mark the stream as interrupted during tool execution
    session.interrupt_stream(f"Executing tool: {tool_name}")
    
    # Notify about tool start
    await enhanced_callbacks.on_tool_start(tool_name, tool_input)
    
    # Initialize progress callback
    async def progress_callback(message, progress):
        await enhanced_callbacks.on_tool_progress(tool_name, message, progress)
    
    try:
        # Check for streaming bash implementation
        if tool_name == "dc_bash":
            try:
                # Try to import the streaming bash tool
                from tools.dc_bash import dc_execute_bash_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming bash implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_bash_tool_streaming(tool_input, progress_callback):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    enhanced_callbacks.on_text(chunk)
                
                # Process the collected output
                tool_result = await dc_process_streaming_output(
                    # Create a generator that yields the collected chunks
                    (chunk for chunk in output_chunks).__aiter__()
                )
                
                # Format the streaming result
                if tool_result.error:
                    tool_result_content = [{"type": "text", "text": tool_result.error}]
                else:
                    tool_result_content = [{"type": "text", "text": tool_result.output}]
                
                # Notify about tool completion
                await enhanced_callbacks.on_tool_complete(tool_name, tool_input, tool_result)
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming bash implementation not available, falling back to standard")
```

### 2. Stream Resumption After Tool Execution (Error Area)

From `unified_streaming_loop.py`, lines 415-442:

```python
                        # Execute tool immediately during streaming
                        tool_result, tool_result_content = await execute_streaming_tool(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_id=tool_id,
                            session=session,
                            enhanced_callbacks=enhanced_callbacks
                        )
                        
                        # Add tool result to conversation
                        tool_result_message = {
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": tool_result_content
                            }]
                        }
                        
                        # Update conversation history with tool result
                        conversation_history.append(tool_result_message)
                        
                        # Resume the stream with updated conversation
                        resume_stream = await client.messages.create(
                            **{**api_params, "messages": conversation_history}
                        )
```

## Research Questions for Claude Chat

1. What's the correct way to implement async generators for streaming tools?

2. How should we structure the conversation history when resuming after a tool execution during streaming?

3. How do we properly track tool IDs between the initial stream and resumed stream after tool execution?

4. What are best practices for parameter validation when executing tools during streaming?

## Suggested File Attachments for Claude Chat

1. `/home/computeruse/computer_use_demo/streaming/unified_streaming_loop.py` - Main streaming agent loop with tool execution

2. `/home/computeruse/computer_use_demo/streaming/tools/dc_bash.py` - Bash tool implementation with streaming

3. `/home/computeruse/computer_use_demo/streaming/streaming_enhancements.py` - Session management and callbacks

4. `/home/computeruse/computer_use_demo/streamlit_streaming.py` - Streamlit UI with streaming integration

5. Any official documentation about the Claude API's tool use during streaming (if available)

## Additional Context

- We're using the latest Claude 3 Sonnet model (claude-3-7-sonnet-20250219)
- The API supports streaming with `stream=True` parameter
- The current implementation tracks thinking tokens with the `thinking` parameter
- The UI updates properly during streaming when no tools are used
- When Claude attempts to use a tool, the stream interrupts but fails to resume properly

## Goal

We need to understand how to correctly implement tool use during streaming, specifically:

1. The correct pattern for streaming tool output
2. Proper conversation tracking with tool use IDs
3. How to properly resume streaming after tool execution 

This will allow users to have a seamless experience with proper token-by-token streaming that maintains tool usage capability.