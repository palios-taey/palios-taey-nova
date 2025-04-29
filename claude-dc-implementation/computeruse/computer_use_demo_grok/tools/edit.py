"""
Edit tool implementation for Claude Computer Use.
Provides basic file operations like reading, writing and appending.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("edit_tool")

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

# List of potentially dangerous paths to check
DANGEROUS_PATHS = [
    "/etc/passwd", "/etc/shadow", "/etc/sudoers", 
    "/boot", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
    "/proc", "/sys", "/dev", "/var/run"
]

async def validate_edit_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the parameters for the edit tool.
    
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
    
    if action not in ["read", "write", "append"]:
        return False, f"Unknown action: {action}. Must be 'read', 'write', or 'append'"
    
    if "path" not in tool_input:
        return False, "Missing required 'path' parameter"
    
    path = tool_input.get("path", "")
    if not path or not isinstance(path, str):
        return False, "Path must be a non-empty string"
    
    # Check for potentially dangerous paths
    for dangerous_path in DANGEROUS_PATHS:
        if path.startswith(dangerous_path):
            return False, f"Cannot modify system paths: {dangerous_path}"
    
    # Check for write/append-specific parameters
    if action in ["write", "append"] and "content" not in tool_input:
        return False, f"Missing required 'content' parameter for {action} action"
    
    return True, "Valid parameters"

async def safe_read_file(path: str, progress_callback: Optional[Callable[[str], None]] = None) -> ToolResult:
    """Safely read a file with progress updates"""
    try:
        if not os.path.exists(path):
            return ToolResult(error=f"File not found: {path}")
        
        if not os.path.isfile(path):
            return ToolResult(error=f"Not a file: {path}")
        
        if progress_callback:
            progress_callback(f"Reading file: {path}")
        
        # Get file size for progress reporting
        file_size = os.path.getsize(path)
        
        # Read the file
        with open(path, 'r') as f:
            content = f.read()
        
        if progress_callback:
            progress_callback(f"Read {len(content)} bytes from {path}")
        
        return ToolResult(output=content)
    
    except Exception as e:
        logger.error(f"Error reading file {path}: {str(e)}")
        return ToolResult(error=f"Error reading file: {str(e)}")

async def safe_write_file(path: str, content: str, append: bool = False, 
                         progress_callback: Optional[Callable[[str], None]] = None) -> ToolResult:
    """Safely write to a file with progress updates"""
    try:
        # Make sure parent directory exists
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            if progress_callback:
                progress_callback(f"Creating directory: {parent_dir}")
            os.makedirs(parent_dir, exist_ok=True)
        
        # Log the action
        mode = 'a' if append else 'w'
        action = "Appending to" if append else "Writing to"
        if progress_callback:
            progress_callback(f"{action} file: {path}")
        
        # Write to the file
        with open(path, mode) as f:
            f.write(content)
        
        if progress_callback:
            progress_callback(f"Wrote {len(content)} bytes to {path}")
        
        return ToolResult(output=f"Successfully {action.lower()} file: {path}")
    
    except Exception as e:
        logger.error(f"Error writing to file {path}: {str(e)}")
        return ToolResult(error=f"Error writing to file: {str(e)}")

async def execute_edit_tool(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute a file operation.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the output or error
    """
    # Validate parameters
    valid, error_message = await validate_edit_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    action = tool_input.get("action", "")
    path = tool_input.get("path", "")
    
    try:
        # Handle different actions
        if action == "read":
            return await safe_read_file(path, progress_callback)
        
        elif action == "write":
            content = tool_input.get("content", "")
            return await safe_write_file(path, content, False, progress_callback)
        
        elif action == "append":
            content = tool_input.get("content", "")
            return await safe_write_file(path, content, True, progress_callback)
        
        else:
            return ToolResult(error=f"Unknown action: {action}")
        
    except Exception as e:
        logger.error(f"Error executing edit action: {str(e)}")
        return ToolResult(error=f"Error executing action: {str(e)}")

if __name__ == "__main__":
    # Test the tool
    import sys
    import json
    
    async def test_action(action, path, content=None):
        tool_input = {"action": action, "path": path}
        if content is not None:
            tool_input["content"] = content
        
        result = await execute_edit_tool(tool_input)
        if result.error:
            print(f"Error: {result.error}")
            return 1
        else:
            print(f"Output: {result.output}")
            return 0
    
    if len(sys.argv) > 2:
        action = sys.argv[1]
        path = sys.argv[2]
        content = sys.argv[3] if len(sys.argv) > 3 else None
        
        # Run the test
        exit_code = asyncio.run(test_action(action, path, content))
        sys.exit(exit_code)
    else:
        print("Usage: python edit.py <action> <path> [content]")
        print("Examples:")
        print("  python edit.py read /path/to/file.txt")
        print("  python edit.py write /path/to/file.txt \"Hello, world!\"")
        print("  python edit.py append /path/to/file.txt \"Another line\"")
        sys.exit(1)