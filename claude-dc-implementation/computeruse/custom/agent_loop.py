#!/usr/bin/env python3
"""
Minimal agent loop implementation for Claude with computer use capabilities.
Focuses on core features:
- Streaming responses with token-by-token output
- Tool use integrated with streaming
- Thinking token budget management
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_custom')

try:
    import anthropic
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
    sys.exit(1)

# Computer use tool definition
COMPUTER_USE_TOOL = {
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
            }
        },
        "required": ["action"]
    }
}

# Bash tool definition
BASH_TOOL = {
    "name": "bash",
    "description": "Execute bash commands on the system",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            }
        },
        "required": ["command"]
    }
}

# System prompt with explicit instructions for tool usage
SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. computer_20250124 - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter

2. bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute
   * Example: Use bash(command="ls -la") NOT bash()

Be precise and careful with tool parameters. Always include all required parameters for each tool.
When using tools, wait for their output before continuing.
"""

class ToolResult:
    """Simple container for tool execution results"""
    def __init__(self, output: Optional[str] = None, error: Optional[str] = None, base64_image: Optional[str] = None):
        self.output = output
        self.error = error
        self.base64_image = base64_image

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a tool based on name and input parameters
    Returns a ToolResult with output, error, or base64_image
    """
    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
    
    try:
        # Validate parameters first
        valid, error_msg = validate_tool_parameters(tool_name, tool_input)
        if not valid:
            return ToolResult(error=f"Invalid parameters: {error_msg}")
        
        # Execute the appropriate tool
        if tool_name == "computer_20250124":
            return await execute_computer_tool(tool_input)
        elif tool_name == "bash":
            return await execute_bash_tool(tool_input)
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")

def validate_tool_parameters(tool_name: str, tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate tool parameters before execution
    Returns (is_valid, error_message)
    """
    if tool_name == "computer_20250124":
        # Check for action parameter
        if "action" not in tool_input:
            return False, "Missing required 'action' parameter"
            
        action = tool_input.get("action")
        
        # Validate parameters based on action
        if action in ["move_mouse", "left_button_press"]:
            if "coordinates" not in tool_input:
                return False, f"Missing required 'coordinates' parameter for {action}"
                
            # Check coordinates format
            coordinates = tool_input.get("coordinates")
            if not isinstance(coordinates, list) or len(coordinates) != 2:
                return False, "Invalid coordinates format. Expected [x, y]"
                
        elif action == "type_text":
            if "text" not in tool_input:
                return False, "Missing required 'text' parameter for type_text"
    
    elif tool_name == "bash":
        # Check for command parameter
        if "command" not in tool_input:
            return False, "Missing required 'command' parameter"
    
    return True, "Parameters valid"

async def execute_computer_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a computer use tool action
    """
    action = tool_input.get("action")
    
    # Mock implementation - in real use, this would use pyautogui or similar
    logger.info(f"Executing computer action: {action}")
    
    if action == "screenshot":
        # In a real implementation, capture actual screenshot
        return ToolResult(output="Screenshot captured")
        
    elif action == "move_mouse":
        coordinates = tool_input.get("coordinates", [0, 0])
        # In a real implementation: pyautogui.moveTo(coordinates[0], coordinates[1])
        return ToolResult(output=f"Mouse moved to {coordinates}")
        
    elif action == "left_button_press":
        coordinates = tool_input.get("coordinates", [0, 0])
        # In a real implementation: pyautogui.click(coordinates[0], coordinates[1])
        return ToolResult(output=f"Mouse clicked at {coordinates}")
        
    elif action == "type_text":
        text = tool_input.get("text", "")
        # In a real implementation: pyautogui.write(text)
        return ToolResult(output=f"Typed text: {text}")
        
    else:
        return ToolResult(output=f"Executed {action} (mock implementation)")

async def execute_bash_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a bash command
    """
    command = tool_input.get("command", "")
    if not command:
        return ToolResult(error="Empty command")
    
    try:
        # In a real implementation, this would use subprocess
        logger.info(f"Executing bash command: {command}")
        
        # Mock implementation for testing
        if command == "ls":
            output = "file1.txt\nfile2.txt\ndirectory1/"
        elif command == "pwd":
            output = "/home/user"
        elif command.startswith("echo"):
            output = command[5:]  # Return what comes after "echo "
        else:
            output = f"Executed: {command} (mock implementation)"
            
        return ToolResult(output=output)
    except Exception as e:
        return ToolResult(error=f"Command execution failed: {str(e)}")

async def prepare_thinking_settings(enable_thinking: bool = True, budget_tokens: int = 4000) -> Optional[Dict[str, Any]]:
    """
    Configure thinking settings for Claude API request
    """
    if not enable_thinking:
        return None
    
    return {
        "type": "enabled",
        "budget_tokens": max(1024, budget_tokens)  # Minimum 1024 tokens
    }

def apply_cache_control(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply cache control to optimize token usage
    Mark user messages as ephemeral for prompt caching
    """
    if not messages:
        return messages
        
    # Create a copy to avoid modifying the original
    processed_messages = []
    
    # Set cache breakpoints for recent turns (up to 2 most recent, excluding the last)
    breakpoints_remaining = 2
    for i, message in enumerate(reversed(messages)):
        if message["role"] == "user":
            # Skip the most recent user message (no caching for latest message)
            if i == 0:
                processed_messages.insert(0, message.copy())
                continue
                
            if breakpoints_remaining > 0:
                # Copy the message to avoid modifying original
                msg_copy = message.copy()
                
                # Handle both string and list content types
                if isinstance(msg_copy.get("content", ""), list):
                    for content_block in msg_copy["content"]:
                        if isinstance(content_block, dict) and content_block.get("type") == "text":
                            content_block["cache_control"] = "ephemeral"
                else:
                    # Convert string content to list with cache control
                    content = msg_copy.get("content", "")
                    msg_copy["content"] = [
                        {"type": "text", "text": content, "cache_control": "ephemeral"}
                    ]
                
                processed_messages.insert(0, msg_copy)
                breakpoints_remaining -= 1
            else:
                processed_messages.insert(0, message.copy())
        else:
            processed_messages.insert(0, message.copy())
    
    return processed_messages

async def stream_to_claude(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    model: str = "claude-3-7-sonnet-20250219",
    enable_streaming: bool = True,
    enable_thinking: bool = True,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    api_key: Optional[str] = None,
    max_tokens: int = 16000,
    thinking_budget: int = 4000
):
    """
    Stream a request to Claude API with all features enabled
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key provided and ANTHROPIC_API_KEY not set in environment")
    
    # Initialize the Anthropic client
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    # Apply prompt caching if enabled
    if enable_prompt_caching:
        messages = apply_cache_control(messages)
        logger.info("Applied prompt caching to messages")
    
    # Configure thinking if enabled
    thinking = None
    if enable_thinking:
        thinking = await prepare_thinking_settings(True, thinking_budget)
        logger.info(f"Enabled thinking with budget: {thinking_budget}")
    
    # Configure beta flags
    beta_flags = []
    
    # Required for computer use tools
    beta_flags.append("computer-use-2025-01-24")
    
    # Add prompt caching beta flag if enabled
    if enable_prompt_caching:
        beta_flags.append("cache-control-2024-07-01")
    
    # Add extended output beta flag if enabled
    if enable_extended_output:
        beta_flags.append("output-128k-2025-02-19")
    
    # Combine beta flags
    beta = ",".join(beta_flags) if beta_flags else None
    
    # Create API parameters
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "system": SYSTEM_PROMPT,
        "tools": tools,
        "stream": enable_streaming
    }
    
    # Add thinking if configured
    if thinking:
        api_params["thinking"] = thinking
    
    # Add beta flags if available
    if beta:
        api_params["anthropic_beta"] = beta
    
    logger.info(f"Sending request to Claude API with parameters: {api_params}")
    
    try:
        # Make the API call with streaming
        stream = await client.messages.create(**api_params)
        return stream
    except Exception as e:
        logger.error(f"Error during API call: {str(e)}")
        raise

async def agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    enable_streaming: bool = True,
    enable_thinking: bool = True,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: int = 4000,
    callbacks: Optional[Dict[str, Callable]] = None
):
    """
    Main agent loop for Claude with computer use capabilities
    
    Args:
        user_input: The user's message
        conversation_history: The conversation history
        enable_streaming: Whether to enable streaming responses
        enable_thinking: Whether to enable thinking mode
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking
        callbacks: Optional callbacks for UI integration:
            - on_text(text): Called when new text is received
            - on_tool_use(tool_name, tool_input): Called when a tool is used
            - on_tool_result(tool_name, tool_input, tool_result): Called when a tool returns results
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Initialize callbacks if not provided
    if callbacks is None:
        callbacks = {}
    
    # Default callbacks that print to console
    def default_on_text(text):
        print(text, end="", flush=True)
        
    def default_on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        
    def default_on_tool_result(tool_name, tool_input, tool_result):
        print(f"\nTool output: {tool_result.output or tool_result.error}", flush=True)
    
    # Get callbacks or use defaults
    on_text = callbacks.get("on_text", default_on_text)
    on_tool_use = callbacks.get("on_tool_use", default_on_tool_use)
    on_tool_result = callbacks.get("on_tool_result", default_on_tool_result)
    
    # Add the user message to the conversation
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Define available tools
    tools = [COMPUTER_USE_TOOL, BASH_TOOL]
    
    # Call Claude API with streaming
    try:
        stream = await stream_to_claude(
            messages=conversation_history,
            tools=tools,
            model=model,
            enable_streaming=enable_streaming,
            enable_thinking=enable_thinking,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget
        )
        
        # Process the stream
        assistant_response = {"role": "assistant", "content": []}
        tool_use_detected = False
        current_tool_use = None
        
        for chunk in stream:
            # Process different event types
            if hasattr(chunk, "type"):
                if chunk.type == "content_block_start":
                    # New content block started
                    if chunk.content_block.type == "text":
                        # Text content - call callback and add to response
                        text = chunk.content_block.text
                        on_text(text)
                        assistant_response["content"].append({
                            "type": "text",
                            "text": text
                        })
                    elif chunk.content_block.type == "tool_use":
                        # Tool use detected
                        tool_use_detected = True
                        current_tool_use = {
                            "name": chunk.content_block.name,
                            "input": chunk.content_block.input,
                            "id": getattr(chunk.content_block, "id", "tool_1")
                        }
                        on_tool_use(current_tool_use["name"], current_tool_use["input"])
                
                elif chunk.type == "content_block_delta":
                    # Content update
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        # Update text content
                        text = chunk.delta.text
                        on_text(text)
                        if assistant_response["content"] and assistant_response["content"][-1]["type"] == "text":
                            assistant_response["content"][-1]["text"] += text
                
                elif chunk.type == "message_stop":
                    # Message complete
                    logger.info("Message complete")
                    break
        
        # Add the assistant response to conversation history
        conversation_history.append(assistant_response)
        
        # If tool use was detected, execute the tool and continue
        if tool_use_detected and current_tool_use:
            logger.info(f"Executing tool: {current_tool_use['name']}")
            
            # Execute the tool
            tool_result = await execute_tool(
                current_tool_use["name"],
                current_tool_use["input"]
            )
            
            # Call tool result callback
            on_tool_result(current_tool_use["name"], current_tool_use["input"], tool_result)
            
            # Format the tool result
            tool_result_content = []
            if tool_result.error:
                tool_result_content = [{"type": "error", "error": tool_result.error}]
            else:
                if tool_result.output:
                    tool_result_content.append({
                        "type": "text",
                        "text": tool_result.output
                    })
                if tool_result.base64_image:
                    tool_result_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": tool_result.base64_image
                        }
                    })
            
            # Add tool result to conversation
            conversation_history.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": current_tool_use["id"],
                    "content": tool_result_content
                }]
            })
            
            # Continue the conversation with the tool result
            conversation_history = await agent_loop_continue(
                conversation_history,
                enable_streaming=enable_streaming,
                enable_thinking=enable_thinking,
                enable_prompt_caching=enable_prompt_caching,
                enable_extended_output=enable_extended_output,
                model=model,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                callbacks=callbacks
            )
        
        return conversation_history
        
    except Exception as e:
        logger.error(f"Error in agent loop: {str(e)}")
        error_msg = f"I encountered an error: {str(e)}"
        print(f"\nError: {str(e)}")
        
        # Call text callback with error
        if "on_text" in callbacks:
            callbacks["on_text"](f"\n{error_msg}")
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        })
        return conversation_history

async def agent_loop_continue(
    conversation_history: List[Dict[str, Any]],
    enable_streaming: bool = True,
    enable_thinking: bool = True,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: int = 4000,
    callbacks: Optional[Dict[str, Callable]] = None
):
    """
    Continue the agent loop after a tool execution
    
    Args:
        conversation_history: The conversation history
        enable_streaming: Whether to enable streaming responses
        enable_thinking: Whether to enable thinking mode
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking
        callbacks: Optional callbacks for UI integration
    """
    # Define available tools
    tools = [COMPUTER_USE_TOOL, BASH_TOOL]
    
    # Initialize callbacks if not provided
    if callbacks is None:
        callbacks = {}
    
    # Default callbacks that print to console
    def default_on_text(text):
        print(text, end="", flush=True)
        
    def default_on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        
    def default_on_tool_result(tool_name, tool_input, tool_result):
        print(f"\nTool output: {tool_result.output or tool_result.error}", flush=True)
    
    # Get callbacks or use defaults
    on_text = callbacks.get("on_text", default_on_text)
    on_tool_use = callbacks.get("on_tool_use", default_on_tool_use)
    on_tool_result = callbacks.get("on_tool_result", default_on_tool_result)
    
    try:
        # Call Claude API with streaming
        stream = await stream_to_claude(
            messages=conversation_history,
            tools=tools,
            model=model,
            enable_streaming=enable_streaming,
            enable_thinking=enable_thinking,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget
        )
        
        # Process the stream
        assistant_response = {"role": "assistant", "content": []}
        tool_use_detected = False
        current_tool_use = None
        
        for chunk in stream:
            # Process different event types
            if hasattr(chunk, "type"):
                if chunk.type == "content_block_start":
                    # New content block started
                    if chunk.content_block.type == "text":
                        # Text content - call callback and add to response
                        text = chunk.content_block.text
                        on_text(text)
                        assistant_response["content"].append({
                            "type": "text",
                            "text": text
                        })
                    elif chunk.content_block.type == "tool_use":
                        # Tool use detected
                        tool_use_detected = True
                        current_tool_use = {
                            "name": chunk.content_block.name,
                            "input": chunk.content_block.input,
                            "id": getattr(chunk.content_block, "id", "tool_1")
                        }
                        on_tool_use(current_tool_use["name"], current_tool_use["input"])
                
                elif chunk.type == "content_block_delta":
                    # Content update
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        # Update text content
                        text = chunk.delta.text
                        on_text(text)
                        if assistant_response["content"] and assistant_response["content"][-1]["type"] == "text":
                            assistant_response["content"][-1]["text"] += text
                
                elif chunk.type == "message_stop":
                    # Message complete
                    logger.info("Message complete")
                    break
        
        # Add the assistant response to conversation history
        conversation_history.append(assistant_response)
        
        # If tool use was detected, execute the tool and continue recursively
        if tool_use_detected and current_tool_use:
            logger.info(f"Executing tool: {current_tool_use['name']}")
            
            # Execute the tool
            tool_result = await execute_tool(
                current_tool_use["name"],
                current_tool_use["input"]
            )
            
            # Call tool result callback
            on_tool_result(current_tool_use["name"], current_tool_use["input"], tool_result)
            
            # Format the tool result
            tool_result_content = []
            if tool_result.error:
                tool_result_content = [{"type": "error", "error": tool_result.error}]
            else:
                if tool_result.output:
                    tool_result_content.append({
                        "type": "text",
                        "text": tool_result.output
                    })
                if tool_result.base64_image:
                    tool_result_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": tool_result.base64_image
                        }
                    })
            
            # Add tool result to conversation
            conversation_history.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": current_tool_use["id"],
                    "content": tool_result_content
                }]
            })
            
            # Continue the conversation recursively
            conversation_history = await agent_loop_continue(
                conversation_history,
                enable_streaming=enable_streaming,
                enable_thinking=enable_thinking,
                enable_prompt_caching=enable_prompt_caching,
                enable_extended_output=enable_extended_output,
                model=model,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                callbacks=callbacks
            )
        
        return conversation_history
        
    except Exception as e:
        logger.error(f"Error in agent loop continuation: {str(e)}")
        error_msg = f"I encountered an error: {str(e)}"
        print(f"\nError: {str(e)}")
        
        # Call text callback with error
        if "on_text" in callbacks:
            callbacks["on_text"](f"\n{error_msg}")
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        })
        return conversation_history

async def main():
    """
    Main entry point for the custom agent
    """
    print("\nClaude Custom Agent (streaming + tool use + thinking)\n")
    print("Enter your message (or 'exit' to quit):")
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        # Get user input
        user_input = input("> ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        # Process user input in the agent loop
        conversation_history = await agent_loop(
            user_input=user_input,
            conversation_history=conversation_history,
            enable_streaming=True,
            enable_thinking=True,
            enable_prompt_caching=True,
            enable_extended_output=True
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")