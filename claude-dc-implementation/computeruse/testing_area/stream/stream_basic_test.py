#!/usr/bin/env python3
"""
Basic Streaming Test - Most Minimal Version
This script tests streaming without tools to verify core functionality.
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
        logging.FileHandler('basic_streaming_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.basic_streaming')

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

async def test_basic_streaming():
    """Test basic streaming without tools."""
    logger.info("Starting basic streaming test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Set up a simple prompt
    prompt = "Hello! Please write a short poem about streaming data."
    
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
    
    # Set up API params
    api_params = {
        "max_tokens": 1024,
        "messages": messages,
        "model": "claude-3-7-sonnet-20250219",
        "stream": True
    }
    
    # Add system message 
    api_params["system"] = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. Keep your responses short and to the point."
        }
    ]
    
    logger.info("Making API call with streaming enabled")
    try:
        # Make the API call with streaming
        with open('basic_streaming_output.txt', 'w') as f:
            f.write(f"PROMPT: {prompt}\n\nRESPONSE:\n")
            
            stream = client.messages.create(**api_params)
            logger.info("Stream created successfully")
            
            # Process the stream
            print("\nResponse:")
            for event in stream:
                if hasattr(event, "type"):
                    event_type = event.type
                    
                    if event_type == "content_block_start":
                        # New content block started
                        if hasattr(event.content_block, "type"):
                            if event.content_block.type == "text":
                                print(f"\n{event.content_block.text}", end="")
                                f.write(f"{event.content_block.text}")
                    
                    elif event_type == "content_block_delta":
                        # Handle deltas
                        if hasattr(event.delta, "text") and event.delta.text:
                            print(event.delta.text, end="", flush=True)
                            f.write(event.delta.text)
                    
                    elif event_type == "message_stop":
                        print("\n\nMessage complete")
                        f.write("\n\nMessage complete")
                        break
            
            logger.info("Basic streaming test completed successfully")
            
    except Exception as e:
        logger.error(f"Error in streaming test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Basic Streaming Test (No Tools)")
    print("=" * 80)
    success = asyncio.run(test_basic_streaming())
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Check the logs for details.")