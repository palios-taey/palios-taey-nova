#!/usr/bin/env python3
"""
Tool validation test suite for Claude Computer Use.
This validates parameter checking and error handling for tool implementations.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tool_validation")

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
    # Validate action parameter
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

def validate_bash_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the parameters for the bash tool.
    
    Args:
        tool_input: The input parameters for the tool
        
    Returns:
        (is_valid, error_message)
    """
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command", "")
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Check for potentially dangerous commands
    dangerous_commands = [
        "rm -rf", "rmdir", "mkfs", "dd", "chmod -R 777",
        "> /dev/", "format", "shutdown", "reboot", "> /etc/passwd"
    ]
    
    for cmd in dangerous_commands:
        if cmd in command:
            return False, f"Potentially dangerous command: {cmd}"
    
    return True, "Valid parameters"

def execute_computer_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """Mock implementation of computer tool execution for testing"""
    # Validate parameters
    valid, error_message = validate_computer_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    # Mock execution
    action = tool_input.get("action", "")
    return ToolResult(output=f"Successfully executed {action} action")

def execute_bash_tool(tool_input: Dict[str, Any]) -> ToolResult:
    """Mock implementation of bash tool execution for testing"""
    # Validate parameters
    valid, error_message = validate_bash_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    # Mock execution
    command = tool_input.get("command", "")
    return ToolResult(output=f"Successfully executed command: {command}")

# Test cases for computer tool
def test_computer_tool():
    test_cases = [
        # Valid cases
        {
            "name": "Valid screenshot action",
            "input": {"action": "screenshot"},
            "expected_valid": True
        },
        {
            "name": "Valid mouse move action",
            "input": {"action": "move_mouse", "coordinates": [100, 200]},
            "expected_valid": True
        },
        {
            "name": "Valid type text action",
            "input": {"action": "type_text", "text": "Hello World"},
            "expected_valid": True
        },
        
        # Invalid cases
        {
            "name": "Missing action parameter",
            "input": {"coordinates": [100, 200]},
            "expected_valid": False
        },
        {
            "name": "Empty action parameter",
            "input": {"action": ""},
            "expected_valid": False
        },
        {
            "name": "Missing coordinates for mouse action",
            "input": {"action": "move_mouse"},
            "expected_valid": False
        },
        {
            "name": "Invalid coordinates type",
            "input": {"action": "move_mouse", "coordinates": "100,200"},
            "expected_valid": False
        },
        {
            "name": "Missing text for type_text action",
            "input": {"action": "type_text"},
            "expected_valid": False
        }
    ]
    
    passed = True
    for test in test_cases:
        result = execute_computer_tool(test["input"])
        test_passed = (result.error is None) == test["expected_valid"]
        status = "PASSED" if test_passed else "FAILED"
        print(f"{status}: {test['name']}")
        if not test_passed:
            print(f"  Expected valid: {test['expected_valid']}, Got error: {result.error}")
            passed = False
    
    return passed

# Test cases for bash tool
def test_bash_tool():
    test_cases = [
        # Valid cases
        {
            "name": "Valid simple command",
            "input": {"command": "echo 'Hello World'"},
            "expected_valid": True
        },
        {
            "name": "Valid ls command",
            "input": {"command": "ls -la"},
            "expected_valid": True
        },
        
        # Invalid cases
        {
            "name": "Missing command parameter",
            "input": {},
            "expected_valid": False
        },
        {
            "name": "Empty command parameter",
            "input": {"command": ""},
            "expected_valid": False
        },
        {
            "name": "Dangerous rm -rf command",
            "input": {"command": "rm -rf /"},
            "expected_valid": False
        }
    ]
    
    passed = True
    for test in test_cases:
        result = execute_bash_tool(test["input"])
        test_passed = (result.error is None) == test["expected_valid"]
        status = "PASSED" if test_passed else "FAILED"
        print(f"{status}: {test['name']}")
        if not test_passed:
            print(f"  Expected valid: {test['expected_valid']}, Got error: {result.error}")
            passed = False
    
    return passed

def main():
    print("\n=== Test Results ===\n")
    
    computer_tests = test_computer_tool()
    bash_tests = test_bash_tool()
    
    all_tests = computer_tests and bash_tests
    
    print(f"\nSummary: {all_tests}")
    
    return 0 if all_tests else 1

if __name__ == "__main__":
    sys.exit(main())