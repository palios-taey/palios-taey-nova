"""
Tool executor with resilience features.

This module provides functions to execute tools with fallback mechanisms
and comprehensive error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from .models import ToolResult
from .registry import get_tool

# Configure logging
logger = logging.getLogger("tool_executor")

async def execute_tool(
    tool_name: str, 
    tool_input: Dict[str, Any],
    max_retries: int = 1
) -> ToolResult:
    """
    Execute a tool with resilience features.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        max_retries: Maximum number of retry attempts (default: 1)
        
    Returns:
        ToolResult containing the output, error, or image data
    """
    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
    
    # Get tool from registry
    tool_info = get_tool(tool_name)
    if not tool_info:
        error_msg = f"Unknown tool: {tool_name}"
        logger.error(error_msg)
        return ToolResult(error=error_msg)
    
    # Validate parameters
    valid, error_msg = tool_info.validator(tool_input)
    if not valid:
        logger.error(f"Invalid parameters for {tool_name}: {error_msg}")
        return ToolResult(error=f"Invalid parameters: {error_msg}")
    
    # Execute with fallback
    return await execute_with_fallback(
        tool_name, 
        tool_input, 
        tool_info.executor,
        max_retries=max_retries
    )

async def execute_with_fallback(
    tool_name: str, 
    tool_input: Dict[str, Any], 
    executor,
    max_retries: int = 1
) -> ToolResult:
    """
    Execute a tool with retry logic and fallback strategies.
    
    Args:
        tool_name: The name of the tool being executed
        tool_input: The input parameters for the tool
        executor: The function to execute the tool
        max_retries: Maximum number of retry attempts
        
    Returns:
        ToolResult containing the output, error, or image data
    """
    retries = 0
    last_error = None
    start_time = time.time()
    
    # Create a copy of the original input for potential modifications
    current_input = tool_input.copy()
    
    while retries <= max_retries:
        try:
            # Add execution attempt to log
            attempt_msg = f"Executing {tool_name} (attempt {retries+1}/{max_retries+1})"
            logger.info(attempt_msg)
            
            # Execute the tool
            result = await executor(current_input)
            
            # If successful or we've reached max retries, return the result
            if not result.has_error() or retries >= max_retries:
                execution_time = time.time() - start_time
                logger.info(f"Tool {tool_name} executed in {execution_time:.2f}s after {retries+1} attempts")
                return result
            
            # Log the error
            last_error = result.error
            logger.warning(f"Tool {tool_name} execution failed: {last_error}")
            
        except Exception as e:
            # Log the exception
            last_error = str(e)
            logger.error(f"Tool {tool_name} execution raised exception: {last_error}")
        
        # Apply fallback strategy for specific tools
        current_input = apply_fallback_strategy(tool_name, current_input, last_error, retries)
        
        # Wait before retry with increasing backoff
        retry_delay = 0.5 * (2 ** retries)  # Exponential backoff
        logger.info(f"Waiting {retry_delay:.2f}s before retry")
        await asyncio.sleep(retry_delay)
        
        # Increment retry counter
        retries += 1
    
    # If we've exhausted all retries, return the last error
    return ToolResult(error=f"Tool execution failed after {max_retries+1} attempts: {last_error}")

def apply_fallback_strategy(
    tool_name: str, 
    tool_input: Dict[str, Any], 
    error: Optional[str],
    retry_count: int
) -> Dict[str, Any]:
    """
    Apply a fallback strategy based on the tool, input, and error.
    
    Args:
        tool_name: The name of the tool
        tool_input: The original tool input
        error: The error message from the previous attempt
        retry_count: The current retry count
        
    Returns:
        Modified tool input for the next attempt
    """
    # Create a copy of the input to modify
    modified_input = tool_input.copy()
    
    # Apply tool-specific fallback strategies
    if tool_name == "computer":
        action = tool_input.get("action")
        
        # For screenshot failures, no special handling needed
        if action == "screenshot":
            logger.info("Using default screenshot fallback strategy")
            
        # For click actions, slightly adjust coordinates if provided
        elif action in ["left_click", "right_click", "double_click"]:
            if "coordinate" in tool_input and isinstance(tool_input["coordinate"], list):
                # Add a small offset to coordinates (5 pixels in each direction)
                offset = 5 if retry_count == 0 else -5
                modified_input["coordinate"] = [
                    tool_input["coordinate"][0] + offset,
                    tool_input["coordinate"][1] + offset
                ]
                logger.info(f"Adjusted coordinates for {action} to {modified_input['coordinate']}")
        
        # For text input failures, try sending smaller chunks
        elif action == "type" and "text" in tool_input:
            if len(tool_input["text"]) > 20:
                # Truncate text to first 20 chars on first retry
                modified_input["text"] = tool_input["text"][:20]
                logger.info(f"Truncated text for retry: '{modified_input['text']}'")
    
    # For bash command failures, try simplifying or prefixing with error handling
    elif tool_name == "bash" and "command" in tool_input:
        command = tool_input["command"]
        
        # For first retry, add error handling to the command
        if retry_count == 0 and not command.startswith("set -e"):
            modified_input["command"] = f"set -e; {command}"
            logger.info(f"Added error handling to bash command: {modified_input['command']}")
            
        # For second retry, try simplified command or with timeout
        elif retry_count == 1 and not command.startswith("timeout"):
            modified_input["command"] = f"timeout 10 {command}"
            logger.info(f"Added timeout to bash command: {modified_input['command']}")
    
    # For str_replace_editor, adjust behavior based on the command
    elif tool_name == "str_replace_editor":
        command = tool_input.get("command")
        
        # For view command failures, try viewing smaller ranges
        if command == "view" and "view_range" in tool_input:
            # Simplify to just view the file without range
            modified_input.pop("view_range", None)
            logger.info("Removed view_range for str_replace_editor retry")
        
        # For str_replace failures, no specific fallback
        elif command == "str_replace":
            logger.info("Using default str_replace fallback strategy")
    
    logger.info(f"Applied fallback strategy for {tool_name} on retry {retry_count+1}")
    return modified_input