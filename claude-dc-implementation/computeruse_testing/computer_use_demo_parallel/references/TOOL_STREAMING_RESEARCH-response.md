# Mastering the Claude API: Streaming with Tools Implementation Guide

Implementing tools during streaming with the Claude API requires careful handling of async generators, proper conversation state management, and attention to error conditions. This comprehensive guide covers all essential patterns and techniques for robust tool streaming implementation.

## Bottom line up front

The key to correctly implementing tool use during streaming with Claude API is using proper async generators/iterators for managing streaming output, maintaining a thorough tracking system for tool_use_id references in conversation history, implementing proper stream resumption after tool execution, and handling parameter validation meticulously. The most common errors are related to tool_use_id matching issues, which can be avoided with robust conversation state tracking and careful event handling in your streaming implementation.

## Async generator/iterator implementation for streaming tool output

The Claude API supports streaming responses through Server-Sent Events (SSE), with two primary implementation approaches in Python:

### High-level streaming with the Anthropic SDK

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def main() -> None:
    # Define tools
    tools = [
        {
            "name": "get_weather",
            "description": "Get current weather in a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state"}
                },
                "required": ["location"]
            }
        }
    ]
    
    async with client.messages.stream(
        max_tokens=1024,
        messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
        model="claude-3-5-sonnet-20240620",
        tools=tools,
    ) as stream:
        # Process events for tool use
        async for event in stream:
            if event.type == "text":
                print(event.text, end="", flush=True)
            elif event.type == "tool_use":
                # Handle tool use request
                tool_use = event.tool_use
                print(f"\nTool use requested: {tool_use.name}")
                print(f"Tool input: {tool_use.input}")
                print(f"Tool use ID: {tool_use.id}")
                
                # Save the tool_use_id for providing results later
                tool_use_id = tool_use.id

asyncio.run(main())
```

### Event-based streaming approach

For more control over the streaming process, you can use the lower-level event-based approach:

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def main() -> None:
    stream = await client.messages.create(
        max_tokens=1024,
        messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
        model="claude-3-5-sonnet-20240620",
        tools=[{
            "name": "get_weather", 
            "description": "Get weather information", 
            "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
        }],
        stream=True,
    )
    
    # For handling partial JSON from tool_use events
    partial_json = ""
    tool_use_id = None
    
    async for event in stream:
        if event.type == "content_block_delta" and hasattr(event.delta, "type"):
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
            elif event.delta.type == "input_json_delta":
                # Accumulate partial JSON for tool input
                partial_json += event.delta.partial_json
        elif event.type == "content_block_stop" and hasattr(event, "content_block"):
            if event.content_block.type == "tool_use":
                # Tool use block is complete
                print(f"\nTool use complete: {event.content_block.name}")
                tool_use_id = event.content_block.id
                # Now the JSON is complete and can be parsed
                tool_input = json.loads(partial_json)
                partial_json = ""  # Reset for potential next tool
```

### Key considerations for async implementation

1. **Event type handling**: Process different event types properly
   - `content_block_start` for beginning of content blocks
   - `content_block_delta` for incremental updates
   - `content_block_stop` for completion of blocks
   - `message_start` and `message_stop` for message boundaries

2. **Partial JSON accumulation**: Tool use input is sent as partial JSON that must be accumulated
   - Collect `input_json_delta` events until a complete JSON object is formed
   - Only parse the JSON after receiving the corresponding `content_block_stop` event

3. **Error handling**: Implement timeouts and exception handling
   - Set reasonable timeouts for async operations
   - Handle network errors and API exceptions
   - Use try/except blocks around async operations

## Tool_use_id tracking in conversation history

The `tool_use_id` is a unique identifier that connects tool use requests from Claude with your tool results. Proper tracking is essential:

### Event-based tracking pattern

```python
import asyncio
import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def main():
    # Track tool use requests
    tool_requests = {}
    conversation = [
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ]
    
    # First message to request tool use
    async with client.messages.stream(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=conversation,
        tools=[{
            "name": "get_weather", 
            "description": "Get weather information", 
            "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
        }],
    ) as stream:
        async for event in stream:
            if event.type == "tool_use":
                # Save the tool request with its ID
                tool_requests[event.tool_use.id] = {
                    "name": event.tool_use.name,
                    "input": event.tool_use.input
                }
                
                # Add the assistant's response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": event.tool_use.id,
                        "name": event.tool_use.name,
                        "input": event.tool_use.input
                    }]
                })
    
    # If tool requests were made
    if tool_requests:
        # For each tool request, execute the tool and collect results
        tool_results = []
        for tool_id, request in tool_requests.items():
            # Execute the tool
            if request["name"] == "get_weather":
                result = "72°F and sunny"
                
                # Format the tool result with the correct tool_use_id
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result
                })
        
        # Add tool results to conversation
        conversation.append({
            "role": "user",
            "content": tool_results
        })
        
        # Continue the conversation with the tool results
        response = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=conversation
        )
        
        print("\nFinal response:")
        print(response.content[0].text)

asyncio.run(main())
```

### Keys to proper tool_use_id tracking

1. **Store the complete conversation history** including all tool use requests and results
2. **Maintain a mapping** between `tool_use_id` values and tool requests
3. **Always reference the correct tool_use_id** when providing tool results
4. **Match tool result order** with the original tool use order when handling multiple tools
5. **Verify that each tool_use_id is valid** before sending tool results

## Resuming a stream after tool execution

Properly resuming a stream after tool execution requires maintaining conversation state:

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def execute_tool(tool_name, tool_input):
    """Simulate executing a tool based on name and input"""
    if tool_name == "get_weather":
        location = tool_input.get("location", "Unknown")
        return f"72°F and sunny in {location}"
    return "Tool execution failed"

async def main():
    # Initialize conversation history
    conversation = [
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ]
    
    # First request - expect a tool use request
    print("Sending initial request...")
    response = await client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=conversation,
        tools=[{
            "name": "get_weather", 
            "description": "Get weather information", 
            "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
        }],
    )
    
    # Check if Claude wants to use a tool
    if response.stop_reason == "tool_use" and any(block.type == "tool_use" for block in response.content):
        # Find the tool use request
        for block in response.content:
            if block.type == "tool_use":
                tool_use = block
                print(f"Tool requested: {tool_use.name}")
                print(f"Tool input: {tool_use.input}")
                print(f"Tool ID: {tool_use.id}")
                
                # Execute the tool
                tool_result = await execute_tool(tool_use.name, tool_use.input)
                
                # Add the assistant's tool use request to the conversation
                conversation.append({
                    "role": "assistant",
                    "content": [block]
                })
                
                # Add the tool result to the conversation
                conversation.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": tool_result
                        }
                    ]
                })
                
                # Resume the stream with the updated conversation
                print("\nResuming stream with tool results...")
                async with client.messages.stream(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=conversation,
                    tools=[{
                        "name": "get_weather", 
                        "description": "Get weather information", 
                        "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
                    }],
                ) as stream:
                    async for text in stream.text_stream:
                        print(text, end="", flush=True)

asyncio.run(main())
```

### Best practices for resuming streams

1. **Preserve the full conversation history** including all tool use requests and results
2. **Include the tools parameter** when resuming the stream to enable potential additional tool use
3. **Maintain identical tool definitions** between requests
4. **Add the tool results as a new user message** in the conversation
5. **Structure the message content correctly** with appropriate role and content format

## Parameter validation for streaming tools

Robust parameter validation is crucial for preventing errors during streaming:

```python
def validate_tool_input(tool_name, tool_input, tools):
    """Validate tool input against the tool's schema"""
    # Find the tool definition
    tool_def = next((t for t in tools if t["name"] == tool_name), None)
    if not tool_def:
        return False, f"Unknown tool: {tool_name}"
    
    # Get the input schema
    schema = tool_def["input_schema"]
    required_fields = schema.get("required", [])
    
    # Check required fields
    for field in required_fields:
        if field not in tool_input or tool_input[field] is None:
            return False, f"Missing required parameter: {field}"
    
    # Check property types (simple check)
    properties = schema.get("properties", {})
    for param_name, param_value in tool_input.items():
        if param_name in properties:
            param_type = properties[param_name].get("type")
            
            # Basic type checking
            if param_type == "number" and not isinstance(param_value, (int, float)):
                return False, f"Parameter {param_name} must be a number"
            elif param_type == "integer" and not isinstance(param_value, int):
                return False, f"Parameter {param_name} must be an integer"
            elif param_type == "string" and not isinstance(param_value, str):
                return False, f"Parameter {param_name} must be a string"
    
    return True, "Valid input"
```

### Handling validation in streaming context

```python
async def stream_with_validation(prompt, tools):
    """Stream with validation for tool parameters"""
    client = AsyncAnthropic()
    
    # Start streaming
    async with client.messages.stream(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
    ) as stream:
        # Buffer for accumulating tool use blocks
        tool_use_blocks = []
        
        # Process the stream
        async for event in stream:
            # If this is text content, print it
            if event.type == "text":
                print(event.text, end="", flush=True)
            
            # If this is a tool use event, collect it
            elif event.type == "tool_use":
                tool_use = event.tool_use
                
                # Validate the tool parameters
                is_valid, message = validate_tool_input(tool_use.name, tool_use.input, tools)
                
                if is_valid:
                    # Execute the tool
                    tool_result = await execute_tool(tool_use.name, tool_use.input)
                    
                    # Create a tool result object
                    result = {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": tool_result
                    }
                else:
                    # Return an error
                    result = {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": message,
                        "is_error": True
                    }
                
                # Save the result for continuing the conversation
                return result
```

### Validation best practices

1. **Validate against the tool's schema** defined in the input_schema
2. **Check all required parameters** are present and non-null
3. **Perform type checking and conversion** where appropriate
4. **Add security validation** to prevent injection attacks
5. **Return helpful error messages** when validation fails
6. **Include `is_error: true`** in tool results when validation fails

## Handling common errors in streaming tools

The most common error with streaming tool use is the "unexpected tool_use_id" error:

```
{"type":"error","error":{"type":"invalid_request_error","message":"messages.0.content.0: unexpected `tool_use_id` found in `tool_result` blocks: toolu_01NFgHqwavux2Xkqi4T6owNk. Each `tool_result` block must have a corresponding `tool_use` block in the previous message."}}
```

### Implementation for preventing tool_use_id errors

```python
def fix_tool_use_id_mismatch(conversation):
    """Fix conversation where tool_use_id doesn't match or is unexpected"""
    # Find all tool_use blocks and their IDs
    tool_use_ids = set()
    for msg in conversation:
        if msg["role"] == "assistant":
            for content in msg["content"]:
                if isinstance(content, dict) and content.get("type") == "tool_use":
                    tool_use_ids.add(content["id"])
    
    # Verify all tool_result blocks have matching tool_use_id
    for idx, msg in enumerate(conversation):
        if msg["role"] == "user":
            valid_content = []
            for content in msg["content"]:
                if isinstance(content, dict) and content.get("type") == "tool_result":
                    tool_use_id = content.get("tool_use_id")
                    if tool_use_id in tool_use_ids:
                        # This is a valid tool_result
                        valid_content.append(content)
                        # Remove from the set to ensure one-to-one matching
                        tool_use_ids.remove(tool_use_id)
                    else:
                        print(f"Removing invalid tool_result with ID: {tool_use_id}")
                else:
                    valid_content.append(content)
            
            # Replace the message content with valid content only
            conversation[idx]["content"] = valid_content
    
    return conversation
```

### Error handling with timeouts

```python
import asyncio
import time

async def stream_with_timeout(prompt, tools, timeout_seconds=60):
    """Stream with timeout to prevent infinite loops"""
    start_time = time.time()
    
    client = AsyncAnthropic()
    
    try:
        # Create a task with timeout
        stream_task = asyncio.create_task(
            client.messages.stream(
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20240620",
                tools=tools,
            )
        )
        
        # Wait for the stream with a timeout
        stream = await asyncio.wait_for(stream_task, timeout=timeout_seconds)
        
        async with stream as response_stream:
            async for event in response_stream:
                # Process event...
                
                # Check if we're approaching the timeout
                if time.time() - start_time > timeout_seconds - 5:
                    print("Approaching timeout, finishing stream processing")
                    break
                
    except asyncio.TimeoutError:
        print("Stream timeout occurred")
        # Handle timeout gracefully
        return {"error": "Operation timed out"}
    except Exception as e:
        print(f"Error during streaming: {str(e)}")
        return {"error": str(e)}
```

## Best practices and recommendations

Based on the comprehensive research into the Claude API's tool streaming implementation, here are the key recommendations:

1. **Always use a state tracking system** that records tool_use_id values from Claude and ensures each tool_result references a valid ID

2. **Process events in the correct order** and accumulate JSON content from partial deltas before processing

3. **Implement proper validation** for tool parameters and handle error cases gracefully

4. **Use timeouts and circuit breakers** to prevent infinite loops during streaming

5. **Maintain a complete conversation history** including all tool use requests and results

6. **Include detailed debugging information** in development to help diagnose issues

7. **Follow the SSE event model** carefully, handling all relevant event types

8. **When providing tool results**, ensure their format exactly matches the API documentation

9. **Handle multiple tool requests properly** by tracking each tool_use_id individually

10. **Test edge cases thoroughly**, especially around streaming interruptions and error recovery

## Conclusion

Implementing tool use during streaming with the Claude API requires careful attention to async patterns, conversation state management, and error handling. By following the patterns and best practices outlined in this guide, you can build robust applications that leverage Claude's powerful tool capabilities while maintaining a responsive, streaming user experience.

Proper async generator/iterator implementation, meticulous tool_use_id tracking, careful stream resumption techniques, and thorough parameter validation are the four key pillars of a successful Claude API tool streaming implementation. With these elements in place, you can create applications that seamlessly integrate external tools while maintaining the benefits of streaming responses.
