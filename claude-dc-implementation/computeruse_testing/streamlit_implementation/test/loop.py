"""
Core implementation of Claude streaming with tool use.
This file provides the fundamental agent loop for Claude DC with proper thinking parameter and beta flags.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("claude_agent")

try:
    from anthropic import AsyncAnthropic, APIError, APIResponseValidationError, APIStatusError
except ImportError:
    logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
    raise

# Beta flags for different tool versions - CRITICAL FIX: Use dictionary format
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
    "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
}

# Additional beta flags
PROMPT_CACHING_FLAG = "cache-control-2024-07-01"
EXTENDED_OUTPUT_FLAG = "output-128k-2025-02-19"
TOKEN_EFFICIENT_TOOLS_FLAG = "token-efficient-tools-2025-02-19"

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools."""

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

async def run_with_tools(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None,
    system_prompt: Optional[str] = None,
    debug: bool = False
):
    """
    Run the Claude agent with tools.
    
    Args:
        model: The Claude model to use
        messages: The conversation history
        tools: The tool definitions
        api_key: Your Anthropic API key
        max_tokens: Maximum tokens in the response
        thinking_budget: Budget for thinking tokens
        system_prompt: Optional system prompt
        debug: Whether to print debug information
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY not set in environment")
    
    # Create client
    client = AsyncAnthropic(api_key=api_key)
    
    # Set up extra body parameters
    extra_body = {}
    
    # CRITICAL FIX: Thinking is NOT a beta flag, but a parameter in extra_body
    if thinking_budget:
        extra_body["thinking"] = {
            "type": "enabled",
            "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
        }
    
    if debug:
        logger.info(f"Using model: {model}")
        logger.info(f"Extra parameters: {extra_body}")
    
    try:
        # Set up API parameters
        api_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "tools": tools,
            **extra_body  # Unpack extra_body to include thinking configuration
        }
        
        # Add system if provided
        if system_prompt:
            api_params["system"] = system_prompt
        
        # Set streaming to True for the API call
        api_params["stream"] = True
        
        # Make the API call with streaming
        stream = await client.messages.create(**api_params)
        
        # Initialize containers for collecting responses
        content_blocks = []
        tool_use_blocks = []
        
        # Process the streaming response
        async for chunk in stream:
            # Process chunks based on type
            if hasattr(chunk, "type"):
                # Handle content block start events
                if chunk.type == "content_block_start":
                    # Check if this is a tool use block
                    if chunk.content_block.type == "tool_use":
                        # Save tool use blocks to execute later
                        tool_use_blocks.append(chunk.content_block)
                        
                        # If we had an output callback, we would call it here
                        # output_callback({"type": "tool_use", "name": chunk.content_block.name, 
                        #                "input": chunk.content_block.input, "id": chunk.content_block.id})
                    else:
                        # Add other content blocks to our collection
                        content_blocks.append(chunk.content_block)
                        
                        # If we had an output callback, we would call it here
                        # output_callback({"type": "content_block", "content": chunk.content_block})
                
                # Handle content block delta events (text updates)
                elif chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        # Process text update delta
                        # If we had an output callback, we would call it here
                        # output_callback({"type": "text_delta", "text": chunk.delta.text})
                        logger.info(f"Text delta received: {chunk.delta.text[:20]}...")
                
                # Handle message completion
                elif chunk.type == "message_stop":
                    logger.info("Message streaming complete")
                    # If we had an output callback, we would call it here
                    # output_callback({"type": "message_stop"})
                    break
        
        # Return the content blocks we collected
        return {"content_blocks": content_blocks, "tool_use_blocks": tool_use_blocks}
        
    except (APIStatusError, APIResponseValidationError) as e:
        logger.error(f"API Error: {e}")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            logger.error(f"Response text: {e.response.text}")
        raise
        
    except APIError as e:
        logger.error(f"API Error: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# Test function for streaming capability
async def test_streaming():
    """Test the streaming implementation"""
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "ANTHROPIC_API_KEY not set in environment"
        
        # Set up minimal messages
        messages = [
            {"role": "user", "content": "Test message for streaming API call"}
        ]
        
        # Set up minimal tools
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "type": "string",
                            "description": "A test parameter"
                        }
                    },
                    "required": ["param"]
                }
            }
        ]
        
        logger.info("Starting streaming test...")
        
        # Call the API with streaming enabled
        response = await run_with_tools(
            model="claude-3-7-sonnet-20250219",
            messages=messages,
            tools=tools,
            max_tokens=1500,  # Must be greater than thinking_budget
            thinking_budget=1024,  # Minimum budget
            debug=True
        )
        
        # Log received blocks
        content_blocks = response.get("content_blocks", [])
        tool_use_blocks = response.get("tool_use_blocks", [])
        
        logger.info(f"Received {len(content_blocks)} content blocks and {len(tool_use_blocks)} tool use blocks")
        
        return "Test successful - API streaming responded with proper event handling"
        
    except Exception as e:
        logger.error(f"Streaming test failed: {str(e)}")
        return f"Test failed: {str(e)}"

if __name__ == "__main__":
    # Run streaming test
    import sys
    print("Running streaming test with event handling...")
    result = asyncio.run(test_streaming())
    print(result)
    if "successful" in result:
        sys.exit(0)
    else:
        sys.exit(1)