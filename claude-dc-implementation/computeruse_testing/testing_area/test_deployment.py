#!/usr/bin/env python3
"""
A simple test script to validate the Claude DC streaming implementation.
Tests three scenarios:
1. A simple query that doesn't use tools
2. A basic tool operation (simple bash command)
3. A longer response to test streaming behavior
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
logger = logging.getLogger('claude_dc.test')

# Add the parent directory to sys.path
REPO_ROOT = Path("/home/computeruse/github/palios-taey-nova")
CLAUDE_DC_ROOT = REPO_ROOT / "claude-dc-implementation/computeruse"
sys.path.append(str(CLAUDE_DC_ROOT))

# Import required modules (with error handling)
try:
    from computer_use_demo.loop import sampling_loop, APIProvider
    from computer_use_demo.tools import ToolResult
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

# Mock callbacks for testing
def output_callback(content_block):
    """Handle output from the model."""
    if isinstance(content_block, dict):
        if content_block.get("type") == "text":
            text = content_block.get("text", "")
            is_delta = content_block.get("is_delta", False)
            if is_delta:
                print(text, end="")
            else:
                print(f"\nCLAUDE: {text}")
        elif content_block.get("type") == "tool_use":
            print(f"\nTOOL USE: {content_block.get('name')} with input: {content_block.get('input')}")
        elif content_block.get("type") == "thinking":
            print(f"\nTHINKING: {content_block.get('thinking')}")

def tool_output_callback(result, tool_id):
    """Handle output from tools."""
    if result.output:
        print(f"\nTOOL RESULT ({tool_id}): {result.output}")
    if result.error:
        print(f"\nTOOL ERROR ({tool_id}): {result.error}")

def api_response_callback(request, response, error):
    """Handle API responses and errors."""
    if error:
        logger.error(f"API ERROR: {error}")

async def run_test_1():
    """Test a simple query that doesn't use tools."""
    print("\n\n=== TEST 1: Simple Query ===")
    
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "What is the capital of France?"}]}
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return
    
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
            max_tokens=100,
            thinking_budget=None
        )
        print("\nTest 1 completed successfully")
    except Exception as e:
        logger.error(f"Error in Test 1: {e}")

async def run_test_2():
    """Test a basic tool operation (simple bash command)."""
    print("\n\n=== TEST 2: Basic Tool Operation ===")
    
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "Run 'ls -la' and tell me what you see."}]}
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return
    
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
            thinking_budget=None
        )
        print("\nTest 2 completed successfully")
    except Exception as e:
        logger.error(f"Error in Test 2: {e}")

async def run_test_3():
    """Test a longer response to test streaming behavior."""
    print("\n\n=== TEST 3: Streaming Longer Response ===")
    
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "Explain three key benefits of using Python for data science and how they compare to other programming languages. Please provide a detailed explanation."}]}
    ]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return
    
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
            max_tokens=500,
            thinking_budget=None
        )
        print("\nTest 3 completed successfully")
    except Exception as e:
        logger.error(f"Error in Test 3: {e}")

async def main():
    """Run all tests in sequence."""
    print("=== CLAUDE DC STREAMING IMPLEMENTATION TEST ===")
    print("Testing the streaming implementation with various scenarios.")
    
    await run_test_1()
    await run_test_2()
    await run_test_3()
    
    print("\n\n=== ALL TESTS COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main())