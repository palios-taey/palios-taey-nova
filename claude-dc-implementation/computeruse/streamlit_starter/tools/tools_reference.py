"""
Reference implementations for streaming-compatible tools.
These implementations provide proper validation and error handling.
"""
from typing import Dict, Any, Optional, Callable, List, Union, Tuple
import asyncio
import json
import logging
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tools_reference")

class ToolResult:
    """Container for tool execution results"""
    def __init__(self, 
                 output: Optional[str] = None, 
                 error: Optional[str] = None, 
                 base64_image: Optional[str] = None):
        self.output = output
        self.error = error
        self.base64_image = base64_image
    
    def __str__(self):
        if self.error:
            return f"Error: {self.error}"
        return self.output or ""

def validate_computer_tool_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate parameters for computer tool.
    
    Args:
        tool_input: The input parameters for the tool
        
    Returns:
        Tuple containing:
        - Boolean indicating if validation passed
        - Error message if validation failed, None otherwise
    """
    # Check if action is provided
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action")
    
    # Validate parameters for specific actions
    if action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, f"'coordinates' parameter must be a list of 2 integers"
        
        try:
            x, y = coordinates
            if not isinstance(x, int) or not isinstance(y, int):
                return False, f"'coordinates' must contain integer values"
        except (ValueError, TypeError):
            return False, f"Invalid 'coordinates' format: {coordinates}"
    
    # Validate text parameter for text input actions
    if action in ["type_text"]:
        if "text" not in tool_input:
            return False, f"Missing required 'text' parameter for {action}"
        
        text = tool_input.get("text")
        if not isinstance(text, str):
            return False, f"'text' parameter must be a string"
    
    # Validate parameter for press_key action
    if action == "press_key":
        if "text" not in tool_input:
            return False, f"Missing required 'text' parameter for {action}"
    
    # All validations passed
    return True, None

def validate_bash_tool_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate parameters for bash tool.
    
    Args:
        tool_input: The input parameters for the tool
        
    Returns:
        Tuple containing:
        - Boolean indicating if validation passed
        - Error message if validation failed, None otherwise
    """
    # Check if command is provided
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command")
    
    # Validate command is a string
    if not isinstance(command, str):
        return False, "'command' parameter must be a string"
    
    # Validate command is not empty
    if not command.strip():
        return False, "'command' parameter cannot be empty"
    
    # All validations passed
    return True, None

async def execute_computer_tool_with_validation(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute computer tool with parameter validation.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the result of the operation
    """
    # Validate parameters first
    is_valid, error_message = validate_computer_tool_parameters(tool_input)
    if not is_valid:
        return ToolResult(error=error_message)
    
    # Parameters are valid, proceed with execution
    try:
        action = tool_input.get("action")
        
        # Implement specific actions
        if action == "screenshot":
            if progress_callback:
                progress_callback("Taking screenshot...")
            
            # Actual implementation would call the real screenshot function
            # For demo purposes, we'll simulate a delay and return a placeholder
            await asyncio.sleep(0.5)
            
            # In a real implementation, this would be the base64-encoded screenshot
            fake_base64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA"
            
            return ToolResult(
                output="Screenshot taken successfully",
                base64_image=fake_base64
            )
            
        elif action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up"]:
            coordinates = tool_input.get("coordinates")
            x, y = coordinates
            
            if progress_callback:
                progress_callback(f"Executing {action} at coordinates ({x}, {y})...")
            
            # Simulate execution
            await asyncio.sleep(0.3)
            
            return ToolResult(output=f"Executed {action} at coordinates ({x}, {y})")
            
        elif action in ["type_text", "press_key"]:
            text = tool_input.get("text")
            
            if progress_callback:
                progress_callback(f"Executing {action} with '{text}'...")
            
            # Simulate execution
            await asyncio.sleep(0.2)
            
            return ToolResult(output=f"Executed {action} with '{text}'")
            
        else:
            # Handle other actions
            if progress_callback:
                progress_callback(f"Executing {action}...")
            
            # Simulate execution
            await asyncio.sleep(0.2)
            
            return ToolResult(output=f"Executed {action}")
            
    except Exception as e:
        logger.error(f"Error executing computer tool: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")

async def execute_bash_tool_with_validation(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute bash tool with parameter validation.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the result of the operation
    """
    # Validate parameters first
    is_valid, error_message = validate_bash_tool_parameters(tool_input)
    if not is_valid:
        return ToolResult(error=error_message)
    
    # Parameters are valid, proceed with execution
    try:
        command = tool_input.get("command")
        
        if progress_callback:
            progress_callback(f"Executing command: {command}")
        
        # In a real implementation, this would execute the command safely
        # For demo purposes, we'll simulate command execution
        await asyncio.sleep(0.5)
        
        # Simple command result simulation based on command
        if command.startswith("ls"):
            result = "file1.txt\nfile2.py\ndirectory1/\ndirectory2/"
        elif command.startswith("echo"):
            result = command.replace("echo ", "")
        elif command.startswith("pwd"):
            result = "/home/user/documents"
        else:
            result = f"Executed: {command}"
        
        return ToolResult(output=result)
        
    except Exception as e:
        logger.error(f"Error executing bash tool: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")

# Example usage:
"""
# Example computer tool execution with validation
result = await execute_computer_tool_with_validation(
    {"action": "screenshot"},
    progress_callback=lambda msg: print(f"Progress: {msg}")
)
print(result)

# Example bash tool execution with validation
result = await execute_bash_tool_with_validation(
    {"command": "ls -la"},
    progress_callback=lambda msg: print(f"Progress: {msg}")
)
print(result)
"""