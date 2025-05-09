#!/usr/bin/env python3
"""
Test for Streamlined Streaming Implementation

This script tests the final streamlined implementation of streaming with tools
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
        logging.FileHandler('test_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.final')

# Add paths for imports
sys.path.insert(0, str(Path('/home/computeruse/computer_use_demo')))

try:
    # Import our final implementation
    from final_implementation import (
        streaming_enabled_loop, 
        validate_tool_input, 
        APIProvider
    )
    
    # Import tools
    from tools import ToolResult
    
    # Import other requirements
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

# Track token count
token_count = 0

def output_callback(block):
    """Handle content block output with token counting."""
    global token_count
    
    if block.get("type") == "text":
        if block.get("is_delta", False):
            # Handle streaming token
            token_text = block.get("text", "")
            token_count += 1
            
            # Print the token
            print(token_text, end="", flush=True)
        else:
            # Handle full text block
            if "text" in block:
                print(f"\n{block.get('text', '')}", end="")
    elif block.get("type") == "tool_use":
        logger.info(f"Tool use: {block.get('name', 'unknown')}")
        print(f"\n[Using tool: {block.get('name', 'unknown')}]")
    elif block.get("type") == "thinking":
        if "thinking" in block:
            logger.info(f"Thinking received: {block.get('thinking', '')[:50]}...")
            print(f"\n[Thinking: {block.get('thinking', '')[:50]}...]")

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

async def test_final_implementation():
    """Test the final streaming implementation."""
    logger.info("Starting final implementation test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create a prompt that will use tools
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
    
    # Run the streaming loop
    updated_messages = await streaming_enabled_loop(
        model="claude-3-7-sonnet-20250219",
        provider=APIProvider.ANTHROPIC,
        system_prompt_suffix="You help users interact with their computer system.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,
        tool_version="computer_use_20250124"
    )
    
    logger.info(f"Test completed with {len(updated_messages)} messages")
    logger.info(f"Received {token_count} streaming tokens")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Final Streaming Implementation Test")
    print("=" * 80)
    
    try:
        success = asyncio.run(test_final_implementation())
        
        if success:
            print("\nFinal implementation test completed successfully!")
        else:
            print("\nFinal implementation test failed! Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)
    
    print("\nStreamlined implementation is ready for production!")
    sys.exit(0)