#!/bin/bash
# Final fix for Claude DC validation errors

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

# Create a minimal version of loop.py that avoids all the validation issues
cat > /home/computeruse/computer_use_demo/loop.py << 'EOF'
"""
Minimal sampling loop for Claude DC - simplified to avoid validation errors.
"""

import logging
import os
import httpx
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union, cast

from anthropic import Anthropic, APIError, APIResponseValidationError, APIStatusError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

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

# Basic settings
DEFAULT_MAX_TOKENS = 4096
DEFAULT_THINKING_BUDGET = 0  # Disable thinking to avoid validation errors

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
    messages: list[BetaMessageParam],
    output_callback: Callable[[Union[BetaContentBlockParam, Dict[str, Any]]], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request, Union[httpx.Response, object, None], Optional[Exception]], None
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
            
            # Create a basic messages call - avoid all beta flags and thinking
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
                        # Convert to dictionary to avoid validation issues
                        if hasattr(event.content_block, "model_dump"):
                            block_dict = event.content_block.model_dump()
                        else:
                            # Fallback for older SDK versions
                            block_dict = {
                                "type": getattr(event.content_block, "type", "text"),
                            }
                            if hasattr(event.content_block, "text"):
                                block_dict["text"] = event.content_block.text
                        
                        content_blocks.append(block_dict)
                        # Notify callback
                        output_callback(block_dict)
                    
                    elif event.type == "content_block_delta":
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Only handle text deltas
                            if hasattr(event.delta, "text") and event.delta.text:
                                if content_blocks[event.index].get("type") == "text":
                                    content_blocks[event.index]["text"] += event.delta.text
                                    # Notify callback about delta
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
                    
                    # Convert result to dictionary
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
                    
                    # Create tool result block
                    tool_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result_content,
                        "is_error": is_error
                    }
                    
                    tool_results.append(tool_result)
                    tool_output_callback(result, tool_id)
            
            # Process response
            messages.append({
                "role": "assistant",
                "content": content_blocks
            })
            
            # If we have tool results, add them too
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

# Create a simple launch script
cat > /home/computeruse/minimal_launch.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal launcher for Claude DC that uses the Python API directly.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import httpx
from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('minimal_claude')

def main():
    """Main function to start minimal Claude DC."""
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Simple message call without any beta flags or complex features
    print("Testing minimal API call...")
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Say hello and explain what you can do."}
        ],
        system="You are Claude DC, a specialized Claude agent focused on computer tasks."
    )
    
    print("\nResponse from Claude:")
    print(message.content[0].text)
    print("\nAPI call successful! You can now use Streamlit with the fixed code.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x /home/computeruse/minimal_launch.py

echo "Final fix applied!"
echo ""
echo "First, test a minimal API call (no Streamlit) with:"
echo "cd /home/computeruse"
echo "python3 minimal_launch.py"
echo ""
echo "If that works, try the Streamlit interface with:"
echo "python3 launch_claude_simplified.py"