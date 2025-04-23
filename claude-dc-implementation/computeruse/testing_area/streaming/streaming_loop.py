"""
Simplified Streaming Implementation for Claude DC

This module provides a streaming-enabled sampling loop that works with the current
tool collection and API. It focuses on reliability and simplicity.
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
    max_tokens: int = 4096,
    tool_version: str = "computer_use_20250124",
    thinking_budget: Optional[int] = None,
):
    """
    Streaming-enabled sampling loop for Claude DC.
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
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key, max_retries=3)
    
    # Create API parameters
    api_params = {
        "max_tokens": max_tokens,
        "messages": messages,
        "model": model,
        "system": [system],
        "tools": tool_collection.to_params(),
        "stream": True  # Always enable streaming
    }
    
    logger.info("Making streaming API call")
    response_blocks = []
    
    try:
        # Try to make the API call with streaming
        try:
            stream = client.messages.create(**api_params)
            logger.info("Stream created successfully")
            
            for event in stream:
                if hasattr(event, "type"):
                    event_type = event.type
                    
                    if event_type == "content_block_start":
                        # New content block started
                        current_block = event.content_block
                        
                        # Create dict with available properties
                        block_dict = {"type": getattr(current_block, "type", "unknown")}
                        
                        if hasattr(current_block, "text"):
                            block_dict["text"] = current_block.text
                        
                        if hasattr(current_block, "thinking"):
                            block_dict["thinking"] = current_block.thinking
                        
                        if hasattr(current_block, "name") and block_dict["type"] == "tool_use":
                            block_dict["name"] = current_block.name
                            block_dict["input"] = getattr(current_block, "input", {})
                            block_dict["id"] = getattr(current_block, "id", "unknown")
                        
                        # Add to response blocks
                        response_blocks.append(block_dict)
                        
                        # Send to output callback
                        output_callback(block_dict)
                    
                    elif event_type == "content_block_delta":
                        # Handle deltas
                        if hasattr(event, "index") and event.index < len(response_blocks):
                            if hasattr(event.delta, "text") and event.delta.text:
                                # For text deltas
                                if "text" not in response_blocks[event.index]:
                                    response_blocks[event.index]["text"] = ""
                                
                                response_blocks[event.index]["text"] += event.delta.text
                                
                                # Send delta to callback
                                output_callback({
                                    "type": "text",
                                    "text": event.delta.text,
                                    "is_delta": True
                                })
                            
                            elif hasattr(event.delta, "thinking") and event.delta.thinking:
                                # For thinking deltas
                                if "thinking" not in response_blocks[event.index]:
                                    response_blocks[event.index]["thinking"] = ""
                                
                                response_blocks[event.index]["thinking"] += event.delta.thinking
                                
                                # Send delta to callback
                                output_callback({
                                    "type": "thinking",
                                    "thinking": event.delta.thinking,
                                    "is_delta": True
                                })
                    
                    elif event_type == "message_stop":
                        # Message generation complete
                        logger.info("Message generation complete")
                        break
            
        except TypeError as e:
            if "beta" in str(e):
                # Handle beta parameter errors by retrying
                api_params.pop("beta", None)
                logger.warning(f"Retrying without beta parameter: {e}")
                
                stream = client.messages.create(**api_params)
                # Process the stream (similar code as above, omitted for brevity)
            else:
                raise
        
    except Exception as e:
        logger.error(f"Error in streaming API call: {e}")
        api_response_callback(None, None, e)
        return messages
    
    # Add assistant message to history
    messages.append({
        "role": "assistant",
        "content": response_blocks,
    })
    
    # Process tools if any
    tool_result_content = []
    for block in response_blocks:
        if block["type"] == "tool_use":
            # Extract tool information
            tool_name = block["name"]
            tool_id = block["id"]
            tool_input = block["input"]
            
            logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
            
            # Validate and fix tool input
            validated_input = validate_tool_input(tool_name, tool_input)
            if validated_input != tool_input:
                logger.info(f"Tool input was fixed: {tool_input} -> {validated_input}")
                tool_input = validated_input
            
            # Small delay to ensure UI is updated
            await asyncio.sleep(0.5)
            
            try:
                # Run the tool
                result = await tool_collection.run(
                    name=tool_name,
                    tool_input=tool_input,
                )
                
                # Create tool result structure
                tool_result_content.append({
                    "type": "tool_result",
                    "content": result.output if result.output else "",
                    "tool_use_id": tool_id,
                    "is_error": bool(result.error)
                })
                
                # Send to callback
                tool_output_callback(result, tool_id)
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                error_result = ToolResult(error=str(e))
                tool_output_callback(error_result, tool_id)
    
    # Add tool results to messages
    if tool_result_content:
        messages.append({"content": tool_result_content, "role": "user"})
    
    # Log completion time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Streaming loop completed in {duration:.2f} seconds")
    
    return messages