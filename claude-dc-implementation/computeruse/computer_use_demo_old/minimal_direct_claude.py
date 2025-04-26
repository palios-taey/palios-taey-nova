#!/usr/bin/env python3
"""
Minimal direct script to test Claude API parameters.
This script provides a basic test of the Anthropic API with the correct parameters.
"""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("claude_api_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("claude_api_test")

async def test_claude_api():
    """Test the Anthropic API with different parameter configurations."""
    try:
        # Import the Anthropic client
        from anthropic import AsyncAnthropic
        
        # Get API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("No API key found. Please set the ANTHROPIC_API_KEY environment variable.")
            return False
        
        # Initialize client
        client = AsyncAnthropic(api_key=api_key)
        
        # Prepare test messages
        messages = [
            {"role": "user", "content": "Hello, please respond with a short greeting."}
        ]
        
        # Test 1: Basic message without tools or thinking
        logger.info("=== Test 1: Basic message ===")
        response = await client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=100,
            messages=messages,
            system="You are Claude, an AI assistant."
        )
        logger.info(f"Success! Model responded: {response.content[0].text[:100]}")
        
        # Test 2: With thinking parameter
        logger.info("=== Test 2: With thinking parameter ===")
        try:
            response = await client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=100,
                messages=messages,
                system="You are Claude, an AI assistant.",
                thinking={"type": "enabled", "budget_tokens": 1024}
            )
            logger.info(f"Success with thinking parameter! Response: {response.content[0].text[:100]}")
        except Exception as e:
            logger.error(f"Error with thinking parameter: {e}")
        
        # Test 3: With computer use tools beta flag
        logger.info("=== Test 3: With computer use tools beta flag ===")
        try:
            # Define a simple tool
            tools = [{
                "name": "get_current_time",
                "description": "Get the current time",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }]
            
            # Test with betas parameter
            response = await client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=100,
                messages=messages,
                system="You are Claude, an AI assistant.",
                tools=tools,
                betas=["computer-use-2025-01-24"]
            )
            logger.info(f"Success with betas parameter! Response: {response.content[0].text[:100]}")
        except Exception as e:
            logger.error(f"Error with betas parameter: {e}")
            
            # Try alternate approach with anthropic_beta
            try:
                response = await client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=100,
                    messages=messages,
                    system="You are Claude, an AI assistant.",
                    tools=tools,
                    stream=False,
                    extra_headers={"anthropic-beta": "computer-use-2025-01-24"}
                )
                logger.info(f"Success with extra_headers! Response: {response.content[0].text[:100]}")
            except Exception as e:
                logger.error(f"Error with extra_headers approach: {e}")
                
                # Try yet another approach with anthropic_beta parameter
                try:
                    response = await client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=100,
                        messages=messages,
                        system="You are Claude, an AI assistant.",
                        tools=tools,
                        stream=False,
                        anthropic_beta="computer-use-2025-01-24"
                    )
                    logger.info(f"Success with anthropic_beta parameter! Response: {response.content[0].text[:100]}")
                except Exception as e:
                    logger.error(f"Error with anthropic_beta parameter: {e}")
        
        # Test 4: With streaming
        logger.info("=== Test 4: With streaming ===")
        try:
            stream = await client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=100,
                messages=messages,
                system="You are Claude, an AI assistant.",
                stream=True
            )
            
            logger.info("Stream created successfully")
            async for chunk in stream:
                if hasattr(chunk, "type"):
                    logger.debug(f"Received chunk type: {chunk.type}")
                    
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                        logger.info(f"Text chunk: {chunk.delta.text}")
                    
                    if chunk.type == "message_stop":
                        logger.info(f"Message stopped with reason: {getattr(chunk, 'stop_reason', 'unknown')}")
            
            logger.info("Streaming completed successfully")
        except Exception as e:
            logger.error(f"Error with streaming: {e}")
        
        logger.info("All tests completed!")
        return True
    
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point."""
    print("Testing Claude API parameters...")
    
    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_claude_api())
    
    if success:
        print("API test completed - check logs for details")
        return 0
    else:
        print("API test failed - check logs for errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())