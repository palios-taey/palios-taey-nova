# Response Chunking for Streaming Tool Calls

This document explains the response chunking implementation that allows Claude DC to continue generating responses after tool execution during streaming.

## Problem Statement

When Claude DC executes a tool during streaming, the stream is interrupted to process the tool, but there's a challenge in properly resuming the stream afterward to allow continued response generation. Without proper response chunking, Claude DC can only execute a single command, then stops without being able to continue the conversation.

## Solution: Response Chunking

Response chunking allows Claude DC to continue generating responses after tool execution by:

1. **Structured Conversation History**: Properly tracking tool use and results in the conversation
2. **Stream Resumption**: Carefully resuming the stream with the updated conversation
3. **Buffer State Reset**: Properly resetting buffer state between commands
4. **Thinking Disabling**: Disabling thinking during stream resumption to avoid conflicts

## Implementation Details

### 1. Proper Tool Result Structure

When a tool is executed, the conversation history is updated with:

```python
# Add the assistant's tool use to the conversation history
tool_use_message = {
    "role": "assistant",
    "content": [{
        "type": "tool_use",
        "id": tool_id,
        "name": tool_name,
        "input": tool_input
    }]
}
conversation_history.append(tool_use_message)

# Add tool result to conversation
tool_result_message = {
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": tool_result_content
    }]
}
conversation_history.append(tool_result_message)
```

### 2. Stream Resumption with Cleanup

When resuming the stream after tool execution:

```python
# Resume with updated conversation
resume_params = {**api_params, "messages": conversation_history}
# Disable thinking on resume to avoid conflicts
if "thinking" in resume_params:
    del resume_params["thinking"]
    
# Add delay to ensure complete processing
await asyncio.sleep(0.5)
    
# Resume the stream with the updated conversation
resume_stream = await client.messages.create(**resume_params)

# Reset the tool buffer for new messages
tool_buffer.reset_attempts()
```

### 3. Nested Stream Processing

Handle tool calls in the resumed stream with additional resume layers:

```python
# Process the resumed stream
async for resume_chunk in resume_stream:
    # Continue normal processing for resumed stream
    if hasattr(resume_chunk, "type"):
        resume_chunk_type = resume_chunk.type
        
        # Content block delta for text
        if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
            if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                enhanced_callbacks.on_text(resume_chunk.delta.text)
        
        # Process partial function calls in resumed stream
        if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA and hasattr(resume_chunk, "index"):
            # Process with tool buffer
            content = ""
            if hasattr(resume_chunk.delta, "input_json_delta"):
                content = resume_chunk.delta.input_json_delta
            tool_id = getattr(resume_chunk.delta, "tool_use_id", None)
            
            # Handle with buffer
            if content:
                tool_buffer.handle_content_block_delta(
                    resume_chunk.index, content, tool_id
                )
```

## Key Benefits

1. **Multiple Commands**: Claude DC can execute multiple commands in a single response
2. **Continued Reasoning**: Claude DC can continue generating text after tool execution
3. **Coherent Responses**: The response flow remains natural with tools interspersed

## Limitations and Considerations

1. **API Limitations**: The Anthropic API may impose limits on nested stream resumption
2. **Token Consumption**: Multiple tool uses increase token consumption
3. **Potential for Context Loss**: With very complex response chains, context might be partially lost

## Configuration Options

Response chunking can be configured via feature toggles:

```json
{
  "use_response_chunking": true,
  "max_resume_depth": 3
}
```

## Recommended Usage

For optimal performance with response chunking:

1. Limit the number of consecutive tools in a single response (3-5 maximum)
2. Ensure proper validation of all tool parameters before execution
3. Use the XML-format for function calls to reduce ambiguity
4. Consider disabling thinking during streaming for more reliable chunking