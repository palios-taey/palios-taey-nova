#!/usr/bin/env python3
"""
Test script for fixed_production_ready_loop.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Import the fixed production_ready_loop module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixed_production_ready_loop

# Simple output callback to display streaming content
def output_callback(content_block):
    """Handle output content blocks"""
    if content_block.get("type") == "text":
        # Handle text content
        if content_block.get("is_delta", False):
            # This is a streaming delta, print without newline
            print(content_block["text"], end="", flush=True)
        else:
            # This is a complete block, print with newline
            print(f"\n[BLOCK START] {content_block.get('text', '')}")
    elif content_block.get("type") == "thinking":
        # Handle thinking content
        if content_block.get("is_delta", False):
            # This is a streaming delta, print without newline
            print(f"💭{content_block['thinking']}", end="", flush=True)
        else:
            # This is a complete block, print with newline
            print(f"\n[THINKING] {content_block.get('thinking', '')}")
    elif content_block.get("type") == "tool_use":
        # Handle tool use
        print(f"\n[TOOL USE] Using tool: {content_block.get('name', 'unknown')}")
        print(f"Input: {content_block.get('input', {})}")

# Tool output callback to display tool results
def tool_output_callback(result, tool_id):
    """Handle tool output results"""
    if result.error:
        print(f"\n[TOOL ERROR] {tool_id}: {result.error}")
    else:
        if hasattr(result, 'output') and result.output:
            print(f"\n[TOOL RESULT] {tool_id}: {result.output[:100]}...")
        if hasattr(result, 'base64_image') and result.base64_image:
            print(f"\n[TOOL IMAGE] {tool_id}: <image data>")

# API response callback
def api_response_callback(request, response, error):
    """Handle API responses"""
    if error:
        print(f"\n[API ERROR] {type(error).__name__}: {error}")
    elif response:
        print(f"\n[API RESPONSE] Received response")

async def run_test():
    """Run the test with a prompt that exercises tools and streaming"""
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
        else:
            raise ValueError("API key not found")
    
    # Test 1: Simple text streaming without tools
    print("\n=== Test 1: Simple Text Streaming ===")
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! Tell me about the current date. Keep it short."
                }
            ]
        }
    ]
    
    # Run the sampling loop - without tools
    try:
        updated_messages = await fixed_production_ready_loop.sampling_loop(
            model="claude-3-7-sonnet-20250219",
            provider="anthropic",
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key,
            tool_version="",  # Skip tools
            thinking_budget=None,  # Skip thinking
        )
        
        print("\nTest 1 completed!")
        print(f"Final message count: {len(updated_messages)}")
    except Exception as e:
        print(f"Test 1 failed with error: {e}")
    
    # Test 2: Tool use with streaming
    print("\n=== Test 2: Tool Use with Streaming ===")
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please use the bash tool to run the command 'date' and tell me what day of the week it is."
                }
            ]
        }
    ]
    
    # Run the sampling loop - with tools
    try:
        updated_messages = await fixed_production_ready_loop.sampling_loop(
            model="claude-3-7-sonnet-20250219",
            provider="anthropic",
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key,
            tool_version="computer_use_20250124",  # Include tools
            thinking_budget=None,  # Skip thinking
        )
        
        print("\nTest 2 completed!")
        print(f"Final message count: {len(updated_messages)}")
    except Exception as e:
        print(f"Test 2 failed with error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("Fixed Production Ready Loop Streaming Test")
    print("=" * 80)
    asyncio.run(run_test())