"""
Tool adapters for the DC implementation.
These provide mock implementations for testing.
"""

import logging
import json
from typing import Dict, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger("dc_adapters")

def dc_validate_computer_parameters(parameters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for the computer tool.
    
    Args:
        parameters: The parameters to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required action parameter
    if 'action' not in parameters:
        return False, "Missing required parameter: action"
    
    action = parameters.get('action')
    
    # Validate different actions
    if action == 'execute_python':
        if 'code' not in parameters:
            return False, "Missing required parameter for execute_python: code"
    elif action == 'read_file':
        if 'path' not in parameters:
            return False, "Missing required parameter for read_file: path"
    elif action == 'write_file':
        if 'path' not in parameters or 'content' not in parameters:
            return False, "Missing required parameters for write_file: path and/or content"
    elif action == 'list_directory':
        if 'path' not in parameters:
            return False, "Missing required parameter for list_directory: path"
    
    return True, "Parameters validated successfully"

def dc_validate_bash_parameters(parameters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for the bash tool.
    
    Args:
        parameters: The parameters to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required command parameter
    if 'command' not in parameters:
        return False, "Missing required parameter: command"
    
    # Ensure it's a string
    if not isinstance(parameters['command'], str):
        return False, "Parameter 'command' must be a string"
    
    # Check for any unsafe commands or patterns (this is a simple example)
    command = parameters['command'].lower()
    unsafe_commands = ['rm -rf /', 'dd if=/dev/zero', 'rm -rf ~']
    
    for unsafe in unsafe_commands:
        if unsafe in command:
            return False, f"Unsafe command detected: {unsafe}"
    
    return True, "Parameters validated successfully"

def dc_execute_computer_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock implementation of the computer tool.
    
    Args:
        parameters: The parameters for the tool
        
    Returns:
        Results dictionary
    """
    is_valid, message = dc_validate_computer_parameters(parameters)
    if not is_valid:
        return {
            "status": "error",
            "message": message
        }
    
    action = parameters.get('action')
    
    # Mock responses for different actions
    if action == 'execute_python':
        return {
            "status": "success",
            "result": "Mock Python execution (no real execution in mock mode)",
            "stdout": "Mock stdout",
            "stderr": ""
        }
    elif action == 'read_file':
        path = parameters.get('path', '')
        return {
            "status": "success",
            "content": f"Mock file content for {path}",
            "message": "File read successfully (mock data)"
        }
    elif action == 'write_file':
        path = parameters.get('path', '')
        return {
            "status": "success",
            "message": f"File written successfully to {path} (mock operation)"
        }
    elif action == 'list_directory':
        path = parameters.get('path', '')
        return {
            "status": "success",
            "files": ["file1.txt", "file2.py", "directory1/"],
            "message": f"Directory {path} listed successfully (mock data)"
        }
    else:
        return {
            "status": "error",
            "message": f"Unknown action: {action}"
        }

def dc_execute_bash_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock implementation of the bash tool.
    
    Args:
        parameters: The parameters for the tool
        
    Returns:
        Results dictionary
    """
    is_valid, message = dc_validate_bash_parameters(parameters)
    if not is_valid:
        return {
            "status": "error",
            "message": message
        }
    
    command = parameters.get('command', '')
    
    # Provide mock output for common commands
    if 'ls' in command:
        return {
            "status": "success",
            "stdout": "file1.txt\nfile2.py\ndirectory1/\n",
            "stderr": "",
            "exit_code": 0
        }
    elif 'echo' in command:
        # Extract what's being echoed
        echo_content = command.split('echo')[1].strip()
        return {
            "status": "success",
            "stdout": f"{echo_content}\n",
            "stderr": "",
            "exit_code": 0
        }
    elif 'pwd' in command:
        return {
            "status": "success",
            "stdout": "/home/mock/directory\n",
            "stderr": "",
            "exit_code": 0
        }
    else:
        return {
            "status": "success",
            "stdout": f"Mock output for command: {command}",
            "stderr": "",
            "exit_code": 0
        }