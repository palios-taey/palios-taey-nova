#!/usr/bin/env python3
"""
Streaming Benchmark

This script compares streaming and non-streaming modes to demonstrate the benefits
of streaming in terms of perceived responsiveness.
"""

import os
import sys
import time
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streaming_benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.benchmark')

# Add path for module imports
sys.path.insert(0, '/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo')

# Import our streaming implementation
from streaming_loop import streaming_loop, validate_tool_input

# Import Anthropic
try:
    from anthropic import Anthropic
    from tools import ToolResult
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def get_api_key():
    """Get Anthropic API key from environment or file."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            logger.info("Found API key in ~/.anthropic/api_key")
        else:
            raise ValueError("API key not found")
    return api_key

# Track time to first token and token rate
first_token_time = None
token_times = []
token_count = 0
streaming_start_time = None

def streaming_output_callback(block):
    """Handle content block output with timing."""
    global first_token_time, token_count, token_times, streaming_start_time
    
    if streaming_start_time is None:
        streaming_start_time = time.time()
    
    if block.get("type") == "text":
        if block.get("is_delta", False):
            # Handle streaming token
            token_text = block.get("text", "")
            now = time.time()
            
            if first_token_time is None and token_text.strip():
                first_token_time = now
                logger.info(f"Time to first token: {first_token_time - streaming_start_time:.3f}s")
            
            token_count += 1
            token_times.append(now)
            
            # Print the token
            print(token_text, end="", flush=True)
        else:
            # Handle full text block
            print(f"\n{block.get('text', '')}", end="")
    elif block.get("type") == "tool_use":
        logger.info(f"Tool use: {block.get('name')}")
        print(f"\n[Using tool: {block.get('name')}]")

def non_streaming_output_callback(block):
    """Handle content block output for non-streaming mode."""
    if block.get("type") == "text":
        print(f"\n{block.get('text', '')}", end="")
    elif block.get("type") == "tool_use":
        logger.info(f"Tool use: {block.get('name')}")
        print(f"\n[Using tool: {block.get('name')}]")

def tool_output_callback(result, tool_id):
    """Handle tool output."""
    if result.error:
        logger.error(f"Tool error (ID: {tool_id}): {result.error}")
        print(f"\n[Tool Error]: {result.error}")
    else:
        logger.info(f"Tool output received (ID: {tool_id})")
        if result.output:
            print(f"\n[Tool Output]: {result.output[:100]}{'...' if len(result.output) > 100 else ''}")

def api_response_callback(request, response, error):
    """Handle API response."""
    if error:
        logger.error(f"API error: {error}")

async def run_non_streaming_test(api_key):
    """Run a non-streaming test for comparison."""
    # Reset metrics
    global first_token_time, token_count, token_times, streaming_start_time
    first_token_time = None
    token_count = 0
    token_times = []
    streaming_start_time = None
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Set up a prompt that will generate a detailed response
    prompt = "Please explain how neural networks work, including details about backpropagation and activation functions. Keep it under 500 words."
    
    # Create messages
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    # Set up system message
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. Provide clear and concise educational explanations."
        }
    ]
    
    print("\nRunning non-streaming test...")
    start_time = time.time()
    print("\nWaiting for response...", end="", flush=True)
    
    # Make the API call without streaming
    response = client.messages.create(
        max_tokens=4096,
        messages=messages,
        model="claude-3-7-sonnet-20250219",
        system=system
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print the full response at once
    print(f"\n\n{response.content[0].text}")
    
    print(f"\nNon-streaming test completed in {total_time:.2f} seconds")
    logger.info(f"Non-streaming test total time: {total_time:.2f}s")
    
    return total_time

async def run_streaming_test(api_key):
    """Run a streaming test to measure performance."""
    # Reset metrics
    global first_token_time, token_count, token_times, streaming_start_time
    first_token_time = None
    token_count = 0
    token_times = []
    streaming_start_time = None
    
    # Set up the same prompt for a fair comparison
    prompt = "Please explain how neural networks work, including details about backpropagation and activation functions. Keep it under 500 words."
    
    # Create messages
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    print("\nRunning streaming test...")
    start_time = time.time()
    
    # Run with streaming
    await streaming_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="Provide clear and concise educational explanations.",
        messages=messages,
        output_callback=streaming_output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=4096,
        tool_version="computer_use_20250124"
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate metrics
    if token_count > 0 and streaming_start_time is not None:
        if first_token_time is not None:
            ttft = first_token_time - streaming_start_time
        else:
            ttft = "N/A"
        
        print(f"\n\nStreaming test completed in {total_time:.2f} seconds")
        print(f"Time to first token: {ttft}")
        print(f"Total tokens received: {token_count}")
        print(f"Average tokens per second: {token_count / total_time:.2f}")
        
        logger.info(f"Streaming test - Total time: {total_time:.2f}s, TTFT: {ttft}, Tokens: {token_count}")
    
    return total_time

async def benchmark():
    """Run the full benchmark comparing streaming and non-streaming."""
    print("=" * 80)
    print("Claude DC Streaming vs. Non-Streaming Benchmark")
    print("=" * 80)
    
    # Get API key
    api_key = get_api_key()
    
    # Run non-streaming test
    non_streaming_time = await run_non_streaming_test(api_key)
    
    # Short pause between tests
    await asyncio.sleep(1)
    
    # Run streaming test
    streaming_time = await run_streaming_test(api_key)
    
    # Compare results
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(f"Non-streaming time: {non_streaming_time:.2f} seconds")
    print(f"Streaming time: {streaming_time:.2f} seconds")
    
    if streaming_time > 0 and non_streaming_time > 0:
        if first_token_time and streaming_start_time:
            ttft = first_token_time - streaming_start_time
            print(f"Time to first token with streaming: {ttft:.2f} seconds")
            print(f"Perceived responsiveness improvement: {(non_streaming_time - ttft) / non_streaming_time * 100:.1f}%")
    
    print("=" * 80)
    print("\nNote: Even though the total time might be similar, streaming provides a much better user experience")
    print("because the user sees content immediately rather than waiting for the entire response.")
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(benchmark())
    except Exception as e:
        print(f"Benchmark failed with error: {e}")
        logger.error(f"Benchmark failed with error: {e}")
        sys.exit(1)
    
    sys.exit(0)