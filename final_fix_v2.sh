#!/bin/bash
# Final fix for Claude DC validation errors - Version 2

echo "Applying final fix for Claude DC validation errors..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current loop.py
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p /home/computeruse/backups
cp /home/computeruse/computer_use_demo/loop.py /home/computeruse/backups/loop.py.bak_${TIMESTAMP}
echo "Created backup at /home/computeruse/backups/loop.py.bak_${TIMESTAMP}"

# Create a minimal version of loop.py
cat > /home/computeruse/computer_use_demo/loop.py << 'LOOPEOF'
"""
Minimal sampling loop for Claude DC - simplified to avoid validation errors.
"""

import logging
import os
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union, cast

import httpx
from anthropic import Anthropic, APIError, APIResponseValidationError, APIStatusError

from .tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolResult, ToolVersion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc')

# Environment configuration
if 'CLAUDE_ENV' in os.environ:
    MODE = os.environ['CLAUDE_ENV']
else:
    MODE = 'live'

# Define constants and types
DEFAULT_MAX_TOKENS = 4096
DEFAULT_THINKING_BUDGET = 0  # Disable thinking

# Type aliases for cleaner code
BetaContentBlockParam = Dict[str, Any]
BetaMessageParam = Dict[str, Any]
BetaTextBlockParam = Dict[str, Any]
BetaToolResultBlockParam = Dict[str, Any]
BetaToolUseBlockParam = Dict[str, Any]

# System prompt
SYSTEM_PROMPT = """You are Claude DC, "The Conductor," a specialized version of Claude focused on interacting with computer systems."""


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request, Optional[Union[httpx.Response, object]], Optional[Exception]], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
):
    """Simplified sampling loop for Claude DC."""
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    
    system = {
        "type": "text",
        "text": f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    }

    while True:
        try:
            # Initialize client
            client = Anthropic(api_key=api_key, max_retries=4)
            
            # Create API params - simplified with no beta features
            logger.info("Making API call to Anthropic...")
            stream = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=[system],
                messages=messages,
                tools=tool_collection.to_params(),
                stream=True
            )
            
            # Track blocks as dictionaries instead of objects
            content_blocks = []
            
            # Process stream
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        # Get block data as dict
                        block_dict = {}
                        if hasattr(event.content_block, "type"):
                            block_dict["type"] = event.content_block.type
                        else:
                            block_dict["type"] = "text"  # Default to text if no type
                            
                        if hasattr(event.content_block, "text"):
                            block_dict["text"] = event.content_block.text
                        elif block_dict["type"] == "text":
                            block_dict["text"] = ""
                            
                        content_blocks.append(block_dict)
                        # Notify callback
                        output_callback(block_dict)
                    
                    elif event.type == "content_block_delta":
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Only handle text deltas
                            if hasattr(event.delta, "text") and event.delta.text:
                                if content_blocks[event.index].get("type") == "text":
                                    # Update existing text
                                    content_blocks[event.index]["text"] += event.delta.text
                                    # Notify callback
                                    output_callback({
                                        "type": "text",
                                        "text": event.delta.text,
                                        "is_delta": True
                                    })
                    
                    elif event.type == "message_stop":
                        break
            
            # Process tool usage
            tool_results = []
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_id = block.get("id", "")
                    tool_input = block.get("input", {})
                    
                    logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                    
                    # Run tool
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=tool_input,
                        streaming=True
                    )
                    
                    # Convert result
                    tool_result_content = []
                    is_error = bool(result.error)
                    
                    if result.error:
                        tool_result_content = result.error
                    else:
                        if result.output:
                            tool_result_content.append({
                                "type": "text",
                                "text": result.output
                            })
                        if result.base64_image:
                            tool_result_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": result.base64_image
                                }
                            })
                    
                    # Create tool result
                    tool_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result_content,
                        "is_error": is_error
                    }
                    
                    tool_results.append(tool_result)
                    tool_output_callback(result, tool_id)
            
            # Add response to messages
            messages.append({
                "role": "assistant",
                "content": content_blocks
            })
            
            # Handle tool results
            if tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                return messages
                
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"API error: {e}")
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            logger.error(f"API error: {e}")
            api_response_callback(e.request, e.body, e)
            return messages
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            api_response_callback(
                httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
                None,
                e
            )
            return messages
LOOPEOF

# Create a minimal test script
cat > /home/computeruse/test_api.py << 'TESTEOF'
#!/usr/bin/env python3
"""
Simple script to test the Anthropic API directly.
"""

import os
from anthropic import Anthropic

def main():
    """Run a simple API test."""
    # Get API key from environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Initialize client
    client = Anthropic(api_key=api_key)
    
    # Make a simple API call with no beta features
    print("Testing API call...")
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Say hello and explain what you can do in one paragraph."}
        ],
        system="You are Claude, an AI assistant."
    )
    
    print("\nResponse from Claude:")
    print(message.content[0].text)
    print("\nAPI test successful!")
    
if __name__ == "__main__":
    main()
TESTEOF

chmod +x /home/computeruse/test_api.py

# Create a simple standalone launcher
cat > /home/computeruse/simple_claude.py << 'SIMPLEEOF'
#!/usr/bin/env python3
"""
Simple launcher for Claude DC that bypasses Streamlit.
"""

import os
import asyncio
from anthropic import Anthropic

async def main():
    """Run a simple conversation with Claude."""
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Initialize client
    client = Anthropic(api_key=api_key)
    
    # Simple conversation loop
    messages = []
    
    print("\n=== Claude DC Simple Console ===")
    print("(Type 'exit' to quit)")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        # Add to messages
        messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Call API
        print("\nClaude DC: ", end="", flush=True)
        
        response = None
        if os.environ.get('USE_STREAM', 'true').lower() == 'true':
            # With streaming
            with client.messages.stream(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                messages=messages,
                system="You are Claude DC, a helpful AI assistant."
            ) as stream:
                response_text = ""
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    response_text += text
                
                response = {"text": response_text}
        else:
            # Without streaming
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219", 
                max_tokens=4096,
                messages=messages,
                system="You are Claude DC, a helpful AI assistant."
            )
            print(message.content[0].text)
            response = {"text": message.content[0].text}
            
        # Add response to messages
        messages.append({
            "role": "assistant", 
            "content": [{"type": "text", "text": response["text"]}]
        })
    
    print("\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())
SIMPLEEOF

chmod +x /home/computeruse/simple_claude.py

echo "Final fix applied!"
echo ""
echo "To test the API directly (no tools/streaming):"
echo "cd /home/computeruse"
echo "python3 test_api.py"
echo ""
echo "To use a simple Claude console (no tools):"
echo "python3 simple_claude.py"
echo ""
echo "If those work, you can try the full Streamlit interface:"
echo "python3 launch_claude_simplified.py"