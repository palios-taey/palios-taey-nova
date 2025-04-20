#!/usr/bin/env python3
"""
Test script for minimal streaming with tool use.
This script runs a simple test to verify that streaming responses with tool use work.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Set up basic logging for the test script itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
script_logger = logging.getLogger('test_script')

# Determine the correct paths based on environment
script_logger.info("Setting up Python paths for the environment")

if os.path.exists("/home/computeruse"):
    # We're in the container
    script_logger.info("Running in container environment")
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    script_logger.info("Running in host environment")
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

# Add all possible paths to Python path
paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir),
    str(claude_dc_root / "computeruse/current_experiment"),
    str(claude_dc_root / "computeruse/current_experiment/implementation")
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        script_logger.info(f"Added path: {path}")

# Try to identify the computer_use_demo directory structure
if os.path.exists(computer_use_demo_dir):
    script_logger.info(f"computer_use_demo directory exists at: {computer_use_demo_dir}")
    tools_dir = computer_use_demo_dir / "tools"
    if os.path.exists(tools_dir):
        script_logger.info(f"Tools directory exists at: {tools_dir}")
        script_logger.info(f"Contents: {os.listdir(tools_dir)}")
    else:
        script_logger.warning(f"Tools directory not found at: {tools_dir}")
else:
    script_logger.warning(f"computer_use_demo directory not found at: {computer_use_demo_dir}")
    # Try to find the directory by searching
    script_logger.info("Searching for computer_use_demo directory...")
    computeruse_dir = claude_dc_root / "computeruse"
    if os.path.exists(computeruse_dir):
        script_logger.info(f"computeruse directory exists, contents: {os.listdir(computeruse_dir)}")
        
# Set PYTHONPATH environment variable for child processes
os.environ["PYTHONPATH"] = os.pathsep.join(paths_to_add)

# Import our implementation module
from implementation import (
    logger, TEST_PROMPT, run_streaming_test, get_api_key,
    log_response, log_tool_result
)

def print_response(content):
    """Print response content with appropriate formatting."""
    if isinstance(content, dict):
        if content.get("type") == "text":
            text = content.get("text", "")
            is_delta = content.get("is_delta", False)
            
            if is_delta:
                # For delta text, just print without newline
                print(text, end="", flush=True)
            else:
                # For full text blocks, print with newline
                print(f"\n{text}")
        
        elif content.get("type") == "thinking":
            thinking = content.get("thinking", "")
            is_delta = content.get("is_delta", False)
            
            if is_delta:
                # For thinking deltas, just print progress
                print(".", end="", flush=True)
            else:
                # For full thinking blocks
                print(f"\n[Thinking: {thinking[:50]}...]")
        
        elif content.get("type") == "tool_use":
            name = content.get("name", "unknown")
            print(f"\n[Using tool: {name}]")
    else:
        # Fallback for non-dict content
        print(f"\n{content}")

def print_tool_result(result, tool_id):
    """Print tool execution results."""
    if hasattr(result, "output") and result.output:
        print(f"\n[Tool Result {tool_id}]: {result.output}")
    
    if hasattr(result, "error") and result.error:
        print(f"\n[Tool Error {tool_id}]: {result.error}")
    
    if hasattr(result, "base64_image") and result.base64_image:
        print(f"\n[Tool produced an image]")

async def main():
    """Run the streaming test."""
    print("=" * 80)
    print("Minimal Streaming with Tool Use Test")
    print("=" * 80)
    
    try:
        # Get API key
        api_key = get_api_key()
        
        # Set up test message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": TEST_PROMPT
                    }
                ]
            }
        ]
        
        print(f"\nSending prompt: {TEST_PROMPT}")
        print("\nResponse:")
        
        # Run the test with our callback functions
        await run_streaming_test(
            messages=messages,
            api_key=api_key,
            output_callback=print_response,
            tool_callback=print_tool_result
        )
        
        print("\n\nTest completed successfully!")
        print(f"See logs for details: {os.path.abspath('./logs/streaming_test.log')}")
    
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Test failed: {e}")
        
        # Show where to find logs
        print(f"\nCheck the logs for more details: {os.path.abspath('./logs/streaming_test.log')}")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)