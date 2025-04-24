"""
Validators for tool parameters.

This module provides functions to validate parameters for each tool type,
ensuring that required parameters are present and have the correct format.
"""

import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("tool_validators")

def validate_computer_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for computer tool.
    
    Args:
        tool_input: The parameters for the computer tool
        
    Returns:
        (is_valid, error_message)
    """
    # Check if action is present
    if "action" not in tool_input:
        return False, "Missing required parameter 'action'"
    
    action = tool_input.get("action")
    
    # Validate action is one of the allowed values
    allowed_actions = [
        "key", "hold_key", "type", "cursor_position", "mouse_move",
        "left_mouse_down", "left_mouse_up", "left_click", "left_click_drag",
        "right_click", "middle_click", "double_click", "triple_click",
        "scroll", "wait", "screenshot"
    ]
    
    if action not in allowed_actions:
        return False, f"Invalid action: {action}. Must be one of {allowed_actions}"
    
    # Validate parameters based on action
    if action in ["mouse_move", "left_click", "right_click", "middle_click", "double_click", "triple_click"]:
        if "coordinate" not in tool_input and action != "cursor_position":
            return False, f"Missing required parameter 'coordinate' for {action}"
        
        coordinate = tool_input.get("coordinate")
        if coordinate is not None:
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                return False, f"Invalid coordinate format for {action}. Expected [x, y], got {coordinate}"
            
            if not all(isinstance(coord, int) for coord in coordinate):
                return False, f"Coordinates must be integers for {action}"
    
    if action == "left_click_drag":
        if "coordinate" not in tool_input:
            return False, "Missing required parameter 'coordinate' for left_click_drag"
        
        if "start_coordinate" not in tool_input:
            return False, "Missing required parameter 'start_coordinate' for left_click_drag"
        
        start_coordinate = tool_input.get("start_coordinate")
        if not isinstance(start_coordinate, list) or len(start_coordinate) != 2:
            return False, f"Invalid start_coordinate format. Expected [x, y], got {start_coordinate}"
        
        if not all(isinstance(coord, int) for coord in start_coordinate):
            return False, "start_coordinate values must be integers"
    
    if action in ["key", "type", "hold_key"]:
        if "text" not in tool_input:
            return False, f"Missing required parameter 'text' for {action}"
        
        text = tool_input.get("text")
        if not isinstance(text, str):
            return False, f"Parameter 'text' must be a string for {action}"
    
    if action in ["hold_key", "wait"]:
        if "duration" not in tool_input:
            return False, f"Missing required parameter 'duration' for {action}"
        
        duration = tool_input.get("duration")
        if not isinstance(duration, (int, float)):
            return False, f"Parameter 'duration' must be a number for {action}"
        
        if duration < 0:
            return False, f"Parameter 'duration' must be non-negative for {action}"
        
        if duration > 60:  # Limit duration to 60 seconds for safety
            return False, f"Parameter 'duration' must be ≤ 60 seconds for {action}"
    
    if action == "scroll":
        if "scroll_direction" not in tool_input:
            return False, "Missing required parameter 'scroll_direction' for scroll"
        
        scroll_direction = tool_input.get("scroll_direction")
        if scroll_direction not in ["up", "down", "left", "right"]:
            return False, f"Invalid scroll_direction: {scroll_direction}. Must be 'up', 'down', 'left', or 'right'"
        
        if "scroll_amount" not in tool_input:
            return False, "Missing required parameter 'scroll_amount' for scroll"
        
        scroll_amount = tool_input.get("scroll_amount")
        if not isinstance(scroll_amount, int) or scroll_amount < 0:
            return False, f"Parameter 'scroll_amount' must be a non-negative integer for scroll"
    
    return True, "Parameters valid"

def validate_bash_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for bash tool.
    
    Args:
        tool_input: The parameters for the bash tool
        
    Returns:
        (is_valid, error_message)
    """
    # If restart is specified, no need for command
    if tool_input.get("restart") is True:
        return True, "Parameters valid"
    
    # Otherwise, command is required
    if "command" not in tool_input:
        return False, "Missing required parameter 'command'"
    
    command = tool_input.get("command")
    if not isinstance(command, str):
        return False, "Parameter 'command' must be a string"
    
    if not command.strip():
        return False, "Parameter 'command' cannot be empty"
    
    return True, "Parameters valid"

def validate_edit_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for str_replace_editor tool.
    
    Args:
        tool_input: The parameters for the editor tool
        
    Returns:
        (is_valid, error_message)
    """
    # Check required parameters
    if "command" not in tool_input:
        return False, "Missing required parameter 'command'"
    
    if "path" not in tool_input:
        return False, "Missing required parameter 'path'"
    
    command = tool_input.get("command")
    allowed_commands = ["view", "create", "str_replace", "insert", "undo_edit"]
    
    if command not in allowed_commands:
        return False, f"Invalid command: {command}. Must be one of {allowed_commands}"
    
    path = tool_input.get("path")
    if not isinstance(path, str) or not path:
        return False, "Parameter 'path' must be a non-empty string"
    
    # Validate command-specific parameters
    if command == "create":
        if "file_text" not in tool_input:
            return False, "Missing required parameter 'file_text' for command 'create'"
    
    if command == "str_replace":
        if "old_str" not in tool_input:
            return False, "Missing required parameter 'old_str' for command 'str_replace'"
    
    if command == "insert":
        if "insert_line" not in tool_input:
            return False, "Missing required parameter 'insert_line' for command 'insert'"
        
        if "new_str" not in tool_input:
            return False, "Missing required parameter 'new_str' for command 'insert'"
        
        insert_line = tool_input.get("insert_line")
        if not isinstance(insert_line, int):
            return False, "Parameter 'insert_line' must be an integer"
    
    # Validate view_range if provided
    if "view_range" in tool_input:
        view_range = tool_input.get("view_range")
        if not isinstance(view_range, list) or len(view_range) != 2:
            return False, "Parameter 'view_range' must be a list of two integers"
        
        if not all(isinstance(val, int) for val in view_range):
            return False, "Values in 'view_range' must be integers"
    
    return True, "Parameters valid"