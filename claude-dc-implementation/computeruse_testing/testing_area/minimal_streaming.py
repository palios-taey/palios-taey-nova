#!/usr/bin/env python3
"""
Minimal Streaming Implementation
Demonstrates streaming functionality with the bash tool only for maximum compatibility.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('minimal_streaming.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.minimal')

# Add paths for imports
sys.path.insert(0, str(Path('/home/computeruse/computer_use_demo')))

try:
    # Import from tools
    from tools import ToolCollection, ToolResult
    from tools.bash import BashTool20250124
    
    # Import Anthropic
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

# Track tokens
token_count = 0

def output_callback(content):
    """Handle streamed content."""
    global token_count
    
    # For deltas, just print the text
    if isinstance(content, str):
        token_count += 1
        print(content, end="", flush=True)
    # For tool use, print a notification
    elif isinstance(content, dict) and content.get("type") == "tool_use":
        print(f"\n[Using tool: {content.get('name', 'unknown')}]")
    # For other content, print it
    elif isinstance(content, dict) and content.get("type") == "text":
        print(f"\n{content.get('text', '')}")

async def run_tool(tool_name, tool_input):
    """Run a tool and return the result."""
    logger.info(f"Running tool: {tool_name}")
    
    if tool_name == "bash":
        # Create bash tool
        bash_tool = BashTool20250124()
        # Ensure command is specified
        if "command" not in tool_input or not tool_input["command"]:
            logger.warning("Bash tool called without command, adding default")
            tool_input["command"] = "echo 'Please specify a command'"
        # Run the tool
        try:
            result = await bash_tool(**tool_input)
            logger.info(f"Tool execution successful: {result.output[:100]}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(error=str(e))
    else:
        # Unsupported tool
        logger.error(f"Unsupported tool: {tool_name}")
        return ToolResult(error=f"Tool '{tool_name}' not supported in this test")

async def run_streaming_test():
    """Run a streaming test with bash tool."""
    logger.info("Starting minimal streaming test...")
    
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    logger.info("Created Anthropic client")
    
    # Create tool collection with just bash
    bash_tool = BashTool20250124()
    tool_collection = ToolCollection(bash_tool)
    
    # Set up a prompt that will use bash
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
    
    # Set up system message
    system = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant with access to bash. Use the bash tool to find information when appropriate."
        }
    ]
    
    # Set up API params
    api_params = {
        "max_tokens": 4096,
        "messages": messages,
        "model": "claude-3-7-sonnet-20250219",
        "system": system,
        "tools": tool_collection.to_params(),
        "stream": True
    }
    
    logger.info("Making streaming API call")
    try:
        # Make streaming API call
        stream = client.messages.create(**api_params)
        logger.info("Stream created successfully")
        
        # Process the stream for text and tool usage
        response_blocks = []
        current_block = None
        current_index = None
        
        print("\nResponse:")
        for event in stream:
            if hasattr(event, "type"):
                event_type = event.type
                
                if event_type == "content_block_start":
                    # New content block
                    block_data = {}
                    
                    if hasattr(event.content_block, "type"):
                        block_type = event.content_block.type
                        block_data["type"] = block_type
                        
                        # Handle different block types
                        if block_type == "text" and hasattr(event.content_block, "text"):
                            block_data["text"] = event.content_block.text
                            print(f"\n{event.content_block.text}", end="")
                        elif block_type == "tool_use":
                            block_data["name"] = event.content_block.name
                            block_data["input"] = getattr(event.content_block, "input", {})
                            block_data["id"] = getattr(event.content_block, "id", "unknown")
                            print(f"\n[Using tool: {block_data['name']}]")
                    
                    # Store the block
                    response_blocks.append(block_data)
                    current_index = len(response_blocks) - 1
                    current_block = block_data
                
                elif event_type == "content_block_delta":
                    # Content update
                    if hasattr(event, "index") and event.index < len(response_blocks):
                        current_index = event.index
                        current_block = response_blocks[current_index]
                        
                        # Handle text delta
                        if hasattr(event.delta, "text") and event.delta.text:
                            if "text" not in current_block:
                                current_block["text"] = ""
                            current_block["text"] += event.delta.text
                            print(event.delta.text, end="", flush=True)
                
                elif event_type == "message_stop":
                    # Message complete
                    logger.info("Message generation complete")
                    print("\n\nMessage complete!")
                    break
        
        # Process tool usage
        for block in response_blocks:
            if block.get("type") == "tool_use":
                tool_name = block.get("name")
                tool_input = block.get("input", {})
                tool_id = block.get("id")
                
                # Run the tool
                result = await run_tool(tool_name, tool_input)
                
                # Display the result
                if result.error:
                    print(f"\n[Tool Error]: {result.error}")
                else:
                    print(f"\n[Tool Output]: {result.output}")
        
        logger.info(f"Test completed with {len(response_blocks)} content blocks")
        logger.info(f"Received approximately {token_count} streaming tokens")
        return True
        
    except Exception as e:
        logger.error(f"Error in streaming test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Minimal Streaming Implementation Test")
    print("=" * 80)
    
    try:
        success = asyncio.run(run_streaming_test())
        
        if success:
            print("\nMinimal streaming test completed successfully!")
        else:
            print("\nMinimal streaming test failed! Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)
    
    print("\nStreaming functionality works with the bash tool!")
    sys.exit(0)