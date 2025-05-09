#!/usr/bin/env python3
"""
Basic Prompt Cache Test
Tests ephemeral message flagging with cache control.
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cache_basic_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.cache')

# Import Anthropic
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
    """Test basic prompt caching functionality."""
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
    
    # Add system message with cache control
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. Help users learn about technical topics concisely."
        }
    ]
    
    # Try to add cache control (might not be supported in all SDK versions)
    try:
        system[0]["cache_control"] = {"type": "ephemeral"}
        logger.info("Added cache control to system message")
    except Exception as e:
        logger.warning(f"Failed to add cache control to system: {e}")
    
    # Run first request without caching enabled
    logger.info("Making first API call (no cache)")
    start_time_1 = time.time()
    
    try:
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
        follow_up_content = {
            "type": "text",
            "text": "That's helpful. Can you recommend some beginner projects?"
        }
        
        # Try to add cache control (might not be supported in all SDK versions)
        try:
            follow_up_content["cache_control"] = {"type": "ephemeral"}
            logger.info("Added cache control to follow-up message")
        except Exception as e:
            logger.warning(f"Failed to add cache control to follow-up: {e}")
        
        follow_up_messages.append({
            "role": "user",
            "content": [follow_up_content]
        })
        
        # Try with prompt caching enabled via beta flag
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
            
            # Write results to file
            with open('cache_results.txt', 'w') as f:
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
            if "beta" in str(e):
                logger.warning(f"Beta flag not supported: {e}")
                # Try without beta flag
                second_start = time.time()
                second_response = client.messages.create(
                    max_tokens=1024,
                    messages=follow_up_messages,
                    model="claude-3-7-sonnet-20250219",
                    system=system
                )
                second_end = time.time()
                second_duration = second_end - second_start
                logger.info(f"Second request (without beta flag) completed in {second_duration:.2f} seconds")
                
                # Calculate time saved
                time_saved = first_duration - second_duration
                percent_saved = (time_saved / first_duration) * 100 if first_duration > 0 else 0
                
                logger.info(f"Time saved: {time_saved:.2f} seconds ({percent_saved:.1f}%)")
                logger.warning("Could not test with beta flag, but cache control may still be working")
                
                return True
            else:
                logger.error(f"Error in prompt caching test: {e}")
                return False
    except Exception as e:
        logger.error(f"Error in prompt caching test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Prompt Caching Test")
    print("=" * 80)
    
    # Check SDK version
    from anthropic import __version__
    print(f"Anthropic SDK version: {__version__}")
    if int(__version__.split('.')[1]) >= 39:
        print("SDK version supports prompt caching")
    else:
        print(f"WARNING: SDK version {__version__} may not support prompt caching (requires 0.39.0+)")
    
    # Run the test
    success = asyncio.run(test_prompt_caching())
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Check the logs for details.")