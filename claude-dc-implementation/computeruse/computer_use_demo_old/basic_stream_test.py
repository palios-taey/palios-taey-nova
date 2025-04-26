#!/usr/bin/env python3
"""
Basic streaming test for Claude API.
This script tests streaming with the Anthropic API, with no tools or complex features.
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
        logging.FileHandler("basic_stream_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("basic_stream_test")

# Beta flags constants
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
    "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
}

async def test_claude_streaming():
    """Test basic streaming with the Anthropic API."""
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
        
        # Prepare test messages - simple request with no tools
        messages = [
            {"role": "user", "content": "Write a short story about a robot named Claude who learns to code. Keep it very brief, just a few sentences."}
        ]
        
        # Set model to use
        model = "claude-3-7-sonnet-20250219"
        
        logger.info(f"Testing Claude streaming with model: {model}")
        
        # Create extra_headers with beta flag for computer use
        extra_headers = {
            "anthropic-beta": BETA_FLAGS["computer_use_20250124"]
        }
        
        # API parameters for streaming request
        api_params = {
            "model": model,
            "max_tokens": 4000,  # Must be greater than thinking.budget_tokens
            "messages": messages,
            "stream": True,
            "extra_headers": extra_headers,
            # No tools for this basic test
        }
        
        # Add thinking parameters - must be at least 1024 tokens
        # And max_tokens must be greater than thinking.budget_tokens
        thinking = {
            "type": "enabled",
            "budget_tokens": 1024  # Minimum required by API
        }
        api_params["thinking"] = thinking
        
        # Make the streaming request
        logger.info("Starting streaming request...")
        stream = await client.messages.create(**api_params)
        
        logger.info("Stream created successfully")
        
        # Process the stream
        print("\n--- Claude's Response ---\n")
        async for chunk in stream:
            if hasattr(chunk, "type"):
                # Log chunk type for debugging
                logger.debug(f"Received chunk type: {chunk.type}")
                
                # Process content block delta (text)
                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                    text = chunk.delta.text
                    print(text, end="", flush=True)
                    logger.debug(f"Text chunk: {text}")
                
                # Process thinking chunks
                elif chunk.type == "thinking_delta":
                    thinking_text = chunk.thinking
                    logger.debug(f"Thinking: {thinking_text[:50]}...")
                
                # Log message stop
                elif chunk.type == "message_stop":
                    logger.info(f"Message stopped with reason: {getattr(chunk, 'stop_reason', 'unknown')}")
        
        print("\n\n--- End of Response ---\n")
        logger.info("Streaming completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point."""
    print("Testing Claude API streaming...")
    
    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_claude_streaming())
    
    if success:
        print("\nAPI test completed successfully - check logs for details")
        return 0
    else:
        print("\nAPI test failed - check logs for errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())