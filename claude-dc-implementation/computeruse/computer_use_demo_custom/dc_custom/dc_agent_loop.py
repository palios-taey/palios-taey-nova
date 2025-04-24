"""
Custom agent loop implementation with namespace isolation.
This module integrates the streaming API with our namespaced tool registry.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_agent_loop")

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    from dc_setup import dc_initialize
    from dc_executor import dc_execute_tool
    from registry.dc_registry import dc_get_tool_definitions
except ImportError:
    # When imported as a package
    from .dc_setup import dc_initialize
    from .dc_executor import dc_execute_tool
    from .registry.dc_registry import dc_get_tool_definitions

# Set up log directory
LOG_DIR = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True)

# Add file handler for agent logs
file_handler = logging.FileHandler(LOG_DIR / "dc_agent_loop.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Default system prompt with namespace-isolated tool names
DC_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. dc_computer - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter

2. dc_bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute

3. dc_str_replace_editor - For viewing, creating, and editing files
   * ALWAYS include the 'command' and 'path' parameters
   * Different commands need different additional parameters

Be precise and careful with tool parameters. Always include all required parameters for each tool.
When using tools, wait for their output before continuing.
"""

async def dc_agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: Optional[int] = 4000,
    use_real_adapters: bool = False,
    callbacks: Optional[Dict[str, Callable]] = None
):
    """
    Main agent loop for Claude with computer use capabilities, using namespace isolation.
    
    Args:
        user_input: The user's message
        conversation_history: The conversation history
        api_key: The Anthropic API key
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking (None to disable)
        use_real_adapters: Whether to use real adapters or mock implementations
        callbacks: Optional callbacks for UI integration
    """
    # Ensure the DC implementation is initialized
    dc_initialize(use_real_adapters=use_real_adapters)
    
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
    
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key provided and ANTHROPIC_API_KEY not set in environment")
    
    # Import Anthropic client
    try:
        from anthropic import AsyncAnthropic, APIError, APIStatusError, APIResponseValidationError
    except ImportError:
        logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
        raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")
    
    # Initialize the client
    client = AsyncAnthropic(api_key=api_key)
    
    # Add the user message to the conversation
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Get tool definitions from our registry
    tools = dc_get_tool_definitions()
    
    # Set up beta flags
    beta_flags = ["computer-use-2025-01-24"]  # Required for computer use tools
    if thinking_budget is not None:
        beta_flags.append("thinking-2023-05-24")  # Enable thinking
    
    # Create API parameters
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": conversation_history,
        "system": DC_SYSTEM_PROMPT,
        "tools": tools,
        "stream": True,
        "anthropic_beta": ",".join(beta_flags)
    }
    
    # Add thinking parameters if enabled
    if thinking_budget is not None:
        api_params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
    
    logger.info(f"Sending request to Claude API with model: {model}")
    
    try:
        # Make API call with streaming
        stream = await client.messages.create(**api_params)
        
        # Process the stream
        assistant_response = {"role": "assistant", "content": []}
        tool_use_detected = False
        current_tool_use = None
        
        async for chunk in stream:
            # Process content block start
            if hasattr(chunk, "type") and chunk.type == "content_block_start":
                block = chunk.content_block
                
                # Handle text blocks
                if block.type == "text":
                    text = block.text
                    on_text(text)
                    assistant_response["content"].append({
                        "type": "text",
                        "text": text
                    })
                
                # Handle tool use blocks
                elif block.type == "tool_use":
                    tool_use_detected = True
                    current_tool_use = {
                        "name": block.name,
                        "input": block.input,
                        "id": getattr(block, "id", "tool_1")
                    }
                    on_tool_use(current_tool_use["name"], current_tool_use["input"])
                    assistant_response["content"].append(block.model_dump())
            
            # Process content block delta
            elif hasattr(chunk, "type") and chunk.type == "content_block_delta":
                if hasattr(chunk.delta, "text") and chunk.delta.text:
                    text = chunk.delta.text
                    on_text(text)
                    if assistant_response["content"] and assistant_response["content"][-1]["type"] == "text":
                        assistant_response["content"][-1]["text"] += text
            
            # Process thinking blocks (if present)
            elif hasattr(chunk, "type") and chunk.type == "thinking":
                thinking_text = getattr(chunk, "thinking", "")
                if "on_thinking" in callbacks:
                    callbacks["on_thinking"](thinking_text)
                logger.info(f"Thinking: {thinking_text[:100]}...")
        
        # Add the assistant response to conversation history
        conversation_history.append(assistant_response)
        
        # Execute tool if needed
        if tool_use_detected and current_tool_use:
            logger.info(f"Executing tool: {current_tool_use['name']}")
            
            # Execute the tool using our namespace-isolated executor
            tool_result = await dc_execute_tool(
                tool_name=current_tool_use["name"],
                tool_input=current_tool_use["input"]
            )
            
            # Call tool result callback
            on_tool_result(current_tool_use["name"], current_tool_use["input"], tool_result)
            
            # Format the tool result
            tool_result_content = []
            if tool_result.error:
                tool_result_content = [{"type": "text", "text": tool_result.error}]
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
            return await dc_agent_loop(
                user_input="",  # No new user input
                conversation_history=conversation_history,
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                use_real_adapters=use_real_adapters,
                callbacks=callbacks
            )
        
        return conversation_history
    
    except (APIStatusError, APIResponseValidationError, APIError) as e:
        logger.error(f"API error: {str(e)}")
        error_msg = f"I encountered an API error: {str(e)}"
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
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        error_msg = f"I encountered an unexpected error: {str(e)}"
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

async def dc_main():
    """
    Main entry point for CLI usage.
    """
    print("\nClaude DC Custom Agent (Namespace Isolated)\n")
    print("Enter your message (or 'exit' to quit):")
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set in environment")
        api_key = input("Enter your Anthropic API key: ")
    
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
        try:
            conversation_history = await dc_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                api_key=api_key,
                use_real_adapters=True  # Try to use real adapters if available
            )
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(dc_main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")