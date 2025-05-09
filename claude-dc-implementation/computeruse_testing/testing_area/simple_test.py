#!/usr/bin/env python3
"""
Simple test for the streaming implementation.
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
    handlers=[logging.FileHandler("test_log.log")]
)
logger = logging.getLogger('claude_dc.test')

# Add the parent directory to sys.path
REPO_ROOT = Path("/home/computeruse/github/palios-taey-nova")
CLAUDE_DC_ROOT = REPO_ROOT / "claude-dc-implementation/computeruse"
sys.path.append(str(CLAUDE_DC_ROOT))

# Import required modules
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
            print(f"\nTOOL USE: {content_block.get('name')} with input: {content_block.get('input')}")

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
    """Run a simple test."""
    print("\n=====================")
    print("CLAUDE DC SIMPLE TEST")
    print("=====================")
    
    # Simple message to test streaming
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "What is the capital of France? Give me a brief answer."}]}
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    print("\nSending request to Claude API...")
    try:
        result = await sampling_loop(
            model="claude-3-7-sonnet-20250219",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="Keep answers brief and direct.",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key,
            max_tokens=100
        )
        print("\n\nTest completed successfully!")
    except Exception as e:
        print(f"\nERROR in test: {e}")

if __name__ == "__main__":
    asyncio.run(main())