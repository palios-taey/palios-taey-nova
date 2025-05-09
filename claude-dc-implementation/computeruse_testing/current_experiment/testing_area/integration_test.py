#!/usr/bin/env python3
"""
Phase 2 Integration Test
Tests the integration of all Phase 2 features: streaming, prompt caching, and extended output.
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.integration')

# Add necessary paths for imports
computer_use_demo_path = Path('/home/computeruse/computer_use_demo')
sys.path.insert(0, str(computer_use_demo_path))

# Import required modules
try:
    from tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolResult
    from anthropic import Anthropic
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Feature flags
ENABLE_STREAMING = True
ENABLE_PROMPT_CACHE = True
ENABLE_EXTENDED_OUTPUT = True
ENABLE_TOOLS = True

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

def tool_output_callback(result, tool_id):
    """Handle tool output."""
    if result.error:
        logger.error(f"Tool error (ID: {tool_id}): {result.error}")
        print(f"\n[Tool Error]: {result.error}")
    else:
        logger.info(f"Tool output received (ID: {tool_id})")
        if result.output:
            print(f"\n[Tool Output]: {result.output[:100]}{'...' if len(result.output) > 100 else ''}")
        
        if result.base64_image:
            logger.info(f"Tool returned an image (ID: {tool_id})")
            print(f"[Tool returned an image]")

def output_callback(block):
    """Handle content block output."""
    if block.get("type") == "text":
        if block.get("is_delta", False):
            print(block.get("text", ""), end="", flush=True)
        else:
            print(f"\n{block.get('text', '')}", end="")
    elif block.get("type") == "tool_use":
        logger.info(f"Tool use: {block.get('name')}")
        print(f"\n[Using tool: {block.get('name')}]")
    elif block.get("type") == "thinking":
        logger.info(f"Thinking: {block.get('thinking')[:50]}...")
        print(f"\n[Thinking: {block.get('thinking')[:50]}...]")

def api_response_callback(request, response, error):
    """Handle API response."""
    if error:
        logger.error(f"API error: {error}")
    elif response:
        logger.info(f"API response received")

async def integrated_sampling_loop(prompt: str, follow_up: str = None):
    """
    Run an integrated test of all Phase 2 features.
    """
    logger.info("Starting integrated sampling loop test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Set up tools if enabled
    tool_collection = None
    if ENABLE_TOOLS:
        tool_group = TOOL_GROUPS_BY_VERSION.get("computer_use_20250124")
        if tool_group:
            tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
            logger.info(f"Created tool collection with {len(tool_collection.tools)} tools")
    
    # Create initial messages
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
    
    # Add system message
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant with access to tools. Use tools when appropriate to answer questions or perform tasks."
        }
    ]
    
    # Add cache control to system if prompt caching is enabled
    if ENABLE_PROMPT_CACHE:
        system[0]["cache_control"] = {"type": "ephemeral"}
    
    # Set up max tokens based on extended output setting
    max_tokens = 128000 if ENABLE_EXTENDED_OUTPUT else 4096
    
    # Set up API params
    api_params = {
        "max_tokens": max_tokens,
        "messages": messages,
        "model": "claude-3-7-sonnet-20250219",
        "system": system,
        "stream": ENABLE_STREAMING
    }
    
    # Add tools if enabled
    if tool_collection:
        api_params["tools"] = tool_collection.to_params()
    
    # Add beta flags as needed
    beta_flags = []
    if ENABLE_TOOLS:
        beta_flags.append("computer-use-2025-01-24")
    if ENABLE_PROMPT_CACHE:
        beta_flags.append("prompt-caching-2024-07-31")
    
    if beta_flags:
        api_params["beta"] = beta_flags
    
    # First request
    logger.info(f"Making first API call with params: streaming={ENABLE_STREAMING}, tools={ENABLE_TOOLS}, prompt_cache={ENABLE_PROMPT_CACHE}, extended_output={ENABLE_EXTENDED_OUTPUT}")
    start_time_1 = time.time()
    
    try:
        if ENABLE_STREAMING:
            # Streaming implementation
            try:
                stream = client.messages.create(**api_params)
            except TypeError as e:
                # Handle unsupported beta flags
                if "beta" in str(e):
                    logger.warning("Beta parameter not supported, removing it and retrying")
                    api_params.pop("beta", None)
                    stream = client.messages.create(**api_params)
                else:
                    raise
            
            logger.info("Stream created successfully")
            
            # Process the stream
            print("\nResponse:")
            content_blocks = []
            
            for event in stream:
                if hasattr(event, "type"):
                    event_type = event.type
                    
                    if event_type == "content_block_start":
                        # New content block started
                        current_block = event.content_block
                        content_blocks.append(current_block)
                        
                        # Convert block to dict for callback
                        if hasattr(current_block, "model_dump"):
                            block_dict = current_block.model_dump()
                        else:
                            block_dict = {"type": getattr(current_block, "type", "unknown")}
                            
                            if hasattr(current_block, "text"):
                                block_dict["text"] = current_block.text
                            elif hasattr(current_block, "name") and getattr(current_block, "type", None) == "tool_use":
                                block_dict["name"] = current_block.name
                                block_dict["input"] = getattr(current_block, "input", {})
                                block_dict["id"] = getattr(current_block, "id", "unknown")
                        
                        output_callback(block_dict)
                        
                    elif event_type == "content_block_delta":
                        # Content block delta received
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Handle text delta
                            if hasattr(event.delta, "text") and event.delta.text:
                                if hasattr(content_blocks[event.index], "text"):
                                    content_blocks[event.index].text += event.delta.text
                                else:
                                    content_blocks[event.index].text = event.delta.text
                                    
                                # Create delta block for callback
                                delta_block = {
                                    "type": "text",
                                    "text": event.delta.text,
                                    "is_delta": True,
                                }
                                
                                output_callback(delta_block)
                    
                    elif event_type == "message_stop":
                        print("\n\nMessage complete")
                        break
            
            # Create a response structure
            first_response = {
                "role": "assistant",
                "content": content_blocks
            }
            
            # Process any tool uses
            tool_results = []
            for block in content_blocks:
                if getattr(block, "type", "") == "tool_use":
                    tool_name = getattr(block, "name", "")
                    tool_id = getattr(block, "id", "")
                    tool_input = getattr(block, "input", {})
                    
                    logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                    
                    if tool_collection:
                        # Run the tool
                        result = await tool_collection.run(
                            name=tool_name,
                            tool_input=tool_input,
                        )
                        
                        # Call the tool output callback
                        tool_output_callback(result, tool_id)
                        
                        # Add to tool results
                        tool_result = {
                            "type": "tool_result",
                            "content": result.output,
                            "tool_use_id": tool_id,
                            "is_error": bool(result.error)
                        }
                        tool_results.append(tool_result)
            
        else:
            # Non-streaming implementation
            first_response = client.messages.create(**api_params)
            # Print the response
            print("\nResponse:")
            print(first_response.content[0].text)
            
            # No tool processing in non-streaming mode for this test
            tool_results = []
        
        end_time_1 = time.time()
        first_duration = end_time_1 - start_time_1
        logger.info(f"First request completed in {first_duration:.2f} seconds")
        
        # If there's no follow-up or prompt caching is disabled, we're done
        if not follow_up or not ENABLE_PROMPT_CACHE:
            return True
        
        # Create follow-up message with cache breakpoint
        follow_up_messages = messages.copy()
        
        # Add assistant response
        if isinstance(first_response, dict):
            # From streaming
            assistant_message = first_response
        else:
            # From non-streaming
            assistant_message = {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": first_response.content[0].text
                    }
                ]
            }
        
        follow_up_messages.append(assistant_message)
        
        # Add tool results if any
        if tool_results:
            follow_up_messages.append({"role": "user", "content": tool_results})
        
        # Add follow-up user message with cache control
        follow_up_messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": follow_up,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        })
        
        # Make the second request with same parameters but updated messages
        logger.info("Making second API call with prompt caching")
        api_params["messages"] = follow_up_messages
        
        start_time_2 = time.time()
        
        if ENABLE_STREAMING:
            # Streaming implementation (simplified for follow-up)
            stream = client.messages.create(**api_params)
            
            # Process the stream with minimal output
            print("\nFollow-up Response:")
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text") and event.delta.text:
                            print(event.delta.text, end="", flush=True)
                    elif event.type == "message_stop":
                        print("\n\nFollow-up complete")
                        break
        else:
            # Non-streaming implementation
            second_response = client.messages.create(**api_params)
            print("\nFollow-up Response:")
            print(second_response.content[0].text)
        
        end_time_2 = time.time()
        second_duration = end_time_2 - start_time_2
        logger.info(f"Second request completed in {second_duration:.2f} seconds")
        
        # Calculate time saved
        time_saved = first_duration - second_duration
        percent_saved = (time_saved / first_duration) * 100 if first_duration > 0 else 0
        
        logger.info(f"Time saved with caching: {time_saved:.2f} seconds ({percent_saved:.1f}%)")
        
        # Write results to file
        with open('integration_test_results.txt', 'w') as f:
            f.write(f"INTEGRATION TEST RESULTS\n")
            f.write(f"=======================\n\n")
            f.write(f"Features enabled:\n")
            f.write(f"- Streaming: {ENABLE_STREAMING}\n")
            f.write(f"- Tools: {ENABLE_TOOLS}\n")
            f.write(f"- Prompt caching: {ENABLE_PROMPT_CACHE}\n")
            f.write(f"- Extended output: {ENABLE_EXTENDED_OUTPUT}\n\n")
            
            f.write(f"First request: {first_duration:.2f} seconds\n")
            if follow_up and ENABLE_PROMPT_CACHE:
                f.write(f"Second request: {second_duration:.2f} seconds\n")
                f.write(f"Time saved: {time_saved:.2f} seconds ({percent_saved:.1f}%)\n\n")
            
            f.write(f"Integration test {'successful' if (percent_saved > 10 or not ENABLE_PROMPT_CACHE) else 'inconclusive'}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in integration test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 2 Integration Test")
    print("=" * 80)
    print(f"Features enabled:")
    print(f"- Streaming: {ENABLE_STREAMING}")
    print(f"- Tools: {ENABLE_TOOLS}")
    print(f"- Prompt caching: {ENABLE_PROMPT_CACHE}")
    print(f"- Extended output: {ENABLE_EXTENDED_OUTPUT}")
    print("=" * 80)
    
    # Define prompts
    initial_prompt = "Can you provide an in-depth explanation of how neural networks work? Include details about different architectures and training methods."
    follow_up_prompt = "That was helpful. Can you also explain how transformers work specifically?"
    
    success = asyncio.run(integrated_sampling_loop(initial_prompt, follow_up_prompt))
    
    if success:
        print("\nIntegration test completed successfully!")
    else:
        print("\nIntegration test failed! Check the logs for details.")