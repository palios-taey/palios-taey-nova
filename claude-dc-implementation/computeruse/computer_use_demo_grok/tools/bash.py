"""
Bash tool implementation for Claude Computer Use.
"""

import os
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, Callable, List

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

# List of potentially dangerous commands to check for
DANGEROUS_COMMANDS = [
    "rm -rf", "rmdir", "mkfs", "dd", "chmod -R 777",
    "> /dev/", "format", "shutdown", "reboot", "> /etc/passwd",
    "mv /*", "rm /*", ":(){ :|:& };:", "> /dev/sda"
]

async def validate_bash_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
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
    for dangerous_cmd in DANGEROUS_COMMANDS:
        if dangerous_cmd in command:
            return False, f"Potentially dangerous command detected: {dangerous_cmd}"
    
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
    valid, error_message = await validate_bash_parameters(tool_input)
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
        
        # Buffer for collecting stdout in real-time
        stdout_buffer = []
        stderr_buffer = []
        
        # Function to read stdout in chunks and report progress
        async def read_stdout():
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode()
                stdout_buffer.append(decoded_line)
                
                if progress_callback:
                    progress_callback(decoded_line.strip())
        
        # Function to read stderr in chunks
        async def read_stderr():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                
                stderr_buffer.append(line.decode())
        
        # Start reading tasks
        stdout_task = asyncio.create_task(read_stdout())
        stderr_task = asyncio.create_task(read_stderr())
        
        # Wait for the process to complete
        await process.wait()
        
        # Wait for the reading tasks to complete
        await stdout_task
        await stderr_task
        
        # Combine the output
        stdout_output = "".join(stdout_buffer)
        stderr_output = "".join(stderr_buffer)
        
        # Check if the command was successful
        if process.returncode != 0:
            # Command failed
            return ToolResult(error=f"Command failed with exit code {process.returncode}: {stderr_output}")
        
        # Return the output
        return ToolResult(output=stdout_output)
        
    except Exception as e:
        logger.error(f"Error executing bash command: {str(e)}")
        return ToolResult(error=f"Error executing command: {str(e)}")

# Synchronous version for testing
def execute_bash_sync(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Synchronous version of execute_bash_tool for testing.
    """
    try:
        # Validate parameters
        loop = asyncio.new_event_loop()
        valid, error_message = loop.run_until_complete(validate_bash_parameters(tool_input))
        if not valid:
            return ToolResult(error=error_message)
        
        command = tool_input.get("command", "")
        
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