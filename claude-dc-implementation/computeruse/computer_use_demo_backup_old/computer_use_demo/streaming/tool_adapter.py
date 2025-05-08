"""
Tool adapter for the streaming implementation.

This module provides adapters between the original tool implementation and
the streaming-compatible tools, ensuring proper parameter mapping and validation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streaming_tool_adapter")

def validate_tool_input(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and potentially fix tool inputs.
    
    Args:
        tool_name: The name of the tool to validate input for
        tool_input: The input parameters for the tool
        
    Returns:
        Dict with validated and potentially fixed inputs
    """
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
    
    # Handle edit tool
    elif tool_name.lower() == 'edit':
        if 'file_path' not in fixed_input:
            logger.warning("Edit tool called without a file_path, adding default")
            fixed_input['file_path'] = "/tmp/example.txt"
            
        if 'content' not in fixed_input and 'old_text' not in fixed_input:
            logger.warning("Edit tool called without content or old_text, adding defaults")
            fixed_input['content'] = ""
    
    # Add other tool validations as needed
    
    return fixed_input

async def map_and_execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    original_executor: Callable[[str, Dict[str, Any]], Awaitable[Any]],
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Map tool input to the appropriate format, execute the tool with progress reporting.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        original_executor: The original tool execution function
        progress_callback: Optional callback for reporting progress
        
    Returns:
        Dict with the tool execution result
    """
    # Validate and fix input
    validated_input = validate_tool_input(tool_name, tool_input)
    
    # Report start of tool execution
    if progress_callback:
        progress_callback(f"Executing tool: {tool_name}")
    
    try:
        # Check if we should use streaming-specific implementation
        from ..streaming_integration import is_feature_enabled
        
        if tool_name.lower() == 'bash' and is_feature_enabled("use_streaming_bash"):
            # Use streaming bash implementation
            from .tools.dc_bash import execute_bash_with_streaming
            result = await execute_bash_with_streaming(
                validated_input, progress_callback=progress_callback
            )
            return {"output": result.output, "error": result.error}
            
        elif tool_name.lower() in ['read', 'write', 'edit'] and is_feature_enabled("use_streaming_file"):
            # Use streaming file implementation
            from .tools.dc_file import execute_file_operation_with_streaming
            result = await execute_file_operation_with_streaming(
                tool_name, validated_input, progress_callback=progress_callback
            )
            return {"output": result.output, "error": result.error}
            
        else:
            # Fall back to original implementation for other tools
            result = await original_executor(tool_name, validated_input)
            
            # Report completion
            if progress_callback:
                progress_callback(f"Tool execution complete: {tool_name}")
                
            return result
            
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        if progress_callback:
            progress_callback(f"Tool execution error: {str(e)}")
        return {"error": f"Tool execution error: {str(e)}"}