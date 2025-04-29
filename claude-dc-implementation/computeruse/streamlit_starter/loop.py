"""
Core implementation of Claude streaming with tool use.
This file provides the fundamental agent loop for Claude DC.
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, AsyncGenerator
from enum import StrEnum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("claude_agent")

# Add APIProvider for compatibility with existing code
class APIProvider(StrEnum):
    """Enum for different API providers"""
    ANTHROPIC = "anthropic" 
    BEDROCK = "bedrock"
    VERTEX = "vertex"

try:
    from anthropic import AsyncAnthropic, APIError, APIResponseValidationError, APIStatusError
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
    sys.exit(1)

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
    Sets cache breakpoints for recent turns.
    """
    if not messages:
        return messages
    
    # Create a deep copy to avoid modifying the original
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
    This is a placeholder implementation - in a real application, 
    you would import and call the actual tool functions.
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
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
    except ImportError:
        # Mock implementations for testing if tools are not available
        logger.warning(f"Tool module not found, using mock implementation for {tool_name}")
        
        if tool_name == "computer":
            if "action" not in tool_input:
                return ToolResult(error="Missing required 'action' parameter")
            
            action = tool_input.get("action")
            
            if action in ["move_mouse", "left_button_press"] and "coordinates" not in tool_input:
                return ToolResult(error=f"Missing required 'coordinates' parameter for {action}")
                
            if action == "type_text" and "text" not in tool_input:
                return ToolResult(error="Missing required 'text' parameter for type_text")
            
            # Mock implementation
            await asyncio.sleep(0.5)  # Simulate processing time
            return ToolResult(output=f"Executed {action} (mock implementation)")
            
        elif tool_name == "bash":
            if "command" not in tool_input:
                return ToolResult(error="Missing required 'command' parameter")
            
            command = tool_input.get("command", "")
            
            # Mock implementation
            await asyncio.sleep(0.5)  # Simulate processing time
            return ToolResult(output=f"Executed: {command} (mock implementation)")
            
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
    debug: bool = False
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
        debug: Whether to print debug information
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
    # CRITICAL: Thinking is NOT a beta flag, but a parameter in extra_body
    if thinking_budget:
        extra_body["thinking"] = {
            "type": "enabled",
            "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
        }
    
    # Set up system if provided
    system = None
    if system_prompt:
        system = system_prompt
    
    if debug:
        logger.info(f"Using model: {model}")
        logger.info(f"Beta flags: {betas}")
        logger.info(f"Extra parameters: {extra_body}")
    
    # Main conversation loop
    while True:
        try:
            # Call API with streaming
            # Set up API parameters
            api_params = {
                "model": model,
                "messages": messages,
                "system": system,
                "max_tokens": max_tokens,
                "tools": tools,
                "stream": True,
                **extra_body  # Unpack extra_body to include thinking configuration
            }
            
            # Add beta flags if available
            if betas:
                api_params["anthropic_beta"] = ",".join(betas)
            
            # Make the API call
            stream = await client.messages.create(**api_params)
            
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

async def run_with_user_input(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: int = 4000,
    enable_prompt_caching: bool = True,
    enable_extended_output: bool = True,
    callback_functions: Optional[Dict[str, Callable]] = None
):
    """
    Run the agent loop with a user input message.
    A simplified interface for the agent_loop function.
    
    Args:
        user_input: The user's message
        conversation_history: Existing conversation history
        model: Claude model to use
        max_tokens: Maximum tokens in response
        thinking_budget: Thinking token budget
        enable_prompt_caching: Whether to enable prompt caching
        enable_extended_output: Whether to enable extended output
        callback_functions: Optional callbacks for UI integration
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Initialize callbacks if not provided
    if callback_functions is None:
        callback_functions = {}
    
    # Default callbacks that print to console
    def default_on_output(event):
        if event.get("type") == "text_delta":
            print(event.get("text", ""), end="", flush=True)
        elif event.get("type") == "tool_use":
            print(f"\n[Using tool: {event.get('name')}]")
        elif event.get("type") == "tool_progress":
            print(f"\n[Tool progress: {event.get('message')}]")
        elif event.get("type") == "tool_result":
            print(f"\n[Tool result: {event.get('result')}]")
        elif event.get("type") == "message_stop":
            print("\n[Message complete]")
    
    # Get callbacks or use defaults
    on_output = callback_functions.get("on_output", default_on_output)
    on_tool_output = callback_functions.get("on_tool_output", lambda tool_input, tool_id: None)
    
    # Add the user message to the conversation
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Define available tools
    tools = [COMPUTER_TOOL, BASH_TOOL]
    
    # Run the agent loop
    try:
        updated_history = await agent_loop(
            model=model,
            messages=conversation_history,
            tools=tools,
            output_callback=on_output,
            tool_output_callback=on_tool_output,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
            debug=True
        )
        
        return updated_history
        
    except Exception as e:
        logger.error(f"Error in running agent: {e}")
        return conversation_history

async def main():
    """
    Simple CLI demo of the agent loop.
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
        conversation_history = await run_with_user_input(
            user_input=user_input,
            conversation_history=conversation_history
        )

# Add compatibility function for existing code
async def sampling_loop(
    *,
    system_prompt_suffix: str = "",
    model: str,
    provider: APIProvider = APIProvider.ANTHROPIC,
    messages: List[Dict[str, Any]],
    output_callback: Callable[[Any], None],
    tool_output_callback: Optional[Callable[[Any, str], None]] = None,
    api_response_callback: Optional[Callable[[Any, Optional[Any], Optional[Exception]], None]] = None,
    api_key: Optional[str] = None,
    only_n_most_recent_images: Optional[int] = None,
    tool_version: str = "computer_use_20250124",
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None,
    token_efficient_tools_beta: bool = False,
) -> List[Dict[str, Any]]:
    """
    Compatibility wrapper for the agent_loop function.
    This provides the same interface as the original sampling_loop function.
    """
    # Combine system prompts if needed
    custom_system = DEFAULT_SYSTEM_PROMPT
    if system_prompt_suffix:
        custom_system = f"{DEFAULT_SYSTEM_PROMPT}\n\n{system_prompt_suffix}"
        
    # Set up prompt caching and extended output flags
    enable_prompt_caching = True
    enable_extended_output = True
    
    # Call our agent_loop function with the provided parameters
    return await agent_loop(
        model=model,
        messages=messages,
        tools=[COMPUTER_TOOL, BASH_TOOL],
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        tool_version=tool_version,
        max_tokens=max_tokens,
        thinking_budget=thinking_budget,
        system_prompt=custom_system,
        enable_prompt_caching=enable_prompt_caching,
        enable_extended_output=enable_extended_output,
        token_efficient_tools=token_efficient_tools_beta,
        debug=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")