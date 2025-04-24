# Custom Claude Computer Use Implementation: Complete Guide

This guide provides detailed information for implementing a custom Claude computer use agent with streaming capabilities, tool use integration, and thinking token management. This implementation focuses on being minimal, reliable, and AI-first, designed specifically for Claude models.

## 1. Minimal Agent Loop Architecture

The agent loop is the core component of a Claude computer use implementation, responsible for managing the conversation flow between Claude and the environment/tools.

### Core Components

1. **Message Handler**: Manages the conversation state and message history
2. **Tool Manager**: Handles registration, validation, and execution of tools
3. **API Client**: Communicates with the Claude API, supporting streaming responses
4. **UI Renderer**: Displays streaming responses and tool outputs in real-time
5. **Context Manager**: Handles context window optimization and prompt caching

### Agent Loop Flow

```python
async def agent_loop(user_input, conversation_history, tools, model="claude-3-7-sonnet-20250219"):
    """
    Basic agent loop for Claude with computer use capabilities
    """
    # 1. Prepare the message with tool definitions
    messages = prepare_messages(user_input, conversation_history)
    
    # 2. Send to Claude API with streaming enabled
    async for chunk in stream_to_claude(messages, tools, model):
        # 3. Process streaming chunks (text content or tool use)
        if is_tool_use_chunk(chunk):
            # 4. Execute tool when all tool use details are received
            tool_result = await execute_tool(chunk.tool_use)
            
            # 5. Send tool result back to Claude
            await continue_with_tool_result(tool_result, conversation_history)
        else:
            # 6. Stream regular text content to UI
            yield chunk.content
```

### Thinking Token Management

Claude 3.7 Sonnet supports extended thinking mode which can significantly improve reasoning. To implement properly:

```python
def prepare_thinking_settings(enable_thinking=True, budget_tokens=4000):
    """
    Configure thinking settings for Claude API request
    """
    if not enable_thinking:
        return None
    
    return {
        "type": "enabled",
        "budget_tokens": max(1024, budget_tokens)  # Minimum 1024 tokens
    }

async def stream_to_claude(messages, tools, model, enable_thinking=True):
    """
    Stream to Claude with thinking enabled
    """
    thinking = prepare_thinking_settings(enable_thinking)
    
    response = client.messages.stream(
        model=model,
        messages=messages,
        tools=tools,
        thinking=thinking,
        max_tokens=16000,  # Adjust based on needs
        stream=True,
        anthropic_beta="cache-control-2024-07-01,output-128k-2025-02-19"
    )
    
    # Process stream and yield chunks
    async for chunk in response:
        if chunk.type == "thinking_delta":
            # Handle thinking content as desired
            process_thinking(chunk)
        elif chunk.type == "content_block_delta":
            # Handle regular content
            yield chunk
        elif chunk.type == "tool_use":
            # Handle tool use
            yield chunk
```

## 2. API Integration

### Streaming API Setup

```python
import anthropic
import asyncio
import os

# Initialize client
client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

async def stream_with_tools(messages, tools):
    """
    Stream responses from Claude with tools
    """
    try:
        async with client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=16000,
            messages=messages,
            tools=tools,
            stream=True,
            anthropic_beta="cache-control-2024-07-01,output-128k-2025-02-19"
        ) as stream:
            # Extract both text content and tool use actions
            async for text in stream.text_stream:
                print(text, end="", flush=True)
                
            # Get final message to check for tool use
            message = await stream.get_final_message()
            
            if message.stop_reason == "tool_use":
                # Handle tool use
                tool_use = message.content[-1]
                return tool_use
                
    except Exception as e:
        print(f"Error during streaming: {e}")
        return None
```

### Required Parameters and Beta Flags

The key parameters for streaming with tools:

```python
# Important API parameters for streaming with tools
params = {
    "model": "claude-3-7-sonnet-20250219",  # Or claude-3-5-sonnet-20241022
    "max_tokens": 16000,  # Increase for complex tasks
    "stream": True,  # Enable streaming
    "tools": tool_definitions,  # List of tool definitions
    "anthropic_beta": "cache-control-2024-07-01,output-128k-2025-02-19"  # For cache control and extended output
}

# When using thinking
if enable_thinking:
    params["thinking"] = {
        "type": "enabled",
        "budget_tokens": 4000  # At least 1024, recommended 4000+
    }
```

### Prompt Caching Implementation

Prompt caching is crucial for performance in multi-turn conversations:

```python
def apply_cache_control(messages):
    """
    Apply cache control to optimize token usage
    """
    # Set cache breakpoints for recent turns (up to 3)
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(content := message["content"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                # Mark this message as a cache breakpoint
                content[-1]["cache_control"] = {"type": "ephemeral"}
            else:
                # Remove any existing cache control
                content[-1].pop("cache_control", None)
                break
    
    return messages
```

## 3. Tool Integration

### Computer Use Tool Definition

```python
# Define the computer use tool
computer_use_tool = {
    "name": "computer_20250124",
    "description": "Control a computer by taking actions like mouse clicks, keyboard input, and taking screenshots",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "screenshot", "left_button_press", "move_mouse", "type_text",
                    "press_key", "hold_key", "left_mouse_down", "left_mouse_up",
                    "scroll", "triple_click", "wait"
                ],
                "description": "The action to perform"
            },
            "coordinates": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The x and y coordinates for mouse actions"
            },
            "text": {
                "type": "string",
                "description": "The text to type or the key to press"
            },
            # Additional properties omitted for brevity
        },
        "required": ["action"]
    }
}
```

### Streamable Tool Output

```python
async def handle_tool_streaming(tool_use_request):
    """
    Handle tool execution with streaming updates
    """
    # Parse the tool request
    tool_name = tool_use_request.name
    tool_input = tool_use_request.input
    
    # Start streaming status updates
    yield f"Executing tool: {tool_name}"
    
    # Execute the tool with progress updates
    if tool_name == "computer_20250124":
        action = tool_input.get("action")
        
        if action == "screenshot":
            yield "Taking screenshot..."
            result = take_screenshot()
            yield "Screenshot captured"
        elif action == "move_mouse":
            coordinates = tool_input.get("coordinates", [0, 0])
            yield f"Moving mouse to {coordinates}"
            result = move_mouse(*coordinates)
            yield "Mouse moved"
        # Handle other actions...
    
    # Return the final tool result
    return {
        "tool_name": tool_name,
        "tool_result": result
    }
```

### Tool Callbacks During Streaming

```python
async def process_streaming_with_tools():
    """
    Process a streaming response with tool callbacks
    """
    # Initial message to Claude
    messages = [{"role": "user", "content": "Send an email to John about the project status"}]
    
    # Stream the response
    async with client.messages.stream(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        messages=messages,
        tools=[computer_use_tool],
        stream=True
    ) as stream:
        tool_use_detected = False
        
        # Process the stream
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text":
                # Handle text streaming
                print(event.delta.text, end="", flush=True)
            elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                # Tool use detected
                tool_use_detected = True
                print("\nTool use detected!")
            
        # Get the final message
        message = await stream.get_final_message()
        
        # If tool use was detected, execute the tool
        if tool_use_detected:
            tool_use = next((block for block in message.content if block.type == "tool_use"), None)
            
            if tool_use:
                # Execute the tool
                tool_result = await execute_tool(tool_use.name, tool_use.input)
                
                # Continue the conversation with the tool result
                continue_messages = messages + [
                    {"role": "assistant", "content": [{"type": "tool_use", "tool_use": tool_use}]},
                    {"role": "user", "content": [{"type": "tool_result", "tool_result": {"tool_name": tool_use.name, "result": tool_result}}]}
                ]
                
                # Stream the continuation
                await stream_response(continue_messages)
```

### Parameter Validation

```python
def validate_tool_parameters(tool_name, tool_input):
    """
    Validate tool parameters before execution
    """
    if tool_name == "computer_20250124":
        action = tool_input.get("action")
        
        # Validate action
        if not action:
            return False, "Missing required 'action' parameter"
            
        # Validate parameters based on action
        if action == "move_mouse" or action == "left_button_press":
            if "coordinates" not in tool_input:
                return False, "Missing required 'coordinates' parameter for mouse action"
            
            coordinates = tool_input.get("coordinates")
            if not isinstance(coordinates, list) or len(coordinates) != 2:
                return False, "Invalid coordinates format. Expected [x, y]"
        
        elif action == "type_text":
            if "text" not in tool_input:
                return False, "Missing required 'text' parameter for type_text action"
    
    return True, "Parameters valid"
```

## 4. UI Considerations

### Lightweight UI Options

```python
import gradio as gr

def create_minimal_ui():
    """
    Create a minimal UI for Claude computer use
    """
    with gr.Blocks() as app:
        with gr.Row():
            with gr.Column(scale=2):
                # Chat interface
                chatbot = gr.Chatbot(height=600)
                user_input = gr.Textbox(placeholder="Ask Claude to do something...", lines=2)
                submit_btn = gr.Button("Submit")
            
            with gr.Column(scale=3):
                # Screen display
                screen_display = gr.Image(label="Computer Screen", height=600)
                refresh_btn = gr.Button("Refresh Screen")
        
        # Handle user input
        submit_btn.click(
            fn=process_user_input,
            inputs=[user_input, chatbot],
            outputs=[chatbot, screen_display]
        )
        
        # Refresh screen
        refresh_btn.click(
            fn=refresh_screen,
            inputs=[],
            outputs=[screen_display]
        )
    
    return app

# Launch the UI
if __name__ == "__main__":
    app = create_minimal_ui()
    app.launch(server_name="0.0.0.0", server_port=8501)
```

### Streaming Response Rendering

```javascript
// Efficient streaming response handling in JS
function setupStreaming() {
    const responseContainer = document.getElementById('response-container');
    const toolOutputContainer = document.getElementById('tool-output');
    
    // Function to process streaming chunks
    async function processStream(reader) {
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Decode and process the chunk
            buffer += decoder.decode(value, { stream: true });
            
            // Process and render content
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (!line.trim()) continue;
                
                try {
                    const data = JSON.parse(line);
                    
                    if (data.type === 'content') {
                        // Render text content
                        responseContainer.textContent += data.text;
                    } else if (data.type === 'tool_use') {
                        // Render tool use
                        toolOutputContainer.innerHTML = `
                            <div class="tool-execution">
                                <h3>Executing: ${data.tool_name}</h3>
                                <pre>${JSON.stringify(data.input, null, 2)}</pre>
                            </div>
                        `;
                    }
                } catch (e) {
                    console.error('Error parsing stream chunk:', e);
                }
            }
        }
    }
    
    // Start streaming
    fetch('/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: document.getElementById('user-input').value 
        })
    })
    .then(response => {
        const reader = response.body.getReader();
        return processStream(reader);
    })
    .catch(error => {
        console.error('Streaming error:', error);
    });
}
```

### Tool Output Visualization

```python
def render_tool_output(tool_name, tool_input, tool_result):
    """
    Render tool output in a user-friendly way
    """
    if tool_name == "computer_20250124":
        action = tool_input.get("action")
        
        if action == "screenshot":
            # Render the screenshot
            return gr.Image(value=tool_result["screenshot_path"])
        elif action == "move_mouse" or action == "left_button_press":
            # Render mouse action visualization
            coordinates = tool_input.get("coordinates", [0, 0])
            screen_img = get_current_screen()
            # Draw a marker at the coordinates
            screen_with_marker = draw_marker_at_coordinates(screen_img, coordinates)
            return gr.Image(value=screen_with_marker)
        elif action == "type_text":
            # Render text input visualization
            return gr.Textbox(value=f"Typed: {tool_input.get('text', '')}")
    
    # Default rendering for other tools
    return gr.JSON(value=tool_result)
```

## 5. Successful Implementation Patterns

### Minimal Working Example

```python
import anthropic
import asyncio
import os
import base64
from PIL import ImageGrab, Image, ImageDraw
import pyautogui
import io

# Initialize Anthropic client
client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Define computer use tool
computer_use_tool = {
    "name": "computer_20250124",
    "description": "Control a computer with basic actions",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["screenshot", "left_button_press", "move_mouse", "type_text"],
                "description": "The action to perform"
            },
            "coordinates": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The x and y coordinates for mouse actions"
            },
            "text": {
                "type": "string",
                "description": "The text to type"
            }
        },
        "required": ["action"]
    }
}

# Tool implementation
async def execute_computer_tool(action, **params):
    if action == "screenshot":
        screenshot = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return {
            "screenshot_data": base64.b64encode(img_byte_arr).decode('utf-8')
        }
    elif action == "move_mouse":
        coordinates = params.get("coordinates", [0, 0])
        pyautogui.moveTo(coordinates[0], coordinates[1])
        return {"success": True}
    elif action == "left_button_press":
        coordinates = params.get("coordinates", [0, 0])
        pyautogui.click(coordinates[0], coordinates[1])
        return {"success": True}
    elif action == "type_text":
        text = params.get("text", "")
        pyautogui.write(text)
        return {"success": True}
    else:
        return {"error": f"Unsupported action: {action}"}

# Agent loop
async def agent_loop(user_input):
    messages = [{"role": "user", "content": user_input}]
    
    async with client.messages.stream(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        messages=messages,
        tools=[computer_use_tool],
        stream=True
    ) as stream:
        # Process text stream
        async for text in stream.text_stream:
            print(text, end="", flush=True)
        
        # Get the final message
        message = await stream.get_final_message()
        
        # Check for tool use
        if message.stop_reason == "tool_use":
            tool_use = next((block for block in message.content if block.type == "tool_use"), None)
            
            if tool_use:
                print(f"\nExecuting tool: {tool_use.tool_use.name}")
                
                # Execute the tool
                action = tool_use.tool_use.input.get("action")
                result = await execute_computer_tool(
                    action,
                    coordinates=tool_use.tool_use.input.get("coordinates"),
                    text=tool_use.tool_use.input.get("text")
                )
                
                # Continue the conversation with the tool result
                continue_messages = messages + [
                    {"role": "assistant", "content": [
                        {"type": "tool_use", "tool_use": {
                            "name": tool_use.tool_use.name,
                            "input": tool_use.tool_use.input
                        }}
                    ]},
                    {"role": "user", "content": [
                        {"type": "tool_result", "tool_result": {
                            "tool_name": tool_use.tool_use.name,
                            "result": result
                        }}
                    ]}
                ]
                
                # Get assistant's response to the tool result
                await agent_loop_continue(continue_messages)

async def agent_loop_continue(messages):
    async with client.messages.stream(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        messages=messages,
        tools=[computer_use_tool],
        stream=True
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)

# Entry point
async def main():
    user_input = input("Ask Claude to do something: ")
    await agent_loop(user_input)

if __name__ == "__main__":
    asyncio.run(main())
```

### Common Pitfalls to Avoid

1. **Not handling streaming tool use properly**: Tools are streamed as separate events that need special handling.

2. **Ignoring thinking tokens**: For complex tasks, enable extended thinking with an appropriate budget.

3. **Missing validation for tool parameters**: Always validate parameters before execution to avoid errors.

4. **Inefficient context management**: Implement prompt caching to optimize token usage.

5. **Poor error handling**: Implement robust error handling for tool execution failures.

```python
# Error handling example
async def safe_execute_tool(tool_name, tool_input):
    try:
        # Validate parameters
        is_valid, error_message = validate_tool_parameters(tool_name, tool_input)
        if not is_valid:
            return {"error": error_message}
        
        # Execute the tool
        if tool_name == "computer_20250124":
            action = tool_input.get("action")
            result = await execute_computer_tool(action, **tool_input)
            return result
    except Exception as e:
        # Log the error
        print(f"Error executing tool {tool_name}: {str(e)}")
        return {"error": f"Tool execution failed: {str(e)}"}
```

### Testing Approach

```python
import unittest
from unittest.mock import patch, MagicMock

class ComputerUseAgentTest(unittest.TestCase):
    @patch('anthropic.AsyncAnthropic')
    @patch('pyautogui.moveTo')
    async def test_move_mouse_action(self, mock_moveTo, mock_client):
        # Set up mocks
        mock_stream = MagicMock()
        mock_message = MagicMock()
        mock_message.stop_reason = "tool_use"
        mock_message.content = [MagicMock(type="tool_use")]
        mock_message.content[0].tool_use.name = "computer_20250124"
        mock_message.content[0].tool_use.input = {"action": "move_mouse", "coordinates": [100, 200]}
        
        mock_stream.get_final_message.return_value = mock_message
        mock_client.return_value.messages.stream.return_value.__aenter__.return_value = mock_stream
        
        # Run the agent
        await agent_loop("Move the mouse to coordinates 100, 200")
        
        # Verify pyautogui.moveTo was called with correct coordinates
        mock_moveTo.assert_called_once_with(100, 200)
```

## Implementation Approach

For a minimal, reliable implementation with AI capabilities:

1. **Start with the agent loop**: Implement a basic agent loop that supports streaming responses and tool execution.

2. **Add tool definitions**: Define the computer use tools with proper schema validation.

3. **Implement tool execution**: Create functions to execute each tool action with proper error handling.

4. **Add streaming support**: Enhance the implementation to handle streaming responses efficiently.

5. **Optimize with prompt caching**: Implement cache breakpoints to improve performance.

6. **Add thinking support**: Enable extended thinking for complex tasks.

7. **Build a minimal UI**: Create a simple UI for testing and interaction.

8. **Test extensively**: Verify that all components work together correctly.

By following these patterns and approaches, you can create a robust, efficient Claude computer use implementation that leverages streaming, tool use, and thinking capabilities.
