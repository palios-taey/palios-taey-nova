"""
Computer tool implementation for Claude Computer Use.
"""

import os
import asyncio
import base64
import logging
from typing import Dict, Any, Optional, Callable, Union, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("computer_tool")

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

def validate_computer_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the parameters for the computer tool.
    
    Args:
        tool_input: The input parameters for the tool
        
    Returns:
        (is_valid, error_message)
    """
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action", "")
    if not action or not isinstance(action, str):
        return False, "Action must be a non-empty string"
    
    # Validate action-specific parameters
    if action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, "Coordinates must be a list of two integers [x, y]"
        
        if not all(isinstance(coord, int) for coord in coordinates):
            return False, "Coordinates must be integers"
    
    elif action == "type_text":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for type_text"
        
        text = tool_input.get("text")
        if not isinstance(text, str):
            return False, "Text must be a string"
    
    elif action == "press_key":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for press_key"
        
        key = tool_input.get("text")
        if not isinstance(key, str):
            return False, "Key must be a string"
    
    return True, "Valid parameters"

async def execute_computer_tool(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute a computer action.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the output or error
    """
    # Validate parameters
    valid, error_message = validate_computer_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    action = tool_input.get("action", "")
    
    try:
        # Mock implementation for testing
        if progress_callback:
            progress_callback(f"Executing action: {action}")
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Handle different actions
        if action == "screenshot":
            # In a real implementation, take a screenshot
            # For testing, return a mock result
            return ToolResult(
                output="Screenshot captured",
                # In a real implementation, this would be the base64-encoded image
                base64_image=None
            )
        
        elif action == "move_mouse":
            coordinates = tool_input.get("coordinates", [0, 0])
            # In a real implementation, move the mouse
            # For testing, return a mock result
            return ToolResult(output=f"Mouse moved to {coordinates}")
        
        elif action == "left_button_press":
            coordinates = tool_input.get("coordinates", [0, 0])
            # In a real implementation, click the mouse
            # For testing, return a mock result
            return ToolResult(output=f"Mouse clicked at {coordinates}")
        
        elif action == "type_text":
            text = tool_input.get("text", "")
            # In a real implementation, type the text
            # For testing, return a mock result
            return ToolResult(output=f"Typed text: {text}")
        
        elif action == "press_key":
            key = tool_input.get("text", "")
            # In a real implementation, press the key
            # For testing, return a mock result
            return ToolResult(output=f"Pressed key: {key}")
        
        elif action == "wait":
            duration = tool_input.get("duration", 1.0)
            # Wait for the specified duration
            await asyncio.sleep(float(duration))
            return ToolResult(output=f"Waited for {duration} seconds")
        
        else:
            return ToolResult(output=f"Executed {action} (mock implementation)")
        
    except Exception as e:
        logger.error(f"Error executing computer action: {str(e)}")
        return ToolResult(error=f"Error executing action: {str(e)}")

# For testing without asyncio
def execute_computer_sync(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Synchronous version of execute_computer_tool for testing.
    """
    # Validate parameters
    valid, error_message = validate_computer_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    action = tool_input.get("action", "")
    
    try:
        # Handle different actions
        if action == "screenshot":
            return ToolResult(
                output="Screenshot captured",
                base64_image=None
            )
        
        elif action == "move_mouse":
            coordinates = tool_input.get("coordinates", [0, 0])
            return ToolResult(output=f"Mouse moved to {coordinates}")
        
        elif action == "left_button_press":
            coordinates = tool_input.get("coordinates", [0, 0])
            return ToolResult(output=f"Mouse clicked at {coordinates}")
        
        elif action == "type_text":
            text = tool_input.get("text", "")
            return ToolResult(output=f"Typed text: {text}")
        
        elif action == "press_key":
            key = tool_input.get("text", "")
            return ToolResult(output=f"Pressed key: {key}")
        
        else:
            return ToolResult(output=f"Executed {action} (mock implementation)")
        
    except Exception as e:
        logger.error(f"Error executing computer action: {str(e)}")
        return ToolResult(error=f"Error executing action: {str(e)}")

if __name__ == "__main__":
    # Test the tool
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        # Parse parameters from remaining arguments
        params = {"action": action}
        for arg in sys.argv[2:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # Try to parse as JSON if possible
                try:
                    value = json.loads(value)
                except:
                    pass
                params[key] = value
        
        # Execute the action
        result = execute_computer_sync(params)
        
        if result.error:
            print(f"Error: {result.error}")
            sys.exit(1)
        else:
            print(result.output)
    else:
        print("Usage: python computer.py <action> [param=value ...]")
        sys.exit(1)