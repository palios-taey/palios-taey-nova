#!/usr/bin/env python3
"""
Direct test of the bash tool functionality using the loop module.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('claude_dc.test')

# Add necessary directories to sys.path
COMPUTER_USE_DEMO_DIR = Path("/home/computeruse/computer_use_demo")
sys.path.append(str(COMPUTER_USE_DEMO_DIR.parent))

# Import the tool collection directly
from computer_use_demo.tools import ToolCollection, ToolResult
from computer_use_demo.tools.bash import BashTool20250124

async def test_bash_directly():
    """Test the bash tool directly without going through the Claude API."""
    print("\n=================")
    print("DIRECT BASH TEST")
    print("=================")
    
    # Create a bash tool instance
    bash_tool = BashTool20250124()
    
    # Define a command to run
    command = "ls -la"
    
    # Create a callback for streaming output
    def stream_callback(output):
        print(f"Streaming output: {output}")
    
    # Set the stream callback if supported
    if hasattr(bash_tool, 'set_stream_callback'):
        bash_tool.set_stream_callback(stream_callback)
    
    # Execute the command
    print(f"Executing command: {command}")
    result = await bash_tool(command=command)
    
    # Print the result
    print("\nRESULT:")
    if result.output:
        print(f"OUTPUT:\n{result.output}")
    if result.error:
        print(f"ERROR:\n{result.error}")
    
    print("\nTest completed!")

async def main():
    """Run the direct bash test."""
    await test_bash_directly()

if __name__ == "__main__":
    asyncio.run(main())