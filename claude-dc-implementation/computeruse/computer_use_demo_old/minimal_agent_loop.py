#!/usr/bin/env python3
"""
Minimal Agent Loop for Claude Computer Use with Streaming
This implements a basic agent loop with streaming and computer use beta.
"""

import os
import sys
import asyncio
import json
import logging
import base64
from typing import Dict, Any, List, Callable, Optional, AsyncGenerator
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("minimal_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("minimal_agent")

# Beta flags constants
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
    "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
}

@dataclass
class ToolResult:
    """Result of a tool execution."""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None

@dataclass
class AgentSession:
    """Session state for the agent loop."""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    model: str = "claude-3-7-sonnet-20250219"
    max_tokens: int = 16000  # Must be greater than thinking.budget_tokens
    api_key: Optional[str] = None
    system_prompt: str = "You are Claude, an AI assistant with computer use capabilities."
    client = None

async def execute_screenshot_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Mock implementation of the screenshot tool for testing.
    In a real implementation, this would capture a screenshot.
    """
    logger.info("Taking mock screenshot")
    
    # Generate a small 1x1 transparent PNG for testing
    fake_image_data = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xcc\xec\xf1\x00\x00\x00\x00IEND\xaeB`\x82'
    ).decode('utf-8')
    
    return ToolResult(
        output="Screenshot captured successfully",
        base64_image=fake_image_data
    )

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return the list of tool definitions."""
    return [
        {
            "name": "computer_20250124",
            "description": "Control a computer by taking actions like mouse clicks, keyboard input, and taking screenshots",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["screenshot", "move_mouse", "left_button_press", "type_text"],
                        "description": "The action to perform"
                    },
                    "coordinates": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "The x,y coordinates for mouse actions"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type for type_text action"
                    }
                },
                "required": ["action"]
            }
        },
        {
            "name": "bash",
            "description": "Execute bash commands on the system (read-only operations only)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute (read-only operations only)"
                    }
                },
                "required": ["command"]
            }
        }
    ]

async def execute_mouse_tool(action: str, tool_input: Dict[str, Any]) -> ToolResult:
    """
    Mock implementation of mouse actions.
    In a real implementation, this would control the mouse.
    """
    coordinates = tool_input.get("coordinates", [0, 0])
    if not coordinates or len(coordinates) != 2:
        return ToolResult(error="Invalid coordinates. Expected [x, y]")
    
    x, y = coordinates
    
    if action == "move_mouse":
        logger.info(f"Moving mouse to ({x}, {y})")
        return ToolResult(output=f"Moved mouse to coordinates ({x}, {y})")
    elif action == "left_button_press":
        logger.info(f"Clicking at ({x}, {y})")
        return ToolResult(output=f"Clicked at coordinates ({x}, {y})")
    else:
        return ToolResult(error=f"Unsupported mouse action: {action}")

async def execute_keyboard_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Mock implementation of keyboard actions.
    In a real implementation, this would type text.
    """
    text = tool_input.get("text")
    if not text:
        return ToolResult(error="Missing required 'text' parameter for keyboard action")
    
    logger.info(f"Typing text: {text}")
    return ToolResult(output=f"Typed text: {text}")

async def execute_bash_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a bash command (read-only commands only).
    """
    command = tool_input.get("command")
    if not command:
        return ToolResult(error="Missing required 'command' parameter")
    
    # Security: Only allow read-only commands
    allowed_commands = ["ls", "pwd", "cat", "echo", "date", "whoami", "ps", "grep", "find", "head", "tail"]
    command_parts = command.split()
    if not command_parts or command_parts[0] not in allowed_commands:
        return ToolResult(
            error=f"Command '{command_parts[0] if command_parts else ''}' not allowed. Only read-only commands are permitted."
        )
    
    try:
        # Execute the command
        logger.info(f"Executing bash command: {command}")
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        
        # Return the output
        if result.returncode == 0:
            return ToolResult(output=result.stdout)
        else:
            return ToolResult(error=f"Command failed with exit code {result.returncode}: {result.stderr}")
    except subprocess.TimeoutExpired:
        return ToolResult(error="Command timed out after 10 seconds")
    except Exception as e:
        return ToolResult(error=f"Error executing command: {str(e)}")

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a tool based on the tool name and input.
    """
    try:
        if tool_name == "computer_20250124":
            action = tool_input.get("action")
            if not action:
                return ToolResult(error="Missing required 'action' parameter")
            
            if action == "screenshot":
                return await execute_screenshot_tool(tool_input)
            elif action in ["move_mouse", "left_button_press"]:
                return await execute_mouse_tool(action, tool_input)
            elif action == "type_text":
                return await execute_keyboard_tool(tool_input)
            else:
                return ToolResult(error=f"Unsupported action: {action}")
        elif tool_name == "bash":
            return await execute_bash_tool(tool_input)
        else:
            return ToolResult(error=f"Unsupported tool: {tool_name}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return ToolResult(error=f"Error executing tool {tool_name}: {str(e)}")

def format_tool_result(result: ToolResult) -> List[Dict[str, Any]]:
    """Format a tool result for inclusion in the conversation history."""
    formatted_result = []
    
    # Add text output if present
    if result.output:
        formatted_result.append({
            "type": "text",
            "text": result.output
        })
    
    # Add image if present
    if result.base64_image:
        formatted_result.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": result.base64_image
            }
        })
    
    # Add error if present
    if result.error:
        formatted_result.append({
            "type": "text",
            "text": f"Error: {result.error}"
        })
    
    return formatted_result

async def initialize_session(api_key: Optional[str] = None) -> AgentSession:
    """Initialize a new agent session."""
    session = AgentSession()
    
    # Use provided API key or get from environment
    if api_key:
        session.api_key = api_key
    else:
        session.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not session.api_key:
            raise ValueError("No API key provided and ANTHROPIC_API_KEY not set in environment")
    
    # Initialize the Anthropic client
    try:
        from anthropic import AsyncAnthropic
        session.client = AsyncAnthropic(api_key=session.api_key)
    except ImportError:
        logger.error("Anthropic SDK not installed. Install with: pip install anthropic>=0.49.0")
        raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic>=0.49.0")
    
    return session

async def agent_loop(
    session: AgentSession,
    user_input: str,
    text_callback: Optional[Callable[[str], None]] = None,
    thinking_callback: Optional[Callable[[str], None]] = None,
    tool_use_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    tool_result_callback: Optional[Callable[[ToolResult], None]] = None
) -> None:
    """
    Run a single turn of the agent loop.
    
    Args:
        session: The agent session
        user_input: The user's input
        text_callback: Callback for text output
        thinking_callback: Callback for thinking output
    """
    # Add user message to conversation history
    session.conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Main conversation loop
    tool_execution_needed = True
    
    while tool_execution_needed:
        # Set up API parameters
        api_params = {
            "model": session.model,
            "max_tokens": session.max_tokens,
            "messages": session.conversation_history,
            "system": session.system_prompt,
            "stream": True,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 1024  # Minimum 1024 tokens
            },
            "extra_headers": {
                "anthropic-beta": BETA_FLAGS["computer_use_20250124"]
            }
        }
        
        # Get tool definitions
        tools = get_tool_definitions()
        if tools:
            api_params["tools"] = tools
        
        try:
            # Log API request
            logger.debug(f"Sending request to Claude API with params: {json.dumps({k: str(v)[:100] for k, v in api_params.items() if k != 'messages'})}")
            
            # Make the streaming request
            stream = await session.client.messages.create(**api_params)
            
            # Process the stream
            current_text_content = ""
            tool_use_detected = False
            tool_name = None
            tool_input = None
            tool_id = None
            
            # Collect content blocks for the conversation history
            content_blocks = []
            
            async for chunk in stream:
                if hasattr(chunk, "type"):
                    chunk_type = chunk.type
                    
                    # Process content block start
                    if chunk_type == "content_block_start":
                        block = chunk.content_block
                        
                        # Handle text block start
                        if block.type == "text":
                            logger.debug(f"Text block start: {block.text}")
                            current_text_content = block.text
                            if text_callback:
                                text_callback(block.text)
                            content_blocks.append({
                                "type": "text", 
                                "text": block.text
                            })
                        
                        # Handle tool use block
                        elif block.type == "tool_use":
                            logger.info(f"Tool use detected: {block.name}")
                            tool_use_detected = True
                            tool_name = block.name
                            tool_input = block.input
                            tool_id = getattr(block, "id", f"tool_{len(session.conversation_history)}")
                            
                            # Call tool use callback if provided
                            if tool_use_callback:
                                tool_use_callback(tool_name, tool_input)
                                
                            content_blocks.append({
                                "type": "tool_use",
                                "tool_use": {
                                    "name": tool_name,
                                    "input": tool_input,
                                    "id": tool_id
                                }
                            })
                    
                    # Process content block delta (text updates)
                    elif chunk_type == "content_block_delta" and hasattr(chunk.delta, "text"):
                        text = chunk.delta.text
                        current_text_content += text
                        if text_callback:
                            text_callback(text)
                        logger.debug(f"Text chunk: {text}")
                    
                    # Process thinking output
                    elif chunk_type == "thinking":
                        thinking_text = getattr(chunk, "thinking", "")
                        if thinking_callback:
                            thinking_callback(thinking_text)
                        logger.debug(f"Thinking: {thinking_text[:50]}...")
                    
                    # Message is complete
                    elif chunk_type == "message_stop":
                        logger.info(f"Message stopped with reason: {getattr(chunk, 'stop_reason', 'unknown')}")
            
            # Add assistant message to conversation history
            session.conversation_history.append({
                "role": "assistant",
                "content": content_blocks
            })
            
            # If no tool use detected, we're done
            if not tool_use_detected:
                tool_execution_needed = False
                continue
            
            # Execute the tool
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            tool_result = await execute_tool(tool_name, tool_input)
            
            # Call tool result callback if provided
            if tool_result_callback:
                tool_result_callback(tool_result)
            
            # Format the tool result
            formatted_result = format_tool_result(tool_result)
            
            # Add tool result to conversation history
            session.conversation_history.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": formatted_result
                }]
            })
            
            # Continue the conversation with the tool result
            logger.info("Continuing conversation with tool result")
            
        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Add error message for user
            if text_callback:
                text_callback(f"\nError: {str(e)}")
            tool_execution_needed = False

async def main():
    """Main entry point for CLI usage."""
    print("\nClaude Minimal Agent with Streaming\n")
    
    try:
        # Initialize the session
        session = await initialize_session()
        
        # Define callbacks for streaming output
        def text_callback(text):
            print(text, end="", flush=True)
        
        def thinking_callback(text):
            pass  # Ignore thinking output in CLI
        
        while True:
            # Get user input
            user_input = input("\n\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            # Process user input
            print("\nClaude: ", end="")
            await agent_loop(
                session=session,
                user_input=user_input,
                text_callback=text_callback,
                thinking_callback=thinking_callback
            )
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())