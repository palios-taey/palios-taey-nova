#!/usr/bin/env python3
"""
Run the direct implementation version of Claude DC with streaming.

This script launches the direct implementation version which uses no imports
and has all functionality directly embedded for maximum stability during development.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import the direct implementation version
from streaming.unified_streaming_loop_direct import unified_streaming_agent_loop

async def main():
    """Run the direct implementation of Claude DC with streaming"""
    print("\nClaude DC Direct Implementation (No Imports)\n")
    print("This version uses a direct implementation approach with no imports for maximum stability.")
    print("All function call buffer logic, XML prompting, and parameter validation is embedded in the main file.")
    print("\nType your message below, or 'exit' to quit.\n")
    
    # Initialize conversation
    conversation_history = []
    
    # Main interaction loop
    while True:
        # Get user input
        user_input = input("> ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        try:
            # Process with unified streaming
            conversation_history = await unified_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                thinking_budget=2000  # Enable thinking for better planning
            )
            print()  # Add blank line after response
        except Exception as e:
            print(f"Error: {str(e)}")
            
if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())