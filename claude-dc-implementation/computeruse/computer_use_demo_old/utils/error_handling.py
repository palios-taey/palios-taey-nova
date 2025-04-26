"""
Error handling utilities for API and tool errors.

This module provides consistent error handling for API errors, tool errors,
and other exceptions that may occur during agent operation.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Union

# Import models
from models.tool_models import ToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("error_handling")

def handle_api_error(error: Exception) -> Dict[str, Any]:
    """
    Handle API errors from the Anthropic API.
    
    This function logs the error and returns a user-friendly error message
    that can be displayed to the user.
    
    Args:
        error: The exception raised by the API
        
    Returns:
        Error message dict for conversation history
    """
    # Log the error
    logger.error(f"API error: {str(error)}")
    logger.error(traceback.format_exc())
    
    # Determine error type and provide appropriate message
    error_str = str(error).lower()
    
    if "rate limit" in error_str or "429" in error_str:
        # Rate limit error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "I'm currently receiving too many requests. Please wait a moment before trying again."
            }]
        }
    elif "token" in error_str or "authentication" in error_str or "auth" in error_str:
        # Authentication error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "There was an issue with API authentication. Please check your API key."
            }]
        }
    elif "context window" in error_str or "tokens" in error_str or "max_tokens" in error_str:
        # Token limit error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "The conversation has become too long for me to process. Please try starting a new conversation."
            }]
        }
    elif "timeout" in error_str or "timed out" in error_str:
        # Timeout error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "The request timed out. Please try again or try a shorter message."
            }]
        }
    elif "service" in error_str or "server" in error_str:
        # Server error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "I'm experiencing technical difficulties. Please try again in a few moments."
            }]
        }
    else:
        # Generic error
        message = {
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": f"I encountered an error: {str(error)}"
            }]
        }
    
    return message

def handle_tool_error(tool_name: str, error: Exception) -> ToolResult:
    """
    Handle errors that occur during tool execution.
    
    This function logs the error and returns a ToolResult with an appropriate
    error message.
    
    Args:
        tool_name: The name of the tool that raised the error
        error: The exception raised by the tool
        
    Returns:
        ToolResult with error information
    """
    # Log the error
    logger.error(f"Tool error in {tool_name}: {str(error)}")
    logger.error(traceback.format_exc())
    
    # Determine error type and provide appropriate message
    error_str = str(error).lower()
    
    if "permission" in error_str or "access" in error_str:
        # Permission error
        return ToolResult(
            error=f"I don't have permission to perform this operation: {str(error)}"
        )
    elif "not found" in error_str or "no such" in error_str:
        # Not found error
        return ToolResult(
            error=f"The requested resource could not be found: {str(error)}"
        )
    elif "timeout" in error_str or "timed out" in error_str:
        # Timeout error
        return ToolResult(
            error=f"The operation timed out: {str(error)}"
        )
    elif "invalid" in error_str or "format" in error_str or "syntax" in error_str:
        # Invalid input error
        return ToolResult(
            error=f"Invalid input for tool {tool_name}: {str(error)}"
        )
    else:
        # Generic error
        return ToolResult(
            error=f"Error executing tool {tool_name}: {str(error)}"
        )

def format_exception(error: Exception) -> str:
    """
    Format an exception into a user-friendly error message.
    
    Args:
        error: The exception to format
        
    Returns:
        Formatted error message
    """
    # Get the exception type
    error_type = type(error).__name__
    
    # Get the error message
    error_message = str(error)
    
    # Format the error
    return f"{error_type}: {error_message}"