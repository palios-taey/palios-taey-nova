#!/usr/bin/env python3
"""
Direct streaming test without using production_ready_loop.py
"""

import os
import sys
import asyncio
from pathlib import Path
from anthropic import Anthropic

async def run_test():
    """Run a direct streaming test with the Anthropic API"""
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
        else:
            raise ValueError("API key not found")
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    print(f"Created Anthropic client (SDK version: {getattr(Anthropic, '__version__', 'unknown')})")
    
    # Create a simple message
    messages = [
        {
            "role": "user", 
            "content": "Tell me about the current date. Keep it short."
        }
    ]
    
    # Create system message
    system = "You are Claude, an AI assistant. Keep your responses short and to the point."
    
    # Call the API with streaming
    print("Making API call with streaming enabled...")
    stream = client.messages.create(
        max_tokens=1024,
        messages=messages,
        model="claude-3-7-sonnet-20250219",
        system=system,
        stream=True
    )
    
    # Process the stream
    print("\nResponse:")
    for event in stream:
        if hasattr(event, "type"):
            # Handle different event types
            if event.type == "content_block_start":
                # New content block started
                if hasattr(event, "content_block") and hasattr(event.content_block, "type"):
                    if event.content_block.type == "text":
                        print(f"\n[BLOCK START] {getattr(event.content_block, 'text', '')}", end="")
            
            elif event.type == "content_block_delta":
                # Handle deltas
                if hasattr(event, "delta") and hasattr(event.delta, "text"):
                    print(event.delta.text, end="", flush=True)
            
            elif event.type == "message_stop":
                print("\n\n[MESSAGE COMPLETE]")
                break
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    print("=" * 80)
    print("Direct Streaming Test")
    print("=" * 80)
    asyncio.run(run_test())