#!/usr/bin/env python3
"""
Non-interactive test script for the streaming implementation.

This script demonstrates the streaming functionality without requiring user input.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from feature_toggles import get_feature_toggles, get_feature_setting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("non_interactive_test")

# Load API key from secrets file
def load_api_key():
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    try:
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            return secrets["api_keys"]["anthropic"]
    except Exception as e:
        logger.error(f"Error loading API key: {str(e)}")
        return None

async def test_non_interactive_streaming():
    """Run a non-interactive test of the streaming API."""
    
    # Try to import the Anthropic SDK
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        print("Error: Please install the Anthropic SDK: pip install anthropic")
        return
    
    # Set up API key
    api_key = load_api_key()
    if not api_key:
        print("Error: API key is required.")
        return
    
    # Get model from feature toggles
    model = get_feature_setting("api_model", "claude-3-7-sonnet-20250219")
    
    print("\n===== Non-Interactive Streaming Test =====")
    print("This test will demonstrate basic streaming functionality.")
    
    # Pre-defined test messages
    test_messages = [
        "Tell me about the Python programming language.",
        "What are some best practices for error handling in Python?",
        "Explain the concept of asynchronous programming."
    ]
    
    for i, user_input in enumerate(test_messages):
        print(f"\nTest {i+1}: {user_input}")
        print("\nClaude: ", end="", flush=True)
        
        # Initialize the Anthropic client
        client = AsyncAnthropic(api_key=api_key)
        
        # Set up a simple message with streaming
        try:
            # Use the correct API for streaming
            stream = await client.messages.create(
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": user_input}
                ],
                model=model,
                stream=True,
            )
            
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
        
        # Add a separator between tests
        print("\n" + "-" * 80)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(test_non_interactive_streaming())