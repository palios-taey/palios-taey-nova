"""
Tool registry implementation with namespace isolation.
"""

from typing import Dict, Any, List, Callable, Awaitable, Optional

# Import with namespace isolation
from ..models.dc_models import DCToolResult, DCToolInfo

# Tool definitions with namespace-isolated names
DC_COMPUTER_TOOL = {
    "name": "dc_computer",  # Different name from production
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

DC_BASH_TOOL = {
    "name": "dc_bash",  # Different name from production
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

# Will be populated by implementations
DC_TOOL_REGISTRY: Dict[str, DCToolInfo] = {}

def dc_register_tool(
    name: str,
    definition: Dict[str, Any],
    executor: Callable[[Dict[str, Any]], Awaitable[DCToolResult]],
    validator: Callable[[Dict[str, Any]], tuple[bool, str]]
) -> None:
    """Register a tool in the registry."""
    global DC_TOOL_REGISTRY
    DC_TOOL_REGISTRY[name] = DCToolInfo(
        definition=definition,
        executor=executor,
        validator=validator
    )

def dc_get_tool_definitions() -> List[Dict[str, Any]]:
    """Get all tool definitions for API configuration."""
    return [tool_info.definition for tool_info in DC_TOOL_REGISTRY.values()]

def dc_get_tool_executor(tool_name: str) -> Optional[Callable]:
    """Get the executor for a specific tool."""
    if tool_name not in DC_TOOL_REGISTRY:
        return None
    return DC_TOOL_REGISTRY[tool_name].executor

def dc_get_tool_validator(tool_name: str) -> Optional[Callable]:
    """Get the validator for a specific tool."""
    if tool_name not in DC_TOOL_REGISTRY:
        return None
    return DC_TOOL_REGISTRY[tool_name].validator</parameter>
</invoke>