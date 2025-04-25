"""
Tool registry for maintaining tool definitions, executors, and validators.

This module provides a centralized registry for all tools, including their
definitions, executors, and validators. It allows tools to be registered
and retrieved in a consistent manner.
"""

import logging
from typing import Dict, List, Any, Callable, Awaitable, Tuple, Optional
import importlib

from models.tool_models import ToolInfo, ToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tool_registry")

# Global tool registry
TOOL_REGISTRY: Dict[str, ToolInfo] = {}

# Tool definitions
COMPUTER_TOOL = {
    "name": "computer",
    "description": "Control a computer by taking actions like mouse clicks, keyboard input, and taking screenshots",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "screenshot", "left_button_press", "move_mouse", "type_text",
                    "press_key", "hold_key", "left_mouse_down", "left_mouse_up",
                    "scroll", "triple_click", "wait"
                ],
                "description": "The action to perform"
            },
            "coordinates": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "The x and y coordinates for mouse actions"
            },
            "text": {
                "type": "string",
                "description": "The text to type or the key to press"
            }
        },
        "required": ["action"]
    }
}

BASH_TOOL = {
    "name": "bash",
    "description": "Execute bash commands on the system",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            }
        },
        "required": ["command"]
    }
}

EDIT_TOOL = {
    "name": "str_replace_editor",
    "description": "View, create, and edit files on the system",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                "description": "The file operation to perform"
            },
            "path": {
                "type": "string",
                "description": "The file path to operate on"
            },
            "old_string": {
                "type": "string",
                "description": "The string to replace (for str_replace)"
            },
            "new_string": {
                "type": "string",
                "description": "The replacement string (for str_replace)"
            },
            "expected_replacements": {
                "type": "integer",
                "description": "The expected number of replacements (for str_replace)"
            },
            "content": {
                "type": "string",
                "description": "The content to write (for create or insert)"
            },
            "position": {
                "type": "string",
                "description": "Where to insert content (for insert): start, end, or line number"
            }
        },
        "required": ["command", "path"]
    }
}

def register_tool(
    name: str,
    definition: Dict[str, Any],
    executor: Callable[[Dict[str, Any], Optional[Callable]], Awaitable[ToolResult]],
    validator: Callable[[Dict[str, Any]], Tuple[bool, str]],
    streaming: bool = False
) -> None:
    """
    Register a tool in the registry.
    
    Args:
        name: The name of the tool
        definition: The tool definition for Claude API
        executor: Function that executes the tool
        validator: Function that validates tool parameters
        streaming: Whether the tool supports streaming
    """
    global TOOL_REGISTRY
    TOOL_REGISTRY[name] = ToolInfo(
        definition=definition,
        executor=executor,
        validator=validator,
        streaming=streaming
    )
    logger.info(f"Registered tool: {name} (streaming: {streaming})")

def get_tool_registry() -> Dict[str, ToolInfo]:
    """
    Get the tool registry.
    
    Returns:
        The tool registry
    """
    return TOOL_REGISTRY

def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get all tool definitions for the Claude API.
    
    Returns:
        List of tool definitions
    """
    return [tool_info.definition for tool_info in TOOL_REGISTRY.values()]

def get_tool_executor(tool_name: str) -> Optional[Callable]:
    """
    Get the executor for a specific tool.
    
    Args:
        tool_name: The name of the tool
        
    Returns:
        The tool executor function, or None if not found
    """
    if tool_name not in TOOL_REGISTRY:
        return None
    return TOOL_REGISTRY[tool_name].executor

def get_tool_validator(tool_name: str) -> Optional[Callable]:
    """
    Get the validator for a specific tool.
    
    Args:
        tool_name: The name of the tool
        
    Returns:
        The tool validator function, or None if not found
    """
    if tool_name not in TOOL_REGISTRY:
        return None
    return TOOL_REGISTRY[tool_name].validator

def tool_is_streaming(tool_name: str) -> bool:
    """
    Check if a tool supports streaming.
    
    Args:
        tool_name: The name of the tool
        
    Returns:
        True if the tool supports streaming, False otherwise
    """
    if tool_name not in TOOL_REGISTRY:
        return False
    return TOOL_REGISTRY[tool_name].streaming

def initialize_tools() -> None:
    """
    Initialize all tools and register them in the registry.
    
    This function dynamically imports and registers all available tools.
    """
    logger.info("Initializing tools...")
    
    try:
        # Import and register bash tool
        try:
            from tools.bash import execute_bash, validate_bash_parameters, execute_bash_streaming
            register_tool(
                name="bash",
                definition=BASH_TOOL,
                executor=execute_bash_streaming if hasattr(execute_bash_streaming, 'streaming') else execute_bash,
                validator=validate_bash_parameters,
                streaming=hasattr(execute_bash_streaming, 'streaming')
            )
        except ImportError as e:
            logger.error(f"Failed to import bash tool: {str(e)}")
        
        # Import and register edit tool
        try:
            from tools.edit import execute_edit, validate_edit_parameters, execute_edit_streaming
            register_tool(
                name="str_replace_editor",
                definition=EDIT_TOOL,
                executor=execute_edit_streaming if hasattr(execute_edit_streaming, 'streaming') else execute_edit,
                validator=validate_edit_parameters,
                streaming=hasattr(execute_edit_streaming, 'streaming')
            )
        except ImportError as e:
            logger.error(f"Failed to import edit tool: {str(e)}")
        
        # Import and register computer tool
        try:
            from tools.computer import execute_computer, validate_computer_parameters
            register_tool(
                name="computer",
                definition=COMPUTER_TOOL,
                executor=execute_computer,
                validator=validate_computer_parameters,
                streaming=False
            )
        except ImportError as e:
            logger.error(f"Failed to import computer tool: {str(e)}")
        
        logger.info(f"Registered {len(TOOL_REGISTRY)} tools")
        
    except Exception as e:
        logger.error(f"Error initializing tools: {str(e)}")
        # Register fallback tools as needed