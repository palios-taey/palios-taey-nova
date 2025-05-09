"""
Production-ready loop implementation with streaming support.
Based on the successful minimal streaming test.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.loop')

# Determine paths based on environment
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
from computer_use_demo.tools import (
    TOOL_GROUPS_BY_VERSION,
    ToolCollection,
    ToolResult,
    ToolVersion,
)
from anthropic import (
    Anthropic,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)

# Constants
DEFAULT_MAX_TOKENS = 65536  # ~64k max output
DEFAULT_THINKING_BUDGET = 32768  # ~32k thinking budget

# Get boolean environment variable with default value
def get_bool_env(name, default=False):
    """Parse boolean environment variables with proper error handling."""
    value = os.environ.get(name)
    if value is None:
        return default
    
    value = value.lower()
    if value in ('true', 't', 'yes', 'y', '1'):
        return True
    elif value in ('false', 'f', 'no', 'n', '0'):
        return False
    else:
        logger.warning(f"Invalid boolean value for {name}: '{value}', using default: {default}")
        return default

# Feature flags - simplified with focus on streaming
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to True
ENABLE_THINKING = get_bool_env('ENABLE_THINKING', True)  # Default to True

class APIProvider:
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# System prompt - simplified for clarity
SYSTEM_PROMPT = """You are Claude DC, "The Conductor," a specialized version of Claude focused on interacting with computer systems.
You are utilizing an Ubuntu virtual machine with access to tools.
Keep your responses focused and action-oriented.
"""

async def sampling_loop(
    *,
    model: str,
    provider: str,
    system_prompt_suffix: str,
    messages: List[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[Any, Any, Optional[Exception]], None],
    api_key: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    tool_version: str = "computer_use_20250124",
    thinking_budget: Optional[int] = None,
):
    """
    Agentic sampling loop with streaming support.
    Simplified from the original to focus on reliable streaming functionality.
    """
    # Get tool group for specified version
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    
    # Create system prompt
    system = {
        "type": "text",
        "text": f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    }
    
    # Create Anthropic client based on provider
    if provider == APIProvider.ANTHROPIC:
        client = Anthropic(api_key=api_key, max_retries=3)
    elif provider == APIProvider.VERTEX:
        from anthropic import AnthropicVertex
        client = AnthropicVertex()
    elif provider == APIProvider.BEDROCK:
        from anthropic import AnthropicBedrock
        client = AnthropicBedrock()
    else:
        # Fallback to Anthropic API
        client = Anthropic(api_key=api_key, max_retries=3)
    
    # Create API parameters - focusing on essential parameters only
    api_params = {
        "max_tokens": max_tokens,
        "messages": messages,
        "model": model,
        "system": [system],
        "tools": tool_collection.to_params(),
        "stream": ENABLE_STREAMING  # Enable streaming (default: True)
    }
    
    # Add thinking budget if enabled
    if ENABLE_THINKING and thinking_budget:
        try:
            api_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
            logger.info(f"Added thinking budget: {thinking_budget}")
        except Exception as e:
            logger.warning(f"Failed to add thinking parameter: {e}")
    
    # Simplified approach: add required beta flag for computer use tools
    try:
        if tool_version == "computer_use_20250124":
            api_params["beta"] = ["computer-use-2025-01-24"]
            logger.info("Added required beta flag: computer-use-2025-01-24")
    except Exception as e:
        logger.warning(f"Failed to add computer-use beta flag: {e}")
    
    logger.info(f"Making API call with streaming: {ENABLE_STREAMING}")
    
    try:
        # Make API call with proper error handling
        try:
            # First try with all parameters
            stream = client.messages.create(**api_params)
        except TypeError as e:
            # If 'beta' parameter is causing issues, remove it and try again
            if "got an unexpected keyword argument 'beta'" in str(e):
                logger.warning("Beta parameter not supported, removing it and retrying")
                api_params.pop('beta', None)
                
                # Also check for thinking parameter support
                if "thinking" in api_params and "got an unexpected keyword argument 'thinking'" in str(e):
                    logger.warning("Thinking parameter not supported, removing it and retrying")
                    api_params.pop('thinking', None)
                
                # Try API call again without the unsupported parameters
                stream = client.messages.create(**api_params)
            else:
                # Other TypeError, re-raise
                raise
                
        logger.info("Stream created successfully")
        
        # Process the stream
        content_blocks = []
        
        # Process stream events
        for event in stream:
            if hasattr(event, "type"):
                event_type = event.type
                
                if event_type == "content_block_start":
                    # New content block started
                    current_block = event.content_block
                    content_blocks.append(current_block)
                    
                    # Convert block to dict for callback
                    if hasattr(current_block, "model_dump"):
                        # New SDK versions
                        block_dict = current_block.model_dump()
                    else:
                        # Create a dict with minimal properties for older versions
                        block_dict = {"type": getattr(current_block, "type", "unknown")}
                        
                        if hasattr(current_block, "text"):
                            block_dict["text"] = current_block.text
                        elif hasattr(current_block, "thinking"):
                            block_dict["thinking"] = current_block.thinking
                        elif hasattr(current_block, "name") and getattr(current_block, "type", None) == "tool_use":
                            block_dict["name"] = current_block.name
                            block_dict["input"] = getattr(current_block, "input", {})
                            block_dict["id"] = getattr(current_block, "id", "unknown")
                    
                    # Send to output callback
                    output_callback(block_dict)
                    
                elif event_type == "content_block_delta":
                    # Content block delta received
                    if hasattr(event, "index") and event.index < len(content_blocks):
                        # Handle text delta
                        if hasattr(event.delta, "text") and event.delta.text:
                            # Update the block with delta
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
                            
                            # Send to output callback
                            output_callback(delta_block)
                            
                        # Handle thinking delta if available
                        elif hasattr(event.delta, "thinking") and event.delta.thinking:
                            # Update the block with delta
                            if hasattr(content_blocks[event.index], "thinking"):
                                content_blocks[event.index].thinking += event.delta.thinking
                            else:
                                content_blocks[event.index].thinking = event.delta.thinking
                                
                            # Create delta block for callback
                            delta_block = {
                                "type": "thinking",
                                "thinking": event.delta.thinking,
                                "is_delta": True,
                            }
                            
                            # Send to output callback
                            output_callback(delta_block)
                
                elif event_type == "message_stop":
                    # Message generation complete
                    logger.info("Message generation complete")
                    break
                    
        # Create a response structure for consistency with non-streaming mode
        response = {
            "id": "",
            "role": "assistant",
            "model": model,
            "content": content_blocks,
            "stop_reason": "end_turn",
            "type": "message",
        }
        
        # Call API response callback
        api_response_callback(None, response, None)
        
    except (APIStatusError, APIResponseValidationError) as e:
        api_response_callback(None, None, e)
        return messages
    except APIError as e:
        api_response_callback(None, None, e)
        return messages
    except Exception as e:
        api_response_callback(None, None, e)
        return messages
        
    # Process the response
    response_params = _response_to_params(response)
    messages.append({
        "role": "assistant",
        "content": response_params,
    })
    
    # Process tools if any
    tool_result_content = []
    for content_block in response_params:
        if content_block["type"] == "tool_use":
            # Extract tool information
            tool_name = content_block["name"]
            tool_id = content_block["id"]
            tool_input = content_block["input"]
            
            logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
            
            # Configure tool collection for streaming if supported
            for tool in tool_collection.tools:
                if hasattr(tool, 'set_stream_callback'):
                    tool.set_stream_callback(
                        lambda chunk, tid=tool_id: tool_output_callback(
                            ToolResult(output=chunk, error=None),
                            tid
                        )
                    )
            
            # Run the tool
            result = await tool_collection.run(
                name=tool_name,
                tool_input=tool_input,
                streaming=True,  # Enable streaming for the tool
            )
            
            # Create tool result and notify callback
            tool_result = _make_api_tool_result(result, tool_id)
            tool_result_content.append(tool_result)
            
            # Only send final result if tools don't support streaming
            if not any(hasattr(t, 'set_stream_callback') for t in tool_collection.tools):
                tool_output_callback(result, tool_id)
    
    # Add tool results to messages if any
    if tool_result_content:
        messages.append({"content": tool_result_content, "role": "user"})
    
    return messages

def _response_to_params(response):
    """Convert response content to parameters."""
    result = []
    for block in response["content"]:
        if hasattr(block, "type"):
            block_type = block.type
            
            if block_type == "text":
                if hasattr(block, "text") and block.text:
                    result.append({
                        "type": "text", 
                        "text": block.text
                    })
            elif block_type == "thinking":
                if hasattr(block, "thinking") and block.thinking:
                    result.append({
                        "type": "thinking",
                        "thinking": block.thinking
                    })
            elif block_type == "tool_use":
                # Convert tool use block to dict
                tool_dict = {
                    "type": "tool_use",
                    "name": getattr(block, "name", "unknown"),
                    "id": getattr(block, "id", "unknown"),
                    "input": getattr(block, "input", {})
                }
                result.append(tool_dict)
    
    return result

def _make_api_tool_result(result, tool_use_id):
    """Convert a ToolResult to an API tool result block."""
    tool_result_content = []
    is_error = False
    
    if result.error:
        is_error = True
        tool_result_content = result.error
    else:
        if result.output:
            tool_result_content.append({
                "type": "text",
                "text": result.output,
            })
        if result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                },
            })
    
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }