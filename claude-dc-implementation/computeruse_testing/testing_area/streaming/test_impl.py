#!/usr/bin/env python3
"""
Test script for streaming implementation
Tests that streaming functionality works with tools
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
        logging.FileHandler('test_streaming_impl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.streaming_impl')

# Import our implementation
from streaming_impl import streaming_loop, get_bool_env, validate_tool_input

# Import required modules
try:
    sys.path.insert(0, '/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo')
    from tools import ToolResult
    from anthropic import Anthropic
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

async def test_streaming_with_tools():
    """Test the streaming implementation with tools."""
    logger.info("Starting streaming with tools test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Set up a prompt that will use tools
    prompt = "Please tell me the current date and time using the bash tool."
    
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
    
    # Set up streaming flag
    os.environ["ENABLE_STREAMING"] = "true"
    
    # Run the streaming loop
    updated_messages = await streaming_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="Use the bash tool to find information when appropriate.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,
        tool_version="computer_use_20250124"
    )
    
    logger.info("Test completed successfully")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Streaming Implementation Test")
    print("=" * 80)
    success = asyncio.run(test_streaming_with_tools())
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Check the logs for details.")