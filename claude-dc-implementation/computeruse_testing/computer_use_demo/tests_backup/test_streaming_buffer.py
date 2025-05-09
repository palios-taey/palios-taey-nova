#!/usr/bin/env python3
"""
Test script for the unified streaming loop with buffer for Claude DC.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_streaming_buffer")

# Add streaming directory to path
streaming_dir = str(Path(__file__).parent)
sys.path.append(streaming_dir)

# Import the unified streaming agent loop
from streaming.unified_streaming_loop import unified_streaming_agent_loop

async def test_buffer_with_streaming():
    """Test the buffer implementation with real streaming."""
    print("\n=== Testing Buffer Implementation with Streaming ===\n")
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        return
    
    # Use a prompt that requires a tool call
    user_input = "Run the command 'ls -la' to list files in the current directory"
    
    try:
        # Initialize conversation
        conversation = []
        
        # Print the user input
        print(f"User: {user_input}\n")
        print("Claude: ", end="", flush=True)
        
        # Call the unified streaming agent loop with the buffer
        conversation = await unified_streaming_agent_loop(
            user_input=user_input,
            conversation_history=conversation,
            api_key=api_key,
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            thinking_budget=None,  # Disable thinking as per the fix
            use_real_adapters=True  # Use real adapters
        )
        
        print("\n\nTest completed!")
        
    except Exception as e:
        print(f"\n\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("\nTest failed!")

if __name__ == "__main__":
    asyncio.run(test_buffer_with_streaming())