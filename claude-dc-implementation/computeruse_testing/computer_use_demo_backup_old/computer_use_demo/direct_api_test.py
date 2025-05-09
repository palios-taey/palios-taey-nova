"""
Direct test using the Anthropic API.
This bypasses our custom implementation to test the API directly.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("direct_api_test")

async def test_api_directly():
    """Test the Anthropic API directly without our custom implementation."""
    try:
        # Import the Anthropic SDK
        from anthropic import AsyncAnthropic
        
        # Load API key from secrets
        api_key = None
        secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
        if os.path.exists(secrets_path):
            with open(secrets_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets["api_keys"]["anthropic"]
        
        if not api_key:
            logger.error("API key not found")
            return
        
        logger.info("Creating Anthropic client")
        client = AsyncAnthropic(api_key=api_key)
        
        # Define system prompt
        system_prompt = """You are Claude, an AI assistant. Respond briefly."""
        
        # Define conversation history
        messages = [
            {"role": "user", "content": "Hello, what are three key features of streaming in an AI system?"}
        ]
        
        # Set API parameters
        logger.info("Setting up API parameters")
        api_params = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 1000,
            "messages": messages,
            "system": system_prompt,
            "stream": True
        }
        
        # Make API call with streaming
        logger.info("Making streaming API call")
        full_response = ""
        
        stream = await client.messages.create(**api_params)
        
        print("\nClaude: ", end="", flush=True)
        
        # Process the stream
        async for chunk in stream:
            if hasattr(chunk, "type") and chunk.type == "content_block_delta":
                text_delta = chunk.delta.text
                print(text_delta, end="", flush=True)
                full_response += text_delta
        
        print("\n\nStreaming completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in direct API test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_directly())