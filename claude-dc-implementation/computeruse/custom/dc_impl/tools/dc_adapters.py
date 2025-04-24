"""
Tool adapters with namespace isolation for safely integrating with production tools.
"""

import logging
import time
from typing import Dict, Any

# Import from our namespace-isolated modules
from ..models.dc_models import DCToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_tool_adapters")

# Mock implementations for safe development and testing
async def dc_execute_computer_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Safe adapter for computer tool implementation with namespace isolation.
    """
    logger.info(f"DC Computer Tool - Action: {tool_input.get('action')}")
    action = tool_input.get("action")
    
    # Safe mock implementation
    if action == "screenshot":
        logger.info("Taking mock screenshot")
        return DCToolResult(output="Mock screenshot taken")
    elif action == "move_mouse":
        coordinates = tool_input.get("coordinates", [0, 0])
        logger.info(f"Moving mock mouse to: {coordinates}")
        return DCToolResult(output=f"Mock mouse moved to {coordinates}")
    elif action == "type_text":
        text = tool_input.get("text", "")
        logger.info(f"Typing mock text: {text}")
        return DCToolResult(output=f"Mock text typed: {text}")
    else:
        return DCToolResult(output=f"Mock {action} executed")

async def dc_execute_bash_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Safe adapter for bash tool implementation with namespace isolation.
    """
    logger.info(f"DC Bash Tool - Command: {tool_input.get('command')}")
    command = tool_input.get("command", "")
    
    # Safe mock implementation
    if not command:
        return DCToolResult(error="Empty command")
    
    # Simulate command execution safely
    logger.info(f"Executing mock command: {command}")
    
    # Mock responses for common commands
    if command.startswith("ls"):
        return DCToolResult(output="file1.txt\nfile2.txt\ndirectory1/")
    elif command.startswith("echo"):
        return DCToolResult(output=command[5:])  # Echo the text after "echo "
    elif command.startswith("pwd"):
        return DCToolResult(output="/mock/current/directory")
    else:
        return DCToolResult(output=f"Mock execution of: {command}")

# Validator functions for parameter validation
def dc_validate_computer_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate computer tool parameters with namespace isolation.
    """
    # Check for required action parameter
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action")
    
    # Validate parameters based on action
    if action in ["move_mouse", "left_button_press"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, "Invalid coordinates format. Expected [x, y]"
    
    elif action == "type_text":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for type_text"
    
    return True, "Parameters valid"

def dc_validate_bash_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate bash tool parameters with namespace isolation.
    """
    # Check for required command parameter
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    return True, "Parameters valid"