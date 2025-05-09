"""
Tool implementations for Claude DC.
This module provides the implementation for the tools available to Claude.
"""
import os
import sys
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, Union, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tools")

# Flag to disable GUI-dependent features (for headless testing)
GUI_ENABLED = os.environ.get("CLAUDE_DC_GUI_ENABLED", "0") == "1"

try:
    import pyautogui
    GUI_AVAILABLE = True
    logger.info("GUI tools available with pyautogui")
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Install with: pip install pyautogui pillow")
except Exception as e:
    GUI_AVAILABLE = False
    logger.warning(f"Error importing pyautogui: {e}")

async def execute_bash_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a bash command and return the result.
    
    Args:
        tool_input: Tool input with command and optional timeout
        
    Returns:
        Tool execution result with output and status
    """
    try:
        # Extract parameters with validation
        input_params = tool_input.get("input", {})
        if not isinstance(input_params, dict):
            return {"error": "Invalid input format, expected dictionary"}
            
        command = input_params.get("command")
        if not command:
            return {"error": "Command parameter is required"}
        
        timeout = input_params.get("timeout", 30)  # Default 30 seconds timeout
        
        # Log command execution
        logger.info(f"Executing bash command: {command}")
        
        # Execute the command with timeout
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            return {
                "output": stdout_str,
                "error": stderr_str if stderr_str else None,
                "status": process.returncode
            }
        except asyncio.TimeoutError:
            try:
                process.kill()
                return {"error": f"Command timed out after {timeout} seconds"}
            except Exception as e:
                return {"error": f"Command timed out and couldn't be killed: {str(e)}"}
                
    except Exception as e:
        logger.error(f"Error executing bash command: {e}")
        return {"error": f"Command execution failed: {str(e)}"}

async def execute_computer_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute computer actions such as mouse movement, keyboard input, etc.
    
    Args:
        tool_input: Tool input with action and parameters
        
    Returns:
        Tool execution result
    """
    # Check if GUI operations are available
    if not GUI_AVAILABLE and not GUI_ENABLED:
        return {
            "error": "GUI operations not available. Install pyautogui or enable GUI with CLAUDE_DC_GUI_ENABLED=1"
        }
    
    try:
        # Extract parameters with validation
        input_params = tool_input.get("input", {})
        if not isinstance(input_params, dict):
            return {"error": "Invalid input format, expected dictionary"}
            
        action = input_params.get("action")
        if not action:
            return {"error": "Action parameter is required"}
        
        # Log the action
        logger.info(f"Executing computer action: {action}")
        
        # For testing in non-GUI environments
        if not GUI_AVAILABLE and GUI_ENABLED:
            return {
                "success": True,
                "message": f"SIMULATION MODE: Action '{action}' would be executed",
                "parameters": input_params
            }
        
        # Handle different actions
        if action == "screenshot":
            # Implementation for screenshot
            try:
                # Create screenshots directory if it doesn't exist
                os.makedirs("screenshots", exist_ok=True)
                
                # Take screenshot and save to file
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"screenshots/screenshot_{timestamp}.png"
                
                screenshot = pyautogui.screenshot()
                screenshot.save(screenshot_path)
                
                return {
                    "success": True,
                    "path": os.path.abspath(screenshot_path),
                    "message": f"Screenshot saved to {screenshot_path}"
                }
            except Exception as e:
                return {"error": f"Screenshot failed: {str(e)}"}
                
        elif action == "click":
            try:
                # Extract coordinates with validation
                x = input_params.get("x")
                y = input_params.get("y")
                
                if x is None or y is None:
                    return {"error": "x and y coordinates are required for click action"}
                
                # Perform click
                pyautogui.click(x=x, y=y)
                
                return {
                    "success": True,
                    "message": f"Clicked at coordinates ({x}, {y})"
                }
            except Exception as e:
                return {"error": f"Click operation failed: {str(e)}"}
                
        elif action == "type":
            try:
                # Extract text with validation
                text = input_params.get("text")
                
                if not text:
                    return {"error": "text parameter is required for type action"}
                
                # Type the text
                pyautogui.write(text)
                
                return {
                    "success": True,
                    "message": f"Typed text: {text}"
                }
            except Exception as e:
                return {"error": f"Type operation failed: {str(e)}"}
                
        elif action == "pressKey":
            try:
                # Extract key with validation
                key = input_params.get("key")
                
                if not key:
                    return {"error": "key parameter is required for pressKey action"}
                
                # Press the key
                pyautogui.press(key)
                
                return {
                    "success": True,
                    "message": f"Pressed key: {key}"
                }
            except Exception as e:
                return {"error": f"Key press operation failed: {str(e)}"}
                
        elif action == "moveMouse":
            try:
                # Extract coordinates with validation
                x = input_params.get("x")
                y = input_params.get("y")
                
                if x is None or y is None:
                    return {"error": "x and y coordinates are required for moveMouse action"}
                
                # Move the mouse
                pyautogui.moveTo(x=x, y=y)
                
                return {
                    "success": True,
                    "message": f"Moved mouse to coordinates ({x}, {y})"
                }
            except Exception as e:
                return {"error": f"Mouse move operation failed: {str(e)}"}
                
        else:
            return {"error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error executing computer action: {e}")
        return {"error": f"Action execution failed: {str(e)}"}

async def execute_edit_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file operations such as read, write, append, delete.
    
    Args:
        tool_input: Tool input with action, path, and optional content
        
    Returns:
        Tool execution result
    """
    try:
        # Extract parameters with validation
        input_params = tool_input.get("input", {})
        if not isinstance(input_params, dict):
            return {"error": "Invalid input format, expected dictionary"}
            
        action = input_params.get("action")
        if not action:
            return {"error": "Action parameter is required"}
            
        path = input_params.get("path")
        if not path:
            return {"error": "Path parameter is required"}
            
        # Make path absolute if it's not already
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Log the action
        logger.info(f"Executing file {action} operation on {path}")
        
        if action == "read":
            # Read file
            try:
                if not os.path.exists(path):
                    return {"error": f"File not found: {path}"}
                    
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                return {
                    "success": True,
                    "content": content,
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}
                
        elif action == "write":
            # Write file (overwrites existing)
            content = input_params.get("content")
            if content is None:
                return {"error": "Content parameter is required for write action"}
                
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                    
                return {
                    "success": True,
                    "message": f"File written successfully: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to write file: {str(e)}"}
                
        elif action == "append":
            # Append to file
            content = input_params.get("content")
            if content is None:
                return {"error": "Content parameter is required for append action"}
                
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'a', encoding='utf-8') as file:
                    file.write(content)
                    
                return {
                    "success": True,
                    "message": f"Content appended successfully to: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to append to file: {str(e)}"}
                
        elif action == "delete":
            # Delete file
            try:
                if not os.path.exists(path):
                    return {"error": f"File not found: {path}"}
                    
                os.remove(path)
                
                return {
                    "success": True,
                    "message": f"File deleted successfully: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to delete file: {str(e)}"}
                
        else:
            return {"error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error executing file operation: {e}")
        return {"error": f"Operation failed: {str(e)}"}

async def test_tools():
    """
    Test the tool implementations with simple examples.
    """
    # Test bash tool
    print("\n=== Testing bash tool ===")
    bash_result = await execute_bash_tool({
        "name": "bash",
        "input": {"command": "echo 'Hello from bash tool'"}
    })
    print(f"Bash result: {json.dumps(bash_result, indent=2)}")
    
    # Test file operations
    print("\n=== Testing edit tool (write) ===")
    write_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "write",
            "path": "test_file.txt",
            "content": "This is a test file created by the edit tool."
        }
    })
    print(f"Write result: {json.dumps(write_result, indent=2)}")
    
    print("\n=== Testing edit tool (read) ===")
    read_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read",
            "path": "test_file.txt"
        }
    })
    print(f"Read result: {json.dumps(read_result, indent=2)}")
    
    print("\n=== Testing edit tool (delete) ===")
    delete_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "delete",
            "path": "test_file.txt"
        }
    })
    print(f"Delete result: {json.dumps(delete_result, indent=2)}")

if __name__ == "__main__":
    # Run tests
    import nest_asyncio
    nest_asyncio.apply()
    
    asyncio.run(test_tools())