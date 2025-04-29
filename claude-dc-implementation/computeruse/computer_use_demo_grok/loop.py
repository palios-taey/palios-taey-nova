"""
Core implementation of Claude streaming with tool use.
This implements the agent loop for Claude DC with proper streaming support.
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, AsyncGenerator
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("claude_dc.log")
    ]
)
logger = logging.getLogger("claude_agent")

try:
    from anthropic import AsyncAnthropic, Anthropic
    from anthropic.__version__ import __version__ as anthropic_version
    logger.info(f"Using Anthropic SDK version: {anthropic_version}")
    if anthropic_version != "0.50.0":
        warnings.warn(f"Expected Anthropic SDK v0.50.0, but found v{anthropic_version}. This may cause issues.")
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic==0.50.0")
    sys.exit(1)

try:
    from pydantic import BaseModel
except ImportError:
    logger.error("Pydantic not installed. Install with: pip install pydantic")
    sys.exit(1)

# Beta flags from research
BETA_FLAGS = {
    "output_128k": "output-128k-2025-02-19",  # For extended output support
    "tools": "tools-2024-05-16",              # For tool use support
    "prompt_caching": "cache-control-2024-07-01"  # For prompt caching
}

# Tool definitions
COMPUTER_TOOL = {
    "type": "function",
    "function": {
        "name": "computer",
        "description": "Control the computer through mouse and keyboard actions or capture screenshots",
        "parameters": {
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
                "duration": {
                    "type": "number",
                    "description": "Duration in seconds (for wait action)"
                }
            },
            "required": ["action"]
        }
    }
}

BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute bash commands on the system",
        "parameters": {
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
}

EDIT_TOOL = {
    "type": "function",
    "function": {
        "name": "edit",
        "description": "Create, read, or modify files on the system",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "append"],
                    "description": "The action to perform on the file"
                },
                "path": {
                    "type": "string",
                    "description": "The path to the file"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file (for write/append actions)"
                }
            },
            "required": ["action", "path"]
        }
    }
}

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. computer - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter
   * For the wait action, you can optionally include 'duration' in seconds

2. bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute

3. edit - For working with files
   * ALWAYS include the 'action' parameter ('read', 'write', or 'append')
   * ALWAYS include the 'path' parameter with the file path
   * For 'write' and 'append' actions, ALWAYS include the 'content' parameter

IMPORTANT GUIDELINES:
- Be precise and careful with tool parameters. Always include all required parameters.
- When using tools, wait for their output before continuing.
- Don't use tools unless necessary for the task.
- If a task requires multiple steps, break it down and explain your approach.
- For file paths, use absolute paths starting with / when possible.
"""

class ToolResult:
    """Container for tool execution results"""
    def __init__(self, 
                 output: Optional[str] = None, 
                 error: Optional[str] = None, 
                 base64_image: Optional[str] = None):
        self.output = output
        self.error = error
        self.base64_image = base64_image
    
    def __str__(self):
        if self.error:
            return f"Error: {self.error}"
        return self.output or ""

def apply_cache_control(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply cache control to messages for prompt caching.
    Sets cache breakpoints for recent turns.
    """
    if not messages:
        return messages
    
    # Create a deep copy to avoid modifying the original
    processed_messages = json.loads(json.dumps(messages))
    
    breakpoints_remaining = 3
    for i, message in enumerate(reversed(processed_messages)):
        if message["role"] == "user" and breakpoints_remaining > 0:
            # Skip the most recent user message
            if i > 0:
                breakpoints_remaining -= 1
                content = message.get("content", "")
                
                # Handle different content formats
                if isinstance(content, list):
                    # List content format
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            block["cache_control"] = {"type": "ephemeral"}
                            break
                elif isinstance(content, str) and content:
                    # Convert string content to block format
                    message["content"] = [
                        {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                    ]
    
    return processed_messages

async def execute_tool(
    tool_name: str, 
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute a tool with the given input.
    Dynamically imports the appropriate tool implementation.
    """
    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
    
    try:
        # Import the tool implementations
        if tool_name == "computer":
            from tools.computer import execute_computer_tool
            return await execute_computer_tool(tool_input, progress_callback)
        elif tool_name == "bash":
            from tools.bash import execute_bash_tool
            return await execute_bash_tool(tool_input, progress_callback)
        elif tool_name == "edit":
            from tools.edit import execute_edit_tool
            return await execute_edit_tool(tool_input, progress_callback)
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
    except ImportError as e:
        logger.error(f"Tool module not found: {e}")
        return ToolResult(error=f"Tool module not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")

def format_tool_result(result: ToolResult) -> Union[List[Dict[str, Any]], str]:
    """
    Format a tool result for sending back to the API.
    """
    if result.error:
        return result.error
    
    content = []
    
    # Add text output if present
    if result.output:
        content.append({
            "type": "text",
            "text": result.output
        })
    
    # Add image if present
    if result.base64_image:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": result.base64_image
            }
        })
    
    return content

async def agent_loop(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Optional[Callable[[Dict[str, Any], str], None]] = None,
    api_response_callback: Optional[Callable[[Any, Optional[Any], Optional[Exception]], None]] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None,
    system_prompt: Optional[str] = None,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    debug: bool = False
):
    """
    Agent loop for Claude with streaming and tool use.
    
    Args:
        model: The Claude model to use
        messages: The conversation history
        output_callback: Function to call with each content block from Claude
        tool_output_callback: Function to call with tool results
        api_response_callback: Function to call with API response info
        api_key: Your Anthropic API key
        max_tokens: Maximum tokens in the response
        thinking_budget: Budget for thinking tokens
        system_prompt: Optional system prompt
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        debug: Whether to print debug information
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY not set in environment")
    
    # Configure beta flags in headers
    beta_headers = {}
    beta_flags = []
    
    # Always include tools flag
    beta_flags.append(BETA_FLAGS["tools"])
    
    # Add extended output flag if enabled
    if enable_extended_output:
        beta_flags.append(BETA_FLAGS["output_128k"])
    
    # Add prompt caching flag if enabled
    if enable_prompt_caching:
        beta_flags.append(BETA_FLAGS["prompt_caching"])
        # Apply cache control to messages
        messages = apply_cache_control(messages)
    
    # Set the beta flags in the headers
    if beta_flags:
        beta_headers["anthropic-beta"] = ",".join(beta_flags)
    
    # Create client with beta flags in headers
    client = AsyncAnthropic(
        api_key=api_key,
        default_headers=beta_headers
    )
    
    # Configure tools
    tools = [COMPUTER_TOOL, BASH_TOOL, EDIT_TOOL]
    
    # Configure thinking parameter
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "system": system_prompt or DEFAULT_SYSTEM_PROMPT,
        "tools": tools,
    }
    
    # Add thinking parameter (if provided)
    if thinking_budget:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
        }
    
    if debug:
        logger.info(f"Using model: {model}")
        logger.info(f"Beta flags: {beta_flags}")
        logger.info(f"Thinking budget: {thinking_budget if thinking_budget else 'Not enabled'}")
    
    # Main conversation loop
    while True:
        try:
            # Stream the message
            async with client.messages.stream(**params) as stream:
                tool_input_acc = ""
                tool_name = None
                tool_id = None
                
                # Process the stream
                async for event in stream:
                    # Debug event details
                    if debug:
                        logger.debug(f"Event: {event}")
                    
                    # Handle different event types
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, "type"):
                            # Check if this is a tool use block
                            if event.content_block.type == "tool_use":
                                tool_name = event.content_block.name
                                tool_id = event.content_block.id
                                # Reset tool input accumulator
                                tool_input_acc = ""
                                
                                # Notify about tool use
                                output_callback({
                                    "type": "tool_use_start",
                                    "name": tool_name,
                                    "id": tool_id
                                })
                            elif event.content_block.type == "text":
                                # Text content block starting
                                output_callback({
                                    "type": "content_start", 
                                    "content_type": "text"
                                })
                    
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "type"):
                            # Handle text deltas
                            if event.delta.type == "text_delta":
                                output_callback({
                                    "type": "text_delta",
                                    "text": event.delta.text
                                })
                            # Handle tool input deltas
                            elif event.delta.type == "input_json_delta" and event.delta.partial_json:
                                tool_input_acc += event.delta.partial_json
                                output_callback({
                                    "type": "tool_input_delta",
                                    "input_delta": event.delta.partial_json,
                                    "tool_id": tool_id,
                                    "tool_name": tool_name
                                })
                    
                    elif event.type == "content_block_stop":
                        # Content block completed
                        if tool_input_acc:
                            # We have a complete tool input
                            try:
                                # Parse the JSON
                                tool_input = json.loads(tool_input_acc)
                                
                                # Execute the tool
                                output_callback({
                                    "type": "tool_executing",
                                    "name": tool_name,
                                    "input": tool_input,
                                    "id": tool_id
                                })
                                
                                # Execute the tool
                                result = await execute_tool(
                                    tool_name,
                                    tool_input,
                                    progress_callback=lambda msg: output_callback({
                                        "type": "tool_progress",
                                        "message": msg,
                                        "tool_id": tool_id
                                    })
                                )
                                
                                # Format the result
                                formatted_result = format_tool_result(result)
                                
                                # Call tool output callback
                                if tool_output_callback:
                                    tool_output_callback(tool_input, tool_id)
                                
                                # Notify about tool result
                                output_callback({
                                    "type": "tool_result",
                                    "name": tool_name,
                                    "result": str(result),
                                    "tool_id": tool_id
                                })
                                
                                # Add tool result to messages
                                messages.append({
                                    "role": "user",
                                    "content": [{
                                        "type": "tool_result",
                                        "tool_call_id": tool_id,
                                        "content": formatted_result
                                    }]
                                })
                                
                                # Reset tool state
                                tool_input_acc = ""
                                tool_name = None
                                tool_id = None
                                
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON in tool input: {tool_input_acc}")
                                output_callback({
                                    "type": "error",
                                    "message": f"Invalid JSON in tool input: {tool_input_acc}"
                                })
                            except Exception as e:
                                logger.error(f"Error executing tool: {str(e)}")
                                output_callback({
                                    "type": "error",
                                    "message": f"Error executing tool: {str(e)}"
                                })
                    
                    elif event.type == "message_stop":
                        # Message complete
                        output_callback({"type": "message_stop"})
                
                # Get the final message for history
                final_message = await stream.get_final_message()
                
                # Add to conversation history
                messages.append({
                    "role": "assistant",
                    "content": final_message.content
                })
                
                # If we had no tools to execute, we're done
                if not tool_id:
                    return messages
                
        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            output_callback({
                "type": "error",
                "message": f"API Error: {str(e)}"
            })
            
            if api_response_callback:
                api_response_callback(None, None, e)
            
            return messages

async def chat_with_claude(
    query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 4096,
    thinking_budget: int = 1024,
    api_key: Optional[str] = None,
    output_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Simple function to chat with Claude with streaming and tool use.
    
    Args:
        query: The user query
        conversation_history: Existing conversation history
        model: The Claude model to use
        max_tokens: Maximum tokens in the response
        thinking_budget: Budget for thinking tokens
        api_key: Your Anthropic API key
        output_callback: Function to call with Claude's output
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        debug: Whether to print debug information
        
    Returns:
        Updated conversation history
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Add the user query to the conversation
    conversation_history.append({
        "role": "user",
        "content": query
    })
    
    # Set up output callback if not provided
    if output_callback is None:
        def default_output_callback(event):
            if event["type"] == "text_delta":
                print(event["text"], end="", flush=True)
            elif event["type"] == "tool_use_start":
                print(f"\n[Using tool: {event['name']}]")
            elif event["type"] == "tool_executing":
                print(f"\n[Executing {event['name']} with input: {event['input']}]")
            elif event["type"] == "tool_result":
                print(f"\n[Tool result: {event['result']}]")
            elif event["type"] == "error":
                print(f"\n[Error: {event['message']}]")
            elif event["type"] == "message_stop":
                print("\n[Message complete]")
        
        output_callback = default_output_callback
    
    # Run the agent loop
    try:
        updated_history = await agent_loop(
            model=model,
            messages=conversation_history,
            output_callback=output_callback,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            api_key=api_key,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
            debug=debug
        )
        
        return updated_history
        
    except Exception as e:
        logger.error(f"Error in chat_with_claude: {str(e)}")
        return conversation_history

async def main():
    """
    Simple CLI demo of the agent loop.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set the ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)
    
    print("\nClaude Computer Use Agent\n")
    print("Enter your message (or 'exit' to quit):")
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        print("\nClaude:", end="", flush=True)
        
        # Process user input
        conversation_history = await chat_with_claude(
            query=user_input,
            conversation_history=conversation_history,
            debug=False
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")