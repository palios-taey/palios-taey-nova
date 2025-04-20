"""
Utility functions for the streaming tests.
Contains helper functions for parsing and logging streaming events.
"""

import logging
import json
from typing import Any, Dict, List, Optional
import inspect

from .stream_config import logger

def log_event(event_type: str, data: Any) -> None:
    """Log an event with detailed information."""
    logger.info(f"EVENT [{event_type}]: {data}")
    
def log_api_call(params: Dict[str, Any]) -> None:
    """Log API call parameters, excluding sensitive data."""
    # Create a copy to avoid modifying the original
    safe_params = params.copy()
    
    # Remove sensitive or large data
    if "messages" in safe_params:
        msg_count = len(safe_params["messages"])
        safe_params["messages"] = f"[{msg_count} messages - content omitted]"
    
    if "system" in safe_params:
        safe_params["system"] = "[system prompt omitted]"
    
    if "api_key" in safe_params:
        safe_params["api_key"] = "[redacted]"
    
    # Log the safe parameters
    logger.info(f"API CALL: {json.dumps(safe_params, indent=2)}")

def log_response(content_block: Dict[str, Any], is_delta: bool = False) -> None:
    """Log response content with appropriate formatting."""
    block_type = content_block.get("type", "unknown")
    
    if block_type == "text":
        text = content_block.get("text", "")
        if is_delta:
            logger.info(f"DELTA TEXT: {text}")
        else:
            logger.info(f"FULL TEXT: {text}")
    
    elif block_type == "thinking":
        thinking = content_block.get("thinking", "")
        if is_delta:
            logger.info(f"DELTA THINKING: {thinking}")
        else:
            logger.info(f"FULL THINKING: {thinking}")
    
    elif block_type == "tool_use":
        name = content_block.get("name", "unknown")
        input_data = content_block.get("input", {})
        logger.info(f"TOOL USE: {name} with input: {input_data}")
    
    else:
        # Unknown block type - log everything
        logger.info(f"UNKNOWN BLOCK: {json.dumps(content_block, indent=2)}")

def log_tool_result(result: Any, tool_id: str) -> None:
    """Log tool execution results."""
    # Get the attributes of the result object
    if hasattr(result, "output"):
        output = result.output
        logger.info(f"TOOL RESULT [{tool_id}]: {output}")
    
    if hasattr(result, "error") and result.error:
        error = result.error
        logger.warning(f"TOOL ERROR [{tool_id}]: {error}")
    
    if hasattr(result, "base64_image") and result.base64_image:
        logger.info(f"TOOL IMAGE [{tool_id}]: [base64 image data omitted]")

def log_function_entry_exit(func):
    """Decorator to log function entry and exit for debugging."""
    def wrapper(*args, **kwargs):
        logger.info(f"ENTER: {func.__name__}")
        
        # Get parameter values
        params = inspect.signature(func).parameters
        param_values = {}
        
        # Combine positional and keyword arguments
        for i, (param_name, param) in enumerate(params.items()):
            if i < len(args):
                # Handle positional args
                if param_name != 'self':  # Skip self for methods
                    param_values[param_name] = args[i] if param_name != 'api_key' else '[redacted]'
            elif param_name in kwargs:
                # Handle keyword args
                param_values[param_name] = kwargs[param_name] if param_name != 'api_key' else '[redacted]'
        
        logger.info(f"PARAMS: {json.dumps(str(param_values), indent=2)}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"EXIT: {func.__name__} (success)")
            return result
        except Exception as e:
            logger.error(f"EXIT: {func.__name__} (error: {str(e)})")
            raise
    
    return wrapper