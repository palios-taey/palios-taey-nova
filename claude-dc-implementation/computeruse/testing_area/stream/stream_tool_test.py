#!/usr/bin/env python3
"""
Streaming with Tools Test
Tests streaming implementation with actual tool execution.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streaming_tools_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test.streaming_tools')

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
        print(f"\n[Tool Output]: {result.output[:100]}{'...' if result.output and len(result.output) > 100 else ''}")
        
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

async def test_streaming_with_tools():
    """Test streaming implementation with tools."""
    logger.info("Starting streaming with tools test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Set up tools
    tool_group = TOOL_GROUPS_BY_VERSION.get("computer_use_20250124")
    if not tool_group:
        logger.error("Could not find computer_use_20250124 tool group")
        return False
    
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    logger.info(f"Created tool collection with {len(tool_collection.tools)} tools")
    
    # Set up a prompt that will use tools
    prompt = "Please tell me the current date and time using the bash tool."
    
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
    
    # Set up system prompt
    system = {
        "type": "text",
        "text": "You are Claude, an AI assistant with access to tools. Use the bash tool to find information when appropriate."
    }
    
    # Set up API params
    api_params = {
        "max_tokens": 4096,
        "messages": messages,
        "model": "claude-3-7-sonnet-20250219",
        "system": [system],
        "tools": tool_collection.to_params(),
        "stream": True
    }
    
    # Add beta flag if needed
    try:
        api_params["beta"] = ["computer-use-2025-01-24"]
    except Exception as e:
        logger.warning(f"Could not add beta flag: {e}")
    
    logger.info("Making API call with streaming enabled")
    try:
        # Make the API call with streaming
        with open('streaming_tools_output.txt', 'w') as f:
            f.write(f"PROMPT: {prompt}\n\nRESPONSE:\n")
            
            try:
                stream = client.messages.create(**api_params)
            except TypeError as e:
                # If beta parameter causes issues
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
                        f.write(f"\n[Block Start: {block_dict.get('type')}]")
                        
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
                                f.write(event.delta.text)
                    
                    elif event_type == "message_stop":
                        print("\n\nMessage complete")
                        f.write("\n\nMessage complete")
                        break
            
            # Process any tool uses
            for block in content_blocks:
                if getattr(block, "type", "") == "tool_use":
                    tool_name = getattr(block, "name", "")
                    tool_id = getattr(block, "id", "")
                    tool_input = getattr(block, "input", {})
                    
                    logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                    f.write(f"\n\n[Running tool: {tool_name}]")
                    
                    # Run the tool
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=tool_input,
                    )
                    
                    # Call the tool output callback
                    tool_output_callback(result, tool_id)
                    
                    # Write tool result to file
                    f.write(f"\n[Tool Result]: {result.output}")
                    if result.error:
                        f.write(f"\n[Tool Error]: {result.error}")
            
            logger.info("Streaming with tools test completed successfully")
            
    except Exception as e:
        logger.error(f"Error in streaming with tools test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("Streaming with Tools Test")
    print("=" * 80)
    success = asyncio.run(test_streaming_with_tools())
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Check the logs for details.")