"""
Bash tool implementation for Claude Computer Use.
"""

import os
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, Callable, Union, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bash_tool")

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

async def execute_bash_tool(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None,
    working_directory: Optional[str] = None
) -> ToolResult:
    """
    Execute a bash command.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        working_directory: Optional working directory for the command
        
    Returns:
        ToolResult with the output or error
    """
    # Validate parameters
    valid, error_message = validate_bash_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    command = tool_input.get("command", "")
    
    try:
        if progress_callback:
            progress_callback(f"Executing command: {command}")
        
        # Create the process
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_directory
        )
        
        # Wait for the process to complete
        stdout, stderr = await process.communicate()
        
        # Check if the command was successful
        if process.returncode != 0:
            return ToolResult(error=f"Command failed with exit code {process.returncode}: {stderr.decode()}")
        
        # Return the output
        return ToolResult(output=stdout.decode())
        
    except Exception as e:
        logger.error(f"Error executing bash command: {str(e)}")
        return ToolResult(error=f"Error executing command: {str(e)}")

# For testing without asyncio
def execute_bash_sync(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Synchronous version of execute_bash_tool for testing.
    """
    # Validate parameters
    valid, error_message = validate_bash_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    command = tool_input.get("command", "")
    
    try:
        # Execute the command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True
        )
        
        # Check if the command was successful
        if process.returncode != 0:
            return ToolResult(error=f"Command failed with exit code {process.returncode}: {process.stderr}")
        
        # Return the output
        return ToolResult(output=process.stdout)
        
    except Exception as e:
        logger.error(f"Error executing bash command: {str(e)}")
        return ToolResult(error=f"Error executing command: {str(e)}")

if __name__ == "__main__":
    # Test the tool
    import sys
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        result = execute_bash_sync({"command": command})
        if result.error:
            print(f"Error: {result.error}")
            sys.exit(1)
        else:
            print(result.output)
    else:
        print("Usage: python bash.py <command>")
        sys.exit(1)