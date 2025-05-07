#!/usr/bin/env python3
"""
Direct test script for the fixed bash tool implementation.

This script provides a way to test just the bash tool directly,
without going through the full Claude API or conversation loop.
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_bash_direct.log")
    ]
)
logger = logging.getLogger("test_bash_direct")

async def test_bash_tool():
    """Test the fixed bash tool implementation directly."""
    print("\nTesting Bash Tool Implementation\n")
    
    # Import the fixed bash tool implementation
    try:
        from streaming.tools.dc_bash_fixed import (
            dc_execute_bash_tool_streaming,
            dc_process_streaming_output,
            dc_execute_bash_tool
        )
        logger.info("Fixed bash tool implementation loaded successfully")
    except Exception as e:
        logger.error(f"Error loading fixed bash tool implementation: {str(e)}")
        print(f"Error: {str(e)}")
        return
    
    # Define test commands
    test_commands = [
        "ls -la",
        "echo 'Testing streaming output' && sleep 1 && echo 'with delays'",
        "ps aux | grep python | head -5",
        "find . -name '*.py' | sort | head -10"
    ]
    
    # Define which test to run
    test_index = 0
    if len(sys.argv) > 1:
        try:
            test_index = int(sys.argv[1]) - 1
            if test_index < 0 or test_index >= len(test_commands):
                print(f"Invalid test index. Choose between 1 and {len(test_commands)}.")
                test_index = 0
        except ValueError:
            print("Invalid argument. Using default test command.")
    
    # Get the command to test
    command = test_commands[test_index]
    print(f"Testing command: {command}\n")
    
    # Define progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
        
    try:
        # Test the streaming implementation
        print("\n--- Streaming implementation ---\n")
        output_chunks = []
        async for chunk in dc_execute_bash_tool_streaming(
            {"command": command},
            progress_callback=progress_callback
        ):
            # Display the chunk
            print(chunk, end="", flush=True)
            # Collect the chunk for processing
            output_chunks.append(chunk)
            
        # Process the collected chunks
        print("\n\n--- Processing collected output ---\n")
        result = await dc_process_streaming_output(output_chunks)
        
        if result.error:
            print(f"Error: {result.error}")
        else:
            print(f"Success! Output length: {len(result.output)} characters")
            
        # Test the non-streaming implementation for comparison
        print("\n--- Non-streaming implementation ---\n")
        non_streaming_result = await dc_execute_bash_tool({"command": command})
        
        if non_streaming_result.error:
            print(f"Error (non-streaming): {non_streaming_result.error}")
        else:
            print(f"Success (non-streaming)! Output length: {len(non_streaming_result.output)} characters")
            
            # Compare the outputs
            streaming_output = result.output if result.output else ""
            non_streaming_output = non_streaming_result.output if non_streaming_result.output else ""
            
            if streaming_output == non_streaming_output:
                print("\n✅ Outputs match between streaming and non-streaming implementations")
            else:
                print("\n❌ Outputs differ between streaming and non-streaming implementations")
                print(f"Streaming length: {len(streaming_output)}, Non-streaming length: {len(non_streaming_output)}")
    
    except Exception as e:
        logger.error(f"Error testing bash tool: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\nError: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_bash_tool())