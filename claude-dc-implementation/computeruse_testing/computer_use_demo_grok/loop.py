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
from enum import Enum

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

# APIProvider class for compatibility with existing code
class APIProvider(str, Enum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

try:
    from anthropic import AsyncAnthropic, Anthropic
    # Fix: Import version directly since anthropic.__version__ structure changed
    import anthropic
    anthropic_version = anthropic.__version__
    logger.info(f"Using Anthropic SDK version: {anthropic_version}")
    if anthropic_version != "0.50.0":
        warnings.warn(f"Expected Anthropic SDK v0.50.0, but found v{anthropic_version}. This may cause issues.")
        logger.error(f"VERSION MISMATCH: Expected Anthropic SDK v0.50.0, found v{anthropic_version}")
        logger.error("To fix this issue, run: ./update_anthropic_sdk.sh")
        print(f"\n\033[1;31mWARNING: Expected Anthropic SDK v0.50.0, found v{anthropic_version}\033[0m")
        print("\033[1;31mThis version mismatch will cause API compatibility issues!\033[0m")
        print("\033[1;32mTo fix, run: ./update_anthropic_sdk.sh\033[0m\n")
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic==0.50.0")
    print("\n\033[1;31mERROR: Anthropic SDK not installed\033[0m")
    print("\033[1;32mTo install, run: pip install anthropic==0.50.0\033[0m\n")
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

# Tool definitions - Updated to use current format expected by API
COMPUTER_TOOL = {
    "type": "computer_use_20250124",
    "description": "Control the computer",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["click", "type", "pressKey", "moveMouse", "screenshot"],
                "description": "The action to perform"
            },
            "x": {
                "type": "number",
                "description": "x coordinate (for click or moveMouse)"
            },
            "y": {
                "type": "number",
                "description": "y coordinate (for click or moveMouse)"
            },
            "text": {
                "type": "string",
                "description": "Text to type (for type action)"
            },
            "key": {
                "type": "string",
                "description": "Key to press (for pressKey action)"
            }
        },
        "required": ["action"]
    }
}

BASH_TOOL = {
    "type": "bash_20250124",
    "description": "Execute a bash command",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            },
            "timeout": {
                "type": "number",
                "description": "Command timeout in seconds (default: 30)"
            }
        },
        "required": ["command"]
    }
}

EDIT_TOOL = {
    "type": "text_editor_20250124",
    "description": "Edit files on the system",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "append", "delete"],
                "description": "The action to perform"
            },
            "path": {
                "type": "string",
                "description": "File path to operate on"
            },
            "content": {
                "type": "string", 
                "description": "Content to write (for write/append actions)"
            }
        },
        "required": ["action", "path"]
    }
}

# List of available tools
AVAILABLE_TOOLS = [COMPUTER_TOOL, BASH_TOOL, EDIT_TOOL]

async def agent_loop(
    client: Optional[AsyncAnthropic] = None,
    messages: List[Dict[str, Any]] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 4096,
    temperature: float = 0.7,
    thinking: Optional[Dict[str, Any]] = None,
    stream_handler: Optional[Callable] = None,
    tools: List[Dict[str, Any]] = AVAILABLE_TOOLS,
    save_conversation: bool = True,
    conversation_path: str = "conversation_history.json"
) -> Dict[str, Any]:
    """
    Main agent loop for Claude DC with proper streaming support.
    
    Args:
        client: AsyncAnthropic client instance (will create one if not provided)
        messages: List of message objects for conversation history
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Model temperature (0.0-1.0)
        thinking: Thinking parameter configuration
        stream_handler: Callback for streaming events
        tools: List of tool definitions to expose to Claude
        save_conversation: Whether to save the conversation history
        conversation_path: Path to save conversation history
        
    Returns:
        Complete response from Claude after processing
    """
    if not messages:
        messages = [{"role": "user", "content": "Hello, Claude!"}]
    
    if not client:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Create client with beta flags in header (IMPORTANT: this is the correct way)
        beta_flags = f"{BETA_FLAGS['tools']},{BETA_FLAGS['output_128k']}"
        client = AsyncAnthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": beta_flags}
        )
    
    # Prepare request parameters
    params = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "tools": tools,
        "stream": True
    }
    
    # Add thinking parameter if specified (as a request parameter, not beta flag)
    if thinking:
        params["thinking"] = thinking
    
    # Initialize streaming state
    current_content_block = None
    partial_json = ""
    tool_use_index = None
    completed_response = {
        "content": [],
        "tool_use": [],
        "thinking": None
    }
    
    try:
        # Start streaming
        logger.info(f"Starting streaming request to {model}")
        stream = await client.messages.create(**params)
        
        async for event in stream:
            # Process each streaming event type
            if stream_handler:
                await stream_handler(event)
                
            if event.type == "message_start":
                logger.info("Message started")
                
            elif event.type == "content_block_start":
                logger.info(f"Content block started: {event.content_block.type}")
                current_content_block = {
                    "type": event.content_block.type,
                    "text": "" if event.content_block.type == "text" else None,
                    "tool_use": None
                }
                
                if event.content_block.type == "tool_use":
                    current_content_block["tool_use"] = {
                        "name": None,
                        "input": {}
                    }
                    tool_use_index = len(completed_response["content"])
                
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta" and current_content_block:
                    current_content_block["text"] += event.delta.text
                    
                elif event.delta.type == "input_json_delta" and current_content_block:
                    partial_json += event.delta.partial_json
                    
            elif event.type == "content_block_stop":
                logger.info(f"Content block stopped")
                
                # Handle tool use JSON
                if current_content_block and current_content_block["type"] == "tool_use" and partial_json:
                    try:
                        # Parse the accumulated JSON
                        tool_input = json.loads(partial_json)
                        current_content_block["tool_use"] = tool_input
                        
                        # Get tool name or type for display
                        tool_identifier = tool_input.get("type", tool_input.get("name", "unknown-tool"))
                        logger.info(f"Executing tool {tool_identifier}")
                        
                        # Execute the tool
                        tool_result = await execute_tool(tool_input)
                        logger.info(f"Tool execution completed: {tool_identifier}")
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "assistant",
                            "content": [{"type": "tool_use", "tool_use": tool_input}]
                        })
                        
                        messages.append({
                            "role": "user",
                            "content": [{"type": "tool_result", "tool_result": {"tool_use_id": None, "content": tool_result}}]
                        })
                        
                        # Store in completed response
                        completed_response["tool_use"].append({
                            "input": tool_input,
                            "output": tool_result
                        })
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing tool input JSON: {e}")
                        logger.error(f"Partial JSON: {partial_json}")
                    
                    # Reset partial JSON
                    partial_json = ""
                
                # Add the completed block to response
                if current_content_block:
                    completed_response["content"].append(current_content_block)
                current_content_block = None
                
            elif event.type == "message_delta":
                if event.delta.thinking:
                    logger.info("Received thinking content")
                    completed_response["thinking"] = event.delta.thinking
                    
            elif event.type == "message_stop":
                logger.info("Message completed")
                
    except Exception as e:
        logger.error(f"Error in streaming: {e}")
        raise
        
    # Save conversation if requested
    if save_conversation:
        try:
            with open(conversation_path, "w") as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    return completed_response

async def execute_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the specified tool based on the input.
    
    Args:
        tool_input: Tool input specification
        
    Returns:
        Tool execution result
    """
    try:
        # Import tool implementations
        from tools import execute_bash_tool, execute_computer_tool, execute_edit_tool
        
        # Handle different tool types based on the updated format
        tool_type = tool_input.get("type", "")
        
        if tool_type == "bash_20250124":
            return await execute_bash_tool(tool_input)
        elif tool_type == "computer_use_20250124":
            return await execute_computer_tool(tool_input)
        elif tool_type == "text_editor_20250124":
            return await execute_edit_tool(tool_input)
        else:
            # Fallback to check name for backwards compatibility
            tool_name = tool_input.get("name")
            
            if tool_name == "bash":
                return await execute_bash_tool(tool_input)
            elif tool_name == "computer":
                return await execute_computer_tool(tool_input)
            elif tool_name == "edit":
                return await execute_edit_tool(tool_input)
            else:
                return {"error": f"Unknown tool type: {tool_type} or name: {tool_name}"}
    except ImportError:
        logger.error("Tool implementation modules not found")
        return {"error": "Tool implementation not available"}
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        return {"error": f"Tool execution failed: {str(e)}"}

async def chat_with_claude(
    user_input: str,
    conversation_history: List[Dict[str, Any]] = None,
    model: str = "claude-3-7-sonnet-20250219",
    thinking_enabled: bool = True,
    thinking_budget: int = 1024
) -> Dict[str, Any]:
    """
    Simple function to chat with Claude with thinking enabled.
    
    Args:
        user_input: User's message
        conversation_history: Previous conversation history
        model: Claude model to use
        thinking_enabled: Whether to enable thinking
        thinking_budget: Token budget for thinking
        
    Returns:
        Claude's response with full content and thinking
    """
    if not conversation_history:
        conversation_history = []
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Set up thinking parameter if enabled
    thinking = None
    if thinking_enabled:
        thinking = {"type": "enabled", "budget_tokens": thinking_budget}
    
    # Create async client 
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = AsyncAnthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": f"{BETA_FLAGS['tools']},{BETA_FLAGS['output_128k']}"}
    )
    
    # Call agent loop
    response = await agent_loop(
        client=client,
        messages=conversation_history,
        model=model,
        thinking=thinking
    )
    
    # Get text content from response
    text_content = ""
    for block in response["content"]:
        if block["type"] == "text" and block["text"]:
            text_content += block["text"]
    
    # Add assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": text_content
    })
    
    return response

# Added for backwards compatibility with streamlit.py
async def sampling_loop(
    system_prompt_suffix: str = "",
    model: str = "claude-3-7-sonnet-20250219",
    provider: str = "anthropic",
    messages: List[Dict[str, Any]] = None,
    output_callback: Optional[Callable] = None,
    tool_output_callback: Optional[Callable] = None,
    api_response_callback: Optional[Callable] = None,
    api_key: str = None,
    only_n_most_recent_images: int = 0,
    tool_version: str = "computer_use_20250124",
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None,
    token_efficient_tools_beta: bool = False,
) -> List[Dict[str, Any]]:
    """
    Compatibility function for older streamlit.py integrations.
    Implements the sampling loop with Claude for streaming responses.
    
    Args:
        Various parameters for configuration and callbacks
        
    Returns:
        Updated messages list
    """
    # Create API client
    client = AsyncAnthropic(
        api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        default_headers={"anthropic-beta": f"{BETA_FLAGS['tools']},{BETA_FLAGS['output_128k']}"}
    )
    
    # Set up thinking parameter if enabled
    thinking = None
    if thinking_budget is not None:
        thinking = {"type": "enabled", "budget_tokens": thinking_budget}
    
    # Call agent loop with appropriate callbacks
    try:
        response = await agent_loop(
            client=client,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            thinking=thinking,
            tools=AVAILABLE_TOOLS
        )
        
        # Get text content from response
        text_content = ""
        for block in response["content"]:
            if block["type"] == "text" and block["text"]:
                text_content += block["text"]
        
        # Add assistant response to history
        messages.append({
            "role": "assistant",
            "content": text_content
        })
        
        return messages
    except Exception as e:
        logger.error(f"Error in sampling loop: {e}")
        if api_response_callback:
            api_response_callback(None, None, e)
        raise
    
if __name__ == "__main__":
    # Simple test of the agent loop
    import nest_asyncio
    nest_asyncio.apply()
    
    async def test_agent():
        response = await chat_with_claude("Tell me about the Claude DC system")
        print("\nResponse:", response)
        
        text_content = ""
        for block in response["content"]:
            if block["type"] == "text":
                text_content += block["text"]
        
        print("\nText content:", text_content)
        
        if response["thinking"]:
            print("\nThinking:", response["thinking"])
    
    asyncio.run(test_agent())