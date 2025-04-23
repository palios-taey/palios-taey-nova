#!/usr/bin/env python3
"""
Test script for streaming loop implementation
Tests streaming functionality with tool usage
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_streaming_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.streaming_loop')

# Import our streaming implementation
from streaming_loop import streaming_loop, validate_tool_input

# Import Anthropic
try:
    from anthropic import Anthropic
    from computer_use_demo.tools import ToolResult
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def get_api_key():
    """Get Anthropic API key from environment or file."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            logger.info("Found API key in ~/.anthropic/api_key")
        else:
            raise ValueError("API key not found")
    return api_key

def output_callback(block):
    """Handle content block output."""
    if block.get("type") == "text":
        if block.get("is_delta", False):
            print(block.get("text", ""), end="", flush=True)
        else:
            print(f"\n{block.get('text', '')}", end="")
    elif block.get("type") == "tool_use":
        logger.info(f"Tool use: {block.get('name')}")
        print(f"\n[Using tool: {block.get('name')}]")
    elif block.get("type") == "thinking":
        logger.info(f"Thinking: {block.get('thinking')[:50]}...")
        print(f"\n[Thinking: {block.get('thinking')[:50]}...]")

def tool_output_callback(result, tool_id):
    """Handle tool output."""
    if result.error:
        logger.error(f"Tool error (ID: {tool_id}): {result.error}")
        print(f"\n[Tool Error]: {result.error}")
    else:
        logger.info(f"Tool output received (ID: {tool_id})")
        if result.output:
            print(f"\n[Tool Output]: {result.output[:100]}{'...' if len(result.output) > 100 else ''}")
        
        if result.base64_image:
            logger.info(f"Tool returned an image (ID: {tool_id})")
            print(f"[Tool returned an image]")

def api_response_callback(request, response, error):
    """Handle API response."""
    if error:
        logger.error(f"API error: {error}")
    elif response:
        logger.info(f"API response received")

async def test_streaming_loop():
    """Test the streaming loop implementation."""
    logger.info("Starting streaming loop test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Set up a prompt that will use tools
    prompt = "Please tell me the current date and time using the bash tool, and then take a screenshot."
    
    # Create messages
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    # Run the streaming loop
    updated_messages = await streaming_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="Use tools appropriately to help the user.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,
        tool_version="computer_use_20250124"
    )
    
    logger.info(f"Test completed with {len(updated_messages)} messages")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Streaming Loop Test")
    print("=" * 80)
    
    try:
        success = asyncio.run(test_streaming_loop())
        
        if success:
            print("\nTest completed successfully!")
        else:
            print("\nTest failed! Check the logs for details.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)
    
    sys.exit(0)