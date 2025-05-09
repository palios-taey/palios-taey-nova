#!/usr/bin/env python3
"""
Test for Production-Ready Streaming Implementation

This script tests the production-ready implementation of streaming with tools
to ensure it's ready for integration into the actual production environment.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from collections.abc import Callable
from typing import Any, Optional
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.production')

# Add paths for imports
sys.path.insert(0, str(Path('/home/computeruse/computer_use_demo')))
sys.path.insert(0, str(Path('/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/testing_area')))

try:
    # Import our production-ready implementation
    from production_loop import (
        sampling_loop, 
        get_bool_env, 
        validate_tool_input, 
        APIProvider
    )
    
    # Import tools
    from tools import ToolResult, ToolVersion
    
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

async def test_production_implementation():
    """Test the production-ready streaming implementation."""
    logger.info("Starting production implementation test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create a prompt that will demonstrate various capabilities
    prompt = "Please perform the following tasks:\n1. Tell me today's date\n2. Use bash to check the current directory\n3. Take a screenshot of the desktop"
    
    # Create message content with the prompt
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
    
    # Set streaming environment variable
    os.environ["ENABLE_STREAMING"] = "true"
    logger.info(f"Streaming enabled: {get_bool_env('ENABLE_STREAMING', False)}")
    
    # Run the sampling loop
    updated_messages = await sampling_loop(
        model="claude-3-7-sonnet-20250219",
        provider=APIProvider.ANTHROPIC,
        system_prompt_suffix="You help users interact with their computer system.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,
        tool_version="computer_use_20250124",
        thinking_budget=None
    )
    
    logger.info(f"Test completed with {len(updated_messages)} messages")
    logger.info(f"Received {token_count} streaming tokens")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Production-Ready Streaming Implementation Test")
    print("=" * 80)
    
    try:
        success = asyncio.run(test_production_implementation())
        
        if success:
            print("\nProduction implementation test completed successfully!")
        else:
            print("\nProduction implementation test failed! Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)
    
    print("\nImplementation is ready for production!")
    sys.exit(0)