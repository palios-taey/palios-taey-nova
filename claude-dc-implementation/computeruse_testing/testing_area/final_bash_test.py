#!/usr/bin/env python3
"""
Final test for the bash tool implementation with the updated system prompt.
This directly tests the deployed version with enhanced tool usage instructions.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("final_bash_test.log")]
)
logger = logging.getLogger('claude_dc.test')

# Import from the production deployment
sys.path.append('/home/computeruse')
from computer_use_demo.loop import sampling_loop, APIProvider
from computer_use_demo.tools import ToolResult

# Mock callbacks for testing
def output_callback(content_block):
    """Handle output from the model."""
    if isinstance(content_block, dict):
        if content_block.get("type") == "text":
            text = content_block.get("text", "")
            is_delta = content_block.get("is_delta", False)
            if is_delta:
                print(text, end="", flush=True)
            else:
                print(f"\nASSISTANT: {text}")
        elif content_block.get("type") == "tool_use":
            name = content_block.get("name", "unknown")
            tool_input = content_block.get("input", {})
            print(f"\nTOOL USE: {name} with input: {tool_input}")

def tool_output_callback(result, tool_id):
    """Handle output from tools."""
    if result.output:
        print(f"\nTOOL RESULT: {result.output}")
    if result.error:
        print(f"\nTOOL ERROR: {result.error}")

def api_response_callback(request, response, error):
    """Handle API responses and errors."""
    if error:
        print(f"\nAPI ERROR: {error}")

async def main():
    """Run a final test to verify bash tool usage with updated system prompt."""
    print("\n============================")
    print("FINAL BASH TOOL USAGE TEST")
    print("============================")
    
    # Direct message asking to run ls -la command with the command parameter
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "Please run the 'ls -la' command using the bash tool. Remember to use the command parameter."}
        ]}
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    print("\nSending request to Claude API with updated system prompt...")
    try:
        result = await sampling_loop(
            model="claude-3-7-sonnet-20250219",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key,
            max_tokens=300,
            tool_version="computer_use_20250124"  # Specify the tool version
        )
        print("\n\nTest completed successfully!")
    except Exception as e:
        print(f"\nERROR in test: {e}")

if __name__ == "__main__":
    asyncio.run(main())