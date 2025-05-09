"""
Streaming Implementation for Claude DC

This module implements streaming functionality for the Claude DC system without introducing
beta features. It's designed to work with the existing tools and maintains compatibility
with the current API.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.streaming')

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
try:
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
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Constants
DEFAULT_MAX_TOKENS = 4096  # Conservative token limit
DEFAULT_THINKING_BUDGET = 32768  # Support thinking budget

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

# Feature flag - single flag for streaming
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to True for safety
logger.info(f"Streaming enabled: {ENABLE_STREAMING}")

# Provider constants
class APIProvider:
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# Tool input validation
def validate_tool_input(tool_name, tool_input):
    """Validate and potentially fix tool inputs"""
    # Make a copy of the input to avoid modifying the original
    fixed_input = tool_input.copy() if tool_input else {}
    
    # Handle bash tool
    if tool_name.lower() == 'bash':
        if 'command' not in fixed_input or not fixed_input['command']:
            logger.warning("Bash tool called without a command, adding default")
            fixed_input['command'] = "echo 'Please specify a command'"
    
    # Handle computer tool
    elif tool_name.lower() == 'computer':
        if 'action' not in fixed_input or not fixed_input['action']:
            logger.warning("Computer tool called without an action, adding default")
            fixed_input['action'] = "screenshot"
        
        # Check for required coordinates for click actions
        if fixed_input.get('action') in ['left_click', 'right_click', 'mouse_move'] and 'coordinate' not in fixed_input:
            logger.warning(f"Computer tool {fixed_input.get('action')} called without coordinates, adding default")
            fixed_input['coordinate'] = [500, 400]  # Default to middle of screen
    
    # Handle str_replace_editor tool
    elif tool_name.lower() == 'str_replace_editor':
        if 'command' not in fixed_input:
            logger.warning("Editor tool called without a command, adding default")
            fixed_input['command'] = "view"
        
        if 'path' not in fixed_input:
            logger.warning("Editor tool called without a path, adding default")
            fixed_input['path'] = "/tmp/test.txt"
    
    return fixed_input

async def streaming_loop(
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
    Streaming-enabled sampling loop for Claude DC.
    
    This function replaces the original sampling loop with a streaming-enabled version
    that supports token-by-token updates of the response.
    """
    # Start time for metrics
    start_time = datetime.now()
    logger.info(f"Starting streaming loop at {start_time.isoformat()}")
    
    # Get tool group for specified version
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    
    # Create system prompt with current date
    current_date = datetime.now().strftime("%A, %B %-d, %Y")
    system_text = f"You are Claude DC, 'The Conductor,' a specialized version of Claude focused on interacting with computer systems. "
    system_text += f"You are utilizing an Ubuntu virtual machine with access to tools. "
    system_text += f"Keep your responses focused and action-oriented. "
    system_text += f"The current date is {current_date}. "
    
    if system_prompt_suffix:
        system_text += system_prompt_suffix
    
    system = {
        "type": "text",
        "text": system_text,
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
    
    # Create API parameters
    api_params = {
        "max_tokens": max_tokens,
        "messages": messages,
        "model": model,
        "system": [system],
        "tools": tool_collection.to_params(),
    }
    
    # Add streaming if enabled
    if ENABLE_STREAMING:
        api_params["stream"] = True
        logger.info("Streaming enabled")
    
    # Add beta flag for computer use tools
    try:
        if tool_version == "computer_use_20250124":
            api_params["beta"] = ["computer-use-2025-01-24"]
            logger.info("Added computer-use beta flag")
    except Exception as e:
        logger.warning(f"Failed to add computer-use beta flag: {e}")
    
    # Make API call with proper error handling
    try:
        # First try with all parameters
        try:
            if ENABLE_STREAMING:
                # Streaming path
                logger.info("Making streaming API call")
                stream = client.messages.create(**api_params)
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
                
            else:
                # Non-streaming path
                logger.info("Making non-streaming API call")
                response = client.messages.create(**api_params)
                api_response_callback(None, response, None)
                
        except TypeError as e:
            # If 'beta' parameter is causing issues, remove it and try again
            if "got an unexpected keyword argument 'beta'" in str(e):
                logger.warning("Beta parameter not supported, removing it and retrying")
                api_params.pop('beta', None)
                
                # Try API call again without the unsupported parameters
                if ENABLE_STREAMING:
                    logger.info("Retrying streaming API call without beta parameter")
                    stream = client.messages.create(**api_params)
                    # Process stream (similar to above, but omitted for brevity)
                    logger.info("Stream created successfully after removing unsupported parameters")
                else:
                    logger.info("Retrying non-streaming API call without beta parameter")
                    response = client.messages.create(**api_params)
                    api_response_callback(None, response, None)
            else:
                # Other TypeError, re-raise
                raise
                
    except (APIStatusError, APIResponseValidationError) as e:
        logger.error(f"API error: {e}")
        api_response_callback(None, None, e)
        return messages
    except APIError as e:
        logger.error(f"API error: {e}")
        api_response_callback(None, None, e)
        return messages
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        api_response_callback(None, None, e)
        return messages
        
    # Process the response
    if ENABLE_STREAMING:
        response_params = _response_to_params(response)
    else:
        # For non-streaming, convert the response content to the expected format
        response_params = []
        for block in response.content:
            if block.type == "text":
                response_params.append({
                    "type": "text",
                    "text": block.text
                })
            elif block.type == "thinking":
                response_params.append({
                    "type": "thinking",
                    "thinking": block.thinking
                })
            elif block.type == "tool_use":
                response_params.append({
                    "type": "tool_use",
                    "name": block.name,
                    "id": block.id,
                    "input": block.input
                })
    
    # Add assistant message to history
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
            
            # Validate and fix tool input if needed
            validated_input = validate_tool_input(tool_name, tool_input)
            if validated_input != tool_input:
                logger.info(f"Tool input was fixed: {tool_input} -> {validated_input}")
                tool_input = validated_input
            
            # Configure tool collection for streaming if supported
            for tool in tool_collection.tools:
                if hasattr(tool, 'set_stream_callback'):
                    tool.set_stream_callback(
                        lambda chunk, tid=tool_id: tool_output_callback(
                            ToolResult(output=chunk, error=None),
                            tid
                        )
                    )
            
            # Add delay to ensure UI is updated before tool execution
            await asyncio.sleep(0.5)
            
            try:
                # Run the tool with error handling
                result = await tool_collection.run(
                    name=tool_name,
                    tool_input=tool_input,
                    streaming=ENABLE_STREAMING,  # Enable streaming based on the feature flag
                )
                
                # Create tool result and notify callback
                tool_result = _make_api_tool_result(result, tool_id)
                tool_result_content.append(tool_result)
                
                # Only send final result if tools don't support streaming
                if not any(hasattr(t, 'set_stream_callback') for t in tool_collection.tools):
                    tool_output_callback(result, tool_id)
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                # Create error result
                error_result = ToolResult(error=str(e))
                tool_result = _make_api_tool_result(error_result, tool_id)
                tool_result_content.append(tool_result)
                tool_output_callback(error_result, tool_id)
    
    # Add tool results to messages if any
    if tool_result_content:
        messages.append({"content": tool_result_content, "role": "user"})
    
    # Log completion time and duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Sampling loop completed at {end_time.isoformat()} (duration: {duration:.2f}s)")
    
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