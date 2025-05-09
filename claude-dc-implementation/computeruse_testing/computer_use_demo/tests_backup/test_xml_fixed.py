#!/usr/bin/env python3
"""
Test script for the fixed XML function calls during streaming.

This script runs a simple test of the unified streaming loop
with XML function calls to verify the fix works.
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
logger = logging.getLogger("test_xml_fixed")

# Add the streaming directory to sys.path
streaming_dir = str(Path(__file__).parent)
sys.path.append(streaming_dir)

# Import the unified streaming agent loop
from streaming.unified_streaming_loop import unified_streaming_agent_loop

async def test_with_bash_command():
    """
    Test the fixed implementation with a simple bash command.
    
    This will force Claude DC to use a tool call, which will test
    the buffer pattern with XML function calls.
    """
    print("\n=== Testing XML Function Call Fix ===\n")
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        return
    
    # Set up a simple conversation with a command that requires a tool
    conversation = []
    user_input = "Run the command 'ls -la' to list files in the current directory"
    
    try:
        # This will force Claude DC to use a tool call
        print(f"User: {user_input}\n")
        print("Claude: ", end="", flush=True)
        
        # Call the unified streaming agent loop
        conversation = await unified_streaming_agent_loop(
            user_input=user_input,
            conversation_history=conversation,
            api_key=api_key,
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,  # Smaller limit for testing
            thinking_budget=None,  # Disable thinking as per the fix
            use_real_adapters=True  # Use real adapters
        )
        
        print("\n\nTest completed successfully!")
        
    except Exception as e:
        print(f"\n\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("\nTest failed!")

if __name__ == "__main__":
    asyncio.run(test_with_bash_command())