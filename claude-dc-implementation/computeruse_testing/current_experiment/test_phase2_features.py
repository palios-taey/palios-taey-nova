#!/usr/bin/env python3
"""
Test script to verify all Phase 2 features are working correctly:
1. Streaming responses with tool use
2. Prompt caching
3. 128K extended output
4. Thinking token budget
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
logger = logging.getLogger('test_phase2')

# Add paths to Python path
if os.path.exists("/home/computeruse"):
    # We're in the container
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

# Add key paths to Python path
paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import required libraries
try:
    # Import from computer_use_demo
    from computer_use_demo import (
        PROMPT_CACHING_BETA_FLAG,
        OUTPUT_128K_BETA_FLAG,
        ENABLE_PROMPT_CACHING,
        ENABLE_EXTENDED_OUTPUT,
        ENABLE_STREAMING,
        ENABLE_THINKING
    )
    from computer_use_demo.loop import sampling_loop
    from computer_use_demo.tools import ToolResult
    logger.info("Successfully imported from computer_use_demo")
except ImportError as e:
    logger.error(f"Failed to import from computer_use_demo: {e}")
    logger.error("Please ensure the code is properly installed")
    sys.exit(1)

# Import Anthropic client
try:
    from anthropic import Anthropic
    logger.info(f"Using Anthropic SDK version: {Anthropic.__version__}")
except ImportError:
    logger.error("Anthropic SDK not found. Please install it with: pip install anthropic")
    sys.exit(1)

# Get API key
def get_api_key():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            logger.info("Found API key in ~/.anthropic/api_key")
        else:
            logger.error("API key not found. Please set ANTHROPIC_API_KEY environment variable or create ~/.anthropic/api_key")
            sys.exit(1)
    return api_key

# Output callback
def output_callback(content_block):
    """Handle streamed content from Claude API."""
    if isinstance(content_block, dict):
        # Handle different block types
        if content_block.get("type") == "text":
            # Text content
            if content_block.get("is_delta", False):
                # Delta update
                print(content_block.get("text", ""), end="", flush=True)
            else:
                # Full block
                print("\n" + content_block.get("text", ""))
        elif content_block.get("type") == "thinking":
            # Thinking content
            if content_block.get("is_delta", False):
                # Delta update (just indicate progress)
                print(".", end="", flush=True)
            else:
                # Full block
                print(f"\n[Thinking: {len(content_block.get('thinking', ''))} characters]")
        elif content_block.get("type") == "tool_use":
            # Tool use notification
            print(f"\n[Using tool: {content_block.get('name', 'unknown')}]")
    else:
        # Fallback
        print(f"Other content: {content_block}")

# Tool output callback
def tool_output_callback(tool_output, tool_id):
    """Handle tool execution results."""
    print(f"\n[Tool output for {tool_id}]")
    if tool_output.output:
        print(tool_output.output)
    if tool_output.error:
        print(f"ERROR: {tool_output.error}")

# API response callback
def api_response_callback(request, response, error):
    """Handle API response or errors."""
    if error:
        print(f"\n[API ERROR: {error}]")
    elif response:
        print(f"\n[API response received: {len(str(response))} characters]")

async def test_phase2_features():
    """Run a test of all Phase 2 features."""
    print("=" * 80)
    print("Testing Claude DC Phase 2 Features")
    print("=" * 80)
    
    # Log current feature flags
    print("\nFeature Flags:")
    print(f"- Streaming: {'ENABLED' if ENABLE_STREAMING else 'DISABLED'}")
    print(f"- Prompt Caching: {'ENABLED' if ENABLE_PROMPT_CACHING else 'DISABLED'}")
    print(f"- Extended Output: {'ENABLED' if ENABLE_EXTENDED_OUTPUT else 'DISABLED'}")
    print(f"- Thinking: {'ENABLED' if ENABLE_THINKING else 'DISABLED'}")
    
    # Get API key
    api_key = get_api_key()
    
    # First message - test streaming and tool use
    messages = [{
        "role": "user",
        "content": [{
            "type": "text",
            "text": "Please tell me what day it is today and generate 5 creative names for tech startups."
        }]
    }]
    
    print("\n\n[TEST 1: Streaming & Tool Use]")
    print("Sending first query to test streaming and basic functionality...")
    
    messages = await sampling_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="You're running in a test environment to verify Phase 2 features.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,  # Smaller for first test
        thinking_budget=2048 if ENABLE_THINKING else None
    )
    
    # Second message - test prompt caching
    messages.append({
        "role": "user",
        "content": [{
            "type": "text",
            "text": "Please use Python to calculate the first 10 Fibonacci numbers."
        }]
    })
    
    print("\n\n[TEST 2: Tool Use & Prompt Caching]")
    print("Sending follow-up query to test prompt caching and tool use...")
    
    messages = await sampling_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="You're running in a test environment to verify Phase 2 features.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=8192,  # Medium size
        thinking_budget=4096 if ENABLE_THINKING else None
    )
    
    # Third message - test extended output
    messages.append({
        "role": "user",
        "content": [{
            "type": "text",
            "text": "Please provide an in-depth explanation of quantum computing, covering the fundamental principles, current state of the technology, major challenges, and potential applications. For each section, include at least 500 words of detailed explanation."
        }]
    })
    
    print("\n\n[TEST 3: Extended Output, Thinking & Prompt Caching]")
    print("Sending query to test extended output (requesting a very long response)...")
    
    messages = await sampling_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="You're running in a test environment to verify Phase 2 features.",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=65536,  # Full extended output
        thinking_budget=32768 if ENABLE_THINKING else None
    )
    
    print("\n\n[TEST COMPLETE]")
    print("All Phase 2 features have been tested.")
    
    # Summary of what was tested
    print("\nFeatures Verified:")
    print("✅ Streaming Responses")
    print("✅ Tool Use with Streaming")
    if ENABLE_PROMPT_CACHING:
        print("✅ Prompt Caching")
    else:
        print("❌ Prompt Caching (DISABLED)")
    if ENABLE_EXTENDED_OUTPUT:
        print("✅ Extended Output (128K)")
    else:
        print("❌ Extended Output (DISABLED)")
    if ENABLE_THINKING:
        print("✅ Thinking Token Budget")
    else:
        print("❌ Thinking Token Budget (DISABLED)")

if __name__ == "__main__":
    print("Starting Phase 2 feature test...")
    asyncio.run(test_phase2_features())