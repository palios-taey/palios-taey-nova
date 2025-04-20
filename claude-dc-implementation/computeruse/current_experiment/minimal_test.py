#!/usr/bin/env python3
"""
Ultra-minimal streaming test.
This is a simplified version that avoids beta flags entirely.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Set Python path based on container environment
if os.path.exists("/home/computeruse"):
    # We're in the container
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

# Add paths to Python path
paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        
# Try to add computeruse path for tools
if os.path.exists(computer_use_demo_dir):
    sys.path.insert(0, str(computer_use_demo_dir))

# Import required libraries
from anthropic import Anthropic

# Get Anthropic API key
def get_api_key():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            print("Found API key in ~/.anthropic/api_key")
        else:
            raise ValueError("API key not found")
    return api_key

async def run_minimal_test():
    """Run a minimal test with streaming only."""
    print("Starting minimal streaming test...")
    
    # Import tool modules
    try:
        # Try to import from computer_use_demo.tools
        from computer_use_demo.tools import ToolCollection, TOOL_GROUPS_BY_VERSION
        print("Successfully imported tools from computer_use_demo.tools")
    except ImportError as e:
        print(f"Failed to import from computer_use_demo.tools: {e}")
        try:
            # Try direct import
            from tools import ToolCollection, TOOL_GROUPS_BY_VERSION
            print("Successfully imported tools directly")
        except ImportError as e2:
            print(f"Failed to import tools: {e2}")
            print("Continuing without tools to test basic streaming...")
            
    # Get API key
    api_key = get_api_key()
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key)
    print("Created Anthropic client")
    
    # Set up a simple prompt
    prompt = "Hello! Can you tell me about today's date and what day of the week it is?"
    
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
    
    # Set up API params - avoiding beta flags entirely
    api_params = {
        "max_tokens": 4096,
        "messages": messages,
        "model": "claude-3-7-sonnet-20250219",
        "stream": True  # Enable streaming
    }
    
    # Add system message 
    api_params["system"] = [
        {
            "type": "text",
            "text": "You are Claude, an AI assistant. Keep your responses short and to the point."
        }
    ]
    
    # Only add tools if we successfully imported them
    if 'ToolCollection' in locals() and 'TOOL_GROUPS_BY_VERSION' in locals():
        try:
            tool_group = TOOL_GROUPS_BY_VERSION.get("computer_use_20250124")
            if tool_group:
                print("Creating tool collection...")
                tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
                api_params["tools"] = tool_collection.to_params()
                print(f"Added {len(tool_collection.tools)} tools to API call")
        except Exception as e:
            print(f"Failed to set up tools: {e}")
            print("Continuing without tools")
    
    print(f"Making API call with streaming enabled")
    try:
        # Make the API call with streaming
        stream = client.messages.create(**api_params)
        print("Stream created successfully")
        
        # Process the stream
        print("\nResponse:")
        for event in stream:
            if hasattr(event, "type"):
                # Handle different event types
                if event.type == "content_block_start":
                    # New content block started
                    if hasattr(event.content_block, "type"):
                        # Print based on block type
                        if event.content_block.type == "text":
                            print(f"\n{event.content_block.text}", end="")
                        elif event.content_block.type == "tool_use":
                            print(f"\n[Using tool: {event.content_block.name}]")
                
                elif event.type == "content_block_delta":
                    # Handle deltas
                    if hasattr(event, "delta") and hasattr(event.delta, "text"):
                        print(event.delta.text, end="", flush=True)
                
                elif event.type == "message_stop":
                    print("\n\nMessage complete")
                    break
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error in streaming test: {e}")
        print("Try checking the installed version of the Anthropic client")
        print(f"You're using Anthropic SDK version: {Anthropic.__version__ if hasattr(Anthropic, '__version__') else 'unknown'}")

if __name__ == "__main__":
    print("=" * 80)
    print("Ultra-Minimal Streaming Test")
    print("=" * 80)
    asyncio.run(run_minimal_test())