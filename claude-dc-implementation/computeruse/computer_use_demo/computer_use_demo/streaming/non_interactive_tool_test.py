#!/usr/bin/env python3
"""
Non-interactive tool streaming test for the streaming implementation.

This script tests the basic streaming functionality with tool use without requiring user input.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("non_interactive_tool_test")

async def execute_bash_command(command):
    """Execute a bash command and return the result."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return {"output": stdout.decode()}
        else:
            return {"error": stderr.decode()}
    except Exception as e:
        return {"error": str(e)}

async def test_non_interactive_tool_streaming(api_key=None, model="claude-3-sonnet-20240229"):
    """Run a non-interactive test of streaming with tool use."""
    
    # Try to import the Anthropic SDK
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        print("Error: Please install the Anthropic SDK: pip install anthropic")
        return
    
    # Set up API key
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: API key is required. Please provide it or set ANTHROPIC_API_KEY.")
        return
    
    print("\n===== Non-Interactive Tool Streaming Test =====")
    print("This test will demonstrate streaming with tool use.")
    
    # Define a simple bash tool
    bash_tool = {
        "name": "bash",
        "description": "Run a bash command and get the output",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run"
                }
            },
            "required": ["command"]
        }
    }
    
    # Set up the tool collection
    tools = [bash_tool]
    
    # Pre-defined test messages that will likely cause tool use
    test_messages = [
        "What files are in the current directory?",
        "How much disk space is available on this system?",
        "What is the current working directory?"
    ]
    
    for i, user_input in enumerate(test_messages):
        print(f"\nTest {i+1}: {user_input}")
        print("\nClaude: ", end="", flush=True)
        
        # Initialize the Anthropic client
        client = AsyncAnthropic(api_key=api_key)
        
        try:
            # Use the correct API for streaming
            stream = await client.messages.create(
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": user_input}
                ],
                model=model,
                tools=tools,
                stream=True,
            )
            
            tool_use = None
            collected_content = ""
            
            async for event in stream:
                if hasattr(event, "type"):
                    event_type = event.type
                    
                    if event_type == "content_block_start":
                        if hasattr(event, "content_block") and hasattr(event.content_block, "type"):
                            block_type = event.content_block.type
                            if block_type == "tool_use":
                                # Claude is attempting to use a tool
                                tool_use = event.content_block
                                tool_name = tool_use.name
                                tool_input = tool_use.input
                                
                                print(f"\n[Using tool: {tool_name}]")
                                print(f"[Tool input: {json.dumps(tool_input)}]")
                                
                                # Execute the tool
                                if tool_name == "bash":
                                    command = tool_input.get("command", "echo 'No command provided'")
                                    result = await execute_bash_command(command)
                                    
                                    # Send the tool result back to Claude
                                    await stream.send_tool_result(
                                        id=tool_use.id, 
                                        result=result
                                    )
                                    print(f"\n[Tool result: {json.dumps(result)}]")
                                    print("\nClaude (continuing): ", end="", flush=True)
                    
                    elif event_type == "content_block_delta":
                        # New content to display
                        if hasattr(event, "delta") and hasattr(event.delta, "text"):
                            print(event.delta.text, end="", flush=True)
                            collected_content += event.delta.text
                    
                    elif event_type == "message_stop":
                        # Message generation complete
                        print()  # Add a newline at the end
                        break
                
                else:
                    # Handle unexpected event structure
                    logger.warning(f"Unexpected event format: {event}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.exception("Error in streaming")
        
        # Add a separator between tests
        print("\n" + "-" * 80)
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test non-interactive tool streaming functionality")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--model", default="claude-3-sonnet-20240229", help="Model to use")
    
    args = parser.parse_args()
    
    asyncio.run(test_non_interactive_tool_streaming(
        api_key=args.api_key,
        model=args.model
    ))