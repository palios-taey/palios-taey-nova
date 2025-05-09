#!/usr/bin/env python3
"""
Prompt Caching Test
Tests prompt caching implementation in isolation.
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prompt_cache_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.prompt_cache')

# Import required libraries
from anthropic import Anthropic

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

async def test_prompt_caching():
    """Test prompt caching functionality."""
    logger.info("Starting prompt caching test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Set up a series of messages for caching
    base_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello Claude! I want to explore machine learning. What are the basics I should know?"
                }
            ]
        }
    ]
    
    # Add system message
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. Help users learn about technical topics concisely."
        }
    ]
    
    # Add cache control to system
    system[0]["cache_control"] = {"type": "ephemeral"}
    
    # Run first request without caching
    logger.info("Making first API call (no cache)")
    start_time_1 = time.time()
    
    first_response = client.messages.create(
        max_tokens=1024,
        messages=base_messages,
        model="claude-3-7-sonnet-20250219",
        system=system
    )
    
    end_time_1 = time.time()
    first_duration = end_time_1 - start_time_1
    logger.info(f"First request completed in {first_duration:.2f} seconds")
    
    # Create follow-up message with cache breakpoint
    follow_up_messages = base_messages.copy()
    assistant_message = {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": first_response.content[0].text
            }
        ]
    }
    follow_up_messages.append(assistant_message)
    
    # Add follow-up user message with cache control
    follow_up_messages.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "That's helpful. Can you recommend some beginner projects?",
                "cache_control": {"type": "ephemeral"}
            }
        ]
    })
    
    # Try with prompt caching enabled
    logger.info("Making second API call (with cache)")
    
    # Add the prompt caching beta flag
    try:
        # Set the caching beta flag
        second_start = time.time()
        second_response = client.messages.create(
            max_tokens=1024,
            messages=follow_up_messages,
            model="claude-3-7-sonnet-20250219",
            system=system,
            beta=["prompt-caching-2024-07-31"]
        )
        second_end = time.time()
        second_duration = second_end - second_start
        logger.info(f"Second request (with caching) completed in {second_duration:.2f} seconds")
        
        # Calculate time saved
        time_saved = first_duration - second_duration
        percent_saved = (time_saved / first_duration) * 100 if first_duration > 0 else 0
        
        logger.info(f"Time saved with caching: {time_saved:.2f} seconds ({percent_saved:.1f}%)")
        
        # Check if there was a meaningful speedup
        if percent_saved > 10:
            logger.info("Prompt caching appears to be working correctly")
        else:
            logger.warning("Prompt caching may not be working as expected (insufficient speedup)")
        
        # Check response headers for caching information
        # Note: Direct header examination not supported in the Python SDK
        # This would be easier to verify with lower-level HTTP requests
        
        # Write results to file
        with open('prompt_cache_results.txt', 'w') as f:
            f.write(f"PROMPT CACHING TEST RESULTS\n")
            f.write(f"==========================\n\n")
            f.write(f"First request (no cache): {first_duration:.2f} seconds\n")
            f.write(f"Second request (with cache): {second_duration:.2f} seconds\n")
            f.write(f"Time saved: {time_saved:.2f} seconds ({percent_saved:.1f}%)\n\n")
            
            f.write(f"First response extract:\n")
            f.write(f"{first_response.content[0].text[:200]}...\n\n")
            
            f.write(f"Second response extract:\n")
            f.write(f"{second_response.content[0].text[:200]}...\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in prompt caching test: {e}")
        return False

def check_sdk_cache_support():
    """Check if the installed SDK supports prompt caching."""
    from anthropic import __version__
    logger.info(f"Anthropic SDK version: {__version__}")
    
    # Check if the SDK version is high enough for prompt caching
    major, minor, patch = __version__.split('.')
    if int(major) >= 0 and int(minor) >= 39:
        logger.info("SDK version supports prompt caching")
        return True
    else:
        logger.warning(f"SDK version {__version__} may not support prompt caching (requires 0.39.0+)")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Prompt Caching Test")
    print("=" * 80)
    
    # Check SDK support
    sdk_supported = check_sdk_cache_support()
    if not sdk_supported:
        print("WARNING: Your SDK version may not support prompt caching.")
        print("Consider upgrading with: pip install --upgrade anthropic>=0.39.0")
    
    # Run the test
    success = asyncio.run(test_prompt_caching())
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Check the logs for details.")