#!/usr/bin/env python3
"""
Minimal test script for the streaming implementation.

This script provides a simple way to test the basic streaming functionality
without relying on the existing code structure.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("minimal_test")

async def test_minimal_streaming(api_key=None, model="claude-3-sonnet-20240229"):
    """Run a minimal test of the streaming API."""
    
    # Try to import the Anthropic SDK
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        print("Error: Please install the Anthropic SDK: pip install anthropic")
        return
    
    # Set up API key
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: API key is required. Please provide it or set ANTHROPIC_API_KEY.")
        return
    
    print("\n===== Minimal Streaming Test =====")
    print("This test will demonstrate basic streaming functionality.")
    print("Enter your message below, or 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        print("\nClaude: ", end="", flush=True)
        
        # Initialize the Anthropic client
        client = AsyncAnthropic(api_key=api_key)
        
        # Set up a simple message with stream=True
        try:
            with client.messages.stream(
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": user_input}
                ],
                model=model,
                stream=True,
            ) as stream:
                async for event in stream:
                    if hasattr(event, "type"):
                        event_type = event.type
                        
                        if event_type == "content_block_start":
                            # A new content block is starting
                            pass
                        
                        elif event_type == "content_block_delta":
                            # New content to display
                            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                                print(event.delta.text, end="", flush=True)
                        
                        elif event_type == "message_stop":
                            # Message generation complete
                            print()  # Add a newline at the end
                            break
                    
                    else:
                        # Handle unexpected event structure
                        logger.warning(f"Unexpected event format: {event}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.exception("Error in streaming")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test minimal streaming functionality")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--model", default="claude-3-sonnet-20240229", help="Model to use")
    
    args = parser.parse_args()
    
    asyncio.run(test_minimal_streaming(
        api_key=args.api_key,
        model=args.model
    ))