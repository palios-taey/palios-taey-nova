"""
Agent loop for Claude Computer Use implementation with streaming, tool use, and thinking capabilities.
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union

try:
    from anthropic import AsyncAnthropic, APIError, APIResponseValidationError, APIStatusError
except ImportError:
    print("Anthropic SDK not installed. Install with: pip install anthropic")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("claude_agent")

# Beta flags for different tool versions
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
    "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
}

# Prompt caching flag
PROMPT_CACHING_FLAG = "cache-control-2024-07-01"

# Extended output flag
EXTENDED_OUTPUT_FLAG = "output-128k-2025-02-19"

# Token-efficient tools flag
TOKEN_EFFICIENT_TOOLS_FLAG = "token-efficient-tools-2025-02-19"

# Tool definitions
COMPUTER_TOOL = {
    "name": "computer",
    "description": "Control a computer by taking actions like mouse clicks, keyboard input, and screenshots",
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

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. computer - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter

2. bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute

Be precise and careful with tool parameters. Always include all required parameters for each tool.
When using tools, wait for their output before continuing.
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
    Sets cache breakpoints for the 3 most recent turns.
    """
    if not messages:
        return messages
    
    # Make a deep copy of messages to avoid modifying the original
    processed_messages = json.loads(json.dumps(messages))
    
    breakpoints_remaining = 3
    for i, message in enumerate(reversed(processed_messages)):
        if message["role"] == "user" and breakpoints_remaining > 0:
            content = message.get("content", "")
            
            # Skip the most recent user message
            if i > 0:
                breakpoints_remaining -= 1
                
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
    
    In a real implementation, this would call the actual tool execution logic.
    For testing, this provides mock responses.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
    """
    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
    
    if progress_callback:
        progress_callback(f"Executing {tool_name}...")
    
    try:
        # Validate required parameters
        if tool_name == "computer":
            if "action" not in tool_input:
                return ToolResult(error="Missing required 'action' parameter")
            
            action = tool_input.get("action")
            
            # Validate parameters based on action
            if action in ["move_mouse", "left_button_press"] and "coordinates" not in tool_input:
                return ToolResult(error=f"Missing required 'coordinates' parameter for {action}")
                
            if action == "type_text" and "text" not in tool_input:
                return ToolResult(error="Missing required 'text' parameter for type_text")
            
            # In a real implementation, we would execute the computer action
            # For testing, we return mock results
            if action == "screenshot":
                if progress_callback:
                    progress_callback("Taking screenshot...")
                    await asyncio.sleep(0.5)  # Simulate processing time
                
                return ToolResult(
                    output="Screenshot captured",
                    # In a real implementation, this would be the base64-encoded image
                    base64_image=None
                )
            
            elif action == "move_mouse":
                coordinates = tool_input.get("coordinates", [0, 0])
                
                if progress_callback:
                    progress_callback(f"Moving mouse to {coordinates}...")
                    await asyncio.sleep(0.2)
                
                return ToolResult(output=f"Mouse moved to {coordinates}")
            
            elif action == "type_text":
                text = tool_input.get("text", "")
                
                if progress_callback:
                    progress_callback(f"Typing text: {text[:10]}...")
                    await asyncio.sleep(0.3)
                
                return ToolResult(output=f"Typed text: {text}")
            
            # Handle other actions similarly...
            return ToolResult(output=f"Executed {action} (mock implementation)")
            
        elif tool_name == "bash":
            if "command" not in tool_input:
                return ToolResult(error="Missing required 'command' parameter")
            
            command = tool_input.get("command", "")
            
            if progress_callback:
                progress_callback(f"Executing command: {command}")
                await asyncio.sleep(0.5)
            
            # In a real implementation, we would execute the command
            # For testing, we return mock results
            if command == "ls":
                return ToolResult(output="file1.txt\nfile2.txt\ndirectory1/")
            elif command == "pwd":
                return ToolResult(output="/home/user")
            elif command.startswith("echo"):
                return ToolResult(output=command[5:])  # Return what comes after "echo "
            
            return ToolResult(output=f"Executed: {command} (mock implementation)")
        
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
            
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
    tools: List[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Optional[Callable[[Dict[str, Any], str], None]] = None,
    api_response_callback: Optional[Callable[[Any, Optional[Any], Optional[Exception]], None]] = None,
    api_key: Optional[str] = None,
    tool_version: str = "computer_use_20250124",
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None,
    system_prompt: Optional[str] = None,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    token_efficient_tools: bool = False,
):
    """
    Agent loop for Claude Computer Use implementation.
    
    Args:
        model: The Claude model to use
        messages: The conversation history
        tools: The tool definitions
        output_callback: Function to call with each content block from Claude
        tool_output_callback: Function to call with tool results
        api_response_callback: Function to call with API response info
        api_key: Your Anthropic API key
        tool_version: The tool version to use (determines beta flag)
        max_tokens: Maximum tokens in the response
        thinking_budget: Budget for thinking tokens
        system_prompt: Optional system prompt
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        token_efficient_tools: Whether to enable token-efficient tools beta flag
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY not set in environment")
    
    # Create client
    client = AsyncAnthropic(api_key=api_key)
    
    # Set up beta flags
    betas = []
    
    # Add tool version beta flag if applicable
    if tool_version in BETA_FLAGS:
        betas.append(BETA_FLAGS[tool_version])
    
    # Add token efficient tools beta flag if requested
    if token_efficient_tools:
        betas.append(TOKEN_EFFICIENT_TOOLS_FLAG)
    
    # Add prompt caching beta flag if enabled
    if enable_prompt_caching:
        betas.append(PROMPT_CACHING_FLAG)
        # Apply cache control to messages
        messages = apply_cache_control(messages)
    
    # Add extended output beta flag if enabled
    if enable_extended_output:
        betas.append(EXTENDED_OUTPUT_FLAG)
    
    # Set up extra body parameters
    extra_body = {}
    
    # Configure thinking for Claude 3.7 Sonnet
    # Note: Thinking is NOT a beta flag, but a parameter in extra_body
    if thinking_budget:
        extra_body["thinking"] = {
            "type": "enabled",
            "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
        }
    
    # Set up system if provided
    system = None
    if system_prompt:
        system = system_prompt
    
    logger.info(f"Using model: {model}")
    logger.info(f"Beta flags: {betas}")
    logger.info(f"Extra parameters: {extra_body}")
    
    # Main conversation loop
    while True:
        try:
            # Call API with streaming
            stream = await client.messages.create(
                model=model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                tools=tools,
                stream=True,
                anthropic_beta=",".join(betas) if betas else None,
                **extra_body  # Unpack extra_body to include thinking configuration
            )
            
            # Process streaming response
            content_blocks = []
            tool_use_blocks = []
            
            async for chunk in stream:
                # Process chunk based on type
                if hasattr(chunk, "type"):
                    if chunk.type == "content_block_start":
                        # New content block starting
                        if chunk.content_block.type == "tool_use":
                            # Save tool use blocks to execute later
                            tool_use_blocks.append(chunk.content_block)
                            # Pass tool use info to callback
                            output_callback({
                                "type": "tool_use",
                                "name": chunk.content_block.name,
                                "input": chunk.content_block.input,
                                "id": chunk.content_block.id
                            })
                        else:
                            # Pass other content blocks to callback
                            output_callback({
                                "type": "content_block",
                                "content": chunk.content_block
                            })
                            content_blocks.append(chunk.content_block)
                    
                    elif chunk.type == "content_block_delta":
                        # Content block update
                        if hasattr(chunk.delta, "text") and chunk.delta.text:
                            # Text update - pass to callback
                            output_callback({
                                "type": "text_delta",
                                "text": chunk.delta.text
                            })
                    
                    elif chunk.type == "message_stop":
                        # Message complete
                        output_callback({"type": "message_stop"})
                        break
            
            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": content_blocks + tool_use_blocks
            })
            
            # If no tool use blocks, we're done
            if not tool_use_blocks:
                return messages
            
            # Process tool use blocks
            tool_results = []
            for tool_block in tool_use_blocks:
                # Execute tool and get result
                result = await execute_tool(
                    tool_block.name,
                    tool_block.input,
                    progress_callback=lambda msg: output_callback({
                        "type": "tool_progress",
                        "message": msg,
                        "tool_id": tool_block.id
                    })
                )
                
                # Format result for API
                formatted_result = format_tool_result(result)
                
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": formatted_result,
                    "is_error": bool(result.error)
                }
                
                tool_results.append(tool_result)
                
                # Call tool output callback
                if tool_output_callback:
                    tool_output_callback(tool_block.input, tool_block.id)
                
                # Also pass to regular output callback
                output_callback({
                    "type": "tool_result",
                    "name": tool_block.name,
                    "result": str(result),
                    "tool_id": tool_block.id
                })
            
            # Add tool results to history
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
        except (APIStatusError, APIResponseValidationError) as e:
            # Handle API errors
            if api_response_callback:
                api_response_callback(e.request, e.response, e)
            
            logger.error(f"API Error: {e}")
            
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response text: {e.response.text}")
            
            # Pass error to output callback
            output_callback({
                "type": "error",
                "message": f"API Error: {e}"
            })
            
            return messages
            
        except APIError as e:
            # Handle other API errors
            if api_response_callback:
                api_response_callback(getattr(e, "request", None), 
                                    getattr(e, "response", None), e)
            
            logger.error(f"API Error: {e}")
            
            # Pass error to output callback
            output_callback({
                "type": "error",
                "message": f"API Error: {e}"
            })
            
            return messages
        
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {e}")
            
            # Pass error to output callback
            output_callback({
                "type": "error",
                "message": f"Unexpected error: {e}"
            })
            
            return messages

async def cli_agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: int = 4000,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
):
    """
    Run the agent loop in CLI mode.
    
    Args:
        user_input: User message
        conversation_history: Existing conversation history
        model: Claude model to use
        max_tokens: Maximum tokens in response
        thinking_budget: Thinking token budget
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Define callbacks
    def handle_output(data):
        if data.get("type") == "content_block":
            content = data.get("content")
            if hasattr(content, "type") and content.type == "text":
                print(content.text, end="", flush=True)
        elif data.get("type") == "text_delta":
            print(data.get("text", ""), end="", flush=True)
        elif data.get("type") == "tool_use":
            print(f"\n[Using tool: {data.get('name')}]")
        elif data.get("type") == "tool_progress":
            print(f"\n[Tool progress: {data.get('message')}]")
        elif data.get("type") == "tool_result":
            print(f"\n[Tool result: {data.get('result')}]")
        elif data.get("type") == "error":
            print(f"\nError: {data.get('message')}")
        elif data.get("type") == "message_stop":
            print("\n[Message complete]")
    
    def handle_tool_output(tool_input, tool_id):
        print(f"\n[Tool output for {tool_id}]")
    
    # Run agent loop
    try:
        tools = [COMPUTER_TOOL, BASH_TOOL]
        
        updated_history = await agent_loop(
            model=model,
            messages=conversation_history,
            tools=tools,
            output_callback=handle_output,
            tool_output_callback=handle_tool_output,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
        )
        
        return updated_history
        
    except Exception as e:
        print(f"\nError in CLI agent loop: {e}")
        return conversation_history

async def main():
    """
    Main entry point for CLI mode.
    """
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
        conversation_history = await cli_agent_loop(
            user_input=user_input,
            conversation_history=conversation_history,
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")