"""
Tool Registry for Claude DC.

This module provides a centralized registry for all tools available to Claude DC,
including their definitions, executors, and validators.
"""

import logging
from typing import Dict, Any, List, Optional

from .models import ToolInfo, ToolRegistry

# Configure logging
logger = logging.getLogger("tool_registry")

# Initialize an empty registry
_registry: ToolRegistry = {}

# Tool definitions with their schema
COMPUTER_USE_TOOL = {
    "name": "computer",
    "description": "Use a mouse and keyboard to interact with a computer, and take screenshots",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "key", "hold_key", "type", "cursor_position", "mouse_move",
                    "left_mouse_down", "left_mouse_up", "left_click", "left_click_drag",
                    "right_click", "middle_click", "double_click", "triple_click",
                    "scroll", "wait", "screenshot"
                ],
                "description": "The action to perform"
            },
            "coordinate": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The x,y coordinates for actions that require a position"
            },
            "text": {
                "type": "string", 
                "description": "The text to type or key to press"
            },
            "duration": {
                "type": "number",
                "description": "Duration in seconds for actions like hold_key or wait"
            },
            "scroll_direction": {
                "type": "string",
                "enum": ["up", "down", "left", "right"],
                "description": "Direction to scroll"
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Amount to scroll"
            },
            "start_coordinate": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Starting coordinates for drag operations"
            }
        },
        "required": ["action"]
    }
}

BASH_TOOL = {
    "name": "bash",
    "description": "Run commands in a bash shell",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to run"
            },
            "restart": {
                "type": "boolean",
                "description": "Whether to restart the bash session"
            }
        },
        "required": ["command"]
    }
}

TEXT_EDITOR_TOOL = {
    "name": "str_replace_editor", 
    "description": "Custom editing tool for viewing, creating and editing files",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                "description": "The command to execute"
            },
            "path": {
                "type": "string",
                "description": "Absolute path to file or directory"
            },
            "file_text": {
                "type": "string",
                "description": "Required for create command, with the content of the file"
            },
            "old_str": {
                "type": "string",
                "description": "For str_replace command, the string to replace"
            },
            "new_str": {
                "type": "string",
                "description": "For str_replace or insert command, the new string"
            },
            "insert_line": {
                "type": "integer",
                "description": "For insert command, the line where to insert"
            },
            "view_range": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional range of lines to view"
            }
        },
        "required": ["command", "path"]
    }
}

def register_tool(
    name: str,
    definition: Dict[str, Any],
    executor,
    validator,
    description: str = ""
) -> None:
    """
    Register a tool in the registry.
    
    Args:
        name: The unique name of the tool
        definition: The tool definition for the Anthropic API
        executor: Function that executes the tool
        validator: Function that validates tool parameters
        description: A human-readable description of the tool
    """
    if name in _registry:
        logger.warning(f"Tool '{name}' already registered, overwriting")
    
    _registry[name] = ToolInfo(
        name=name,
        definition=definition,
        executor=executor,
        validator=validator,
        description=description
    )
    logger.info(f"Tool '{name}' registered successfully")

def get_tool(name: str) -> Optional[ToolInfo]:
    """
    Get a tool from the registry by name.
    
    Args:
        name: The name of the tool to retrieve
        
    Returns:
        The tool info if found, None otherwise
    """
    return _registry.get(name)

def get_all_tools() -> List[ToolInfo]:
    """
    Get all registered tools.
    
    Returns:
        List of all registered tools
    """
    return list(_registry.values())

def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get all tool definitions for the Anthropic API.
    
    Returns:
        List of tool definitions
    """
    return [tool.definition for tool in _registry.values()]

def is_tool_registered(name: str) -> bool:
    """
    Check if a tool is registered.
    
    Args:
        name: The name of the tool to check
        
    Returns:
        True if the tool is registered, False otherwise
    """
    return name in _registry