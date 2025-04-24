"""
Streaming-compatible bash tool implementation for Claude DC.
This module provides enhanced bash execution with streaming output capabilities.
"""

import asyncio
import logging
import time
import re
import traceback
import shlex
from pathlib import Path
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dc_bash_streaming")

# Add file handler for streaming bash logs
log_dir = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dev/streaming/logs")
log_dir.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(log_dir / "dc_bash_streaming.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Define the model for tool results
class DCToolResult:
    """Result model for DC tools with support for streaming output."""
    
    def __init__(
        self, 
        output: Optional[str] = None, 
        error: Optional[str] = None, 
        base64_image: Optional[str] = None,
        system: Optional[str] = None
    ):
        self.output = output
        self.error = error
        self.base64_image = base64_image
        self.system = system

# Validator for read-only commands
async def validate_read_only_command(command: str) -> Tuple[bool, str]:
    """
    Validate that a command is safe and read-only.
    
    Args:
        command: The command to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Strip leading/trailing whitespace
    command = command.strip()
    
    # Normalize command by removing extra whitespace
    normalized_command = ' '.join(command.split())
    base_command = normalized_command.split()[0] if normalized_command.split() else ""
    
    # Whitelist of safe read-only commands
    read_only_commands = {
        # File system inspection
        "ls", "dir", "find", "locate", "stat", "file", "du", "df", "pwd",
        
        # File content viewing
        "cat", "head", "tail", "less", "more", "grep", "zgrep", "zcat", "strings",
        
        # System information
        "ps", "top", "htop", "free", "vmstat", "uptime", "uname", "whoami", "id",
        "date", "cal", "env", "printenv", "hostname", "dmesg",
        
        # Network read-only
        "ping", "netstat", "ss", "ip", "ifconfig", "route", "traceroute", "dig", "nslookup",
        "host", "whois", "wget", "curl",
        
        # Others
        "echo", "which", "whereis", "type", "man", "help"
    }
    
    if base_command not in read_only_commands:
        return False, f"Command '{base_command}' is not in the whitelist of read-only commands"
    
    # Blacklist of dangerous patterns
    dangerous_patterns = [
        # Command chaining/piping to dangerous commands
        r"[|;&`\\](?:\s*sudo|\s*rm|\s*mkfs|\s*dd|\s*mv|\s*cp|\s*chmod|\s*chown|\s*tee|\s*>.+)",
        
        # Output redirection to files
        r"(?:\d?>|>>)\s*\S+",
        
        # Sensitive directories
        r"\s+(/etc/(passwd|shadow|crontab)|/var/log/auth.log)",
        
        # Sensitive commands disguised as arguments
        r"\s+-[a-zA-Z]*[eE][a-zA-Z]*\s+.*\(",  # Commands with exec flags
        
        # Environment variables that might contain secrets
        r"\$\{?SECRET|\$\{?PASSWORD|\$\{?KEY",
        
        # URLs with write-capable protocols
        r"(ftp|sftp|ssh|rsync)://",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, normalized_command):
            return False, f"Command contains potentially dangerous pattern: {pattern}"
    
    # Command-specific validation
    if base_command in ["wget", "curl"]:
        # Only allow output to stdout, not to files
        if re.search(r"(?:-o|-O|--output|--output-document)\s+\S+", normalized_command) and \
           not re.search(r"(?:-o|-O|--output|--output-document)\s+-", normalized_command):
            return False, f"{base_command} cannot write to files, only to stdout"
    
    # Check for potentially dangerous flags/arguments by command
    command_flag_blacklist = {
        "chmod": ["-R", "--recursive"],
        "chown": ["-R", "--recursive"],
        "rm": ["-r", "-f", "--recursive", "--force"],
        "cp": ["-f", "--force"],
        "find": ["-exec", "-delete"],
    }
    
    if base_command in command_flag_blacklist:
        cmd_args = normalized_command.split()[1:]
        for flag in command_flag_blacklist[base_command]:
            if flag in cmd_args:
                return False, f"Dangerous flag '{flag}' detected for command '{base_command}'"
    
    return True, "Command validated as read-only"

async def dc_execute_bash_tool_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a bash command with streaming output.
    
    Args:
        tool_input: The input parameters
        progress_callback: Optional callback for progress updates
        
    Yields:
        Command output chunks as they become available
    """
    command = tool_input.get("command", "")
    if not command:
        yield "Error: Empty command"
        return
    
    logger.info(f"Executing bash command with streaming: {command}")
    start_time = time.time()
    
    # Validate the command is read-only
    is_valid, message = await validate_read_only_command(command)
    if not is_valid:
        logger.warning(f"Command validation failed: {message}")
        yield f"Error: {message}"
        return
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting command: {command}", 0.0)
    
    try:
        # Execute the command with streaming output
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Stream stdout
        stdout_chunks = []
        line_count = 0
        total_bytes = 0
        
        if process.stdout:
            async for line in process.stdout:
                line_str = line.decode('utf-8')
                stdout_chunks.append(line_str)
                line_count += 1
                total_bytes += len(line_str)
                
                # Yield the line to the streaming output
                yield line_str
                
                # Report progress (approximation based on line count)
                if progress_callback:
                    # We don't know total lines, so use a pulsing progress approach
                    progress = min(0.99, (line_count % 100) / 100)
                    await progress_callback(
                        f"Running: {command} (read {total_bytes} bytes)", 
                        progress
                    )
        
        # Wait for completion
        return_code = await process.wait()
        
        # Measure execution time
        execution_time = time.time() - start_time
        logger.info(f"Command completed in {execution_time:.2f} seconds with return code {return_code}")
        
        # Get stderr if there was an error
        if return_code != 0:
            if process.stderr:
                stderr = await process.stderr.read()
                stderr_str = stderr.decode('utf-8')
                yield f"\nError (return code {return_code}):\n{stderr_str}"
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed: {command}", 1.0)
            
        # If nothing was yielded yet (empty output), yield a completion message
        if not stdout_chunks:
            yield f"Command completed successfully with no output."
    
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Report error in progress
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)
        
        # Yield error message
        yield f"Error executing command: {str(e)}\n{traceback.format_exc()}"

# Function to process streaming output for tool results
async def dc_process_streaming_output(
    generator: AsyncGenerator[str, None]
) -> DCToolResult:
    """
    Process streaming output and collect it into a DCToolResult.
    
    Args:
        generator: An async generator yielding command output
        
    Returns:
        DCToolResult with collected output/error
    """
    output_chunks = []
    error_chunks = []
    
    try:
        async for chunk in generator:
            # Check if this is an error message
            if chunk.startswith("Error:") or chunk.startswith("\nError"):
                error_chunks.append(chunk)
            else:
                output_chunks.append(chunk)
    except Exception as e:
        error_chunks.append(f"Error processing output: {str(e)}")
    
    if error_chunks:
        return DCToolResult(error="".join(error_chunks))
    else:
        return DCToolResult(output="".join(output_chunks))

# Function to execute bash command and convert to DCToolResult (for compatibility)
async def dc_execute_bash_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Execute bash command and return DCToolResult (non-streaming wrapper).
    
    Args:
        tool_input: The input parameters
        
    Returns:
        DCToolResult with command output/error
    """
    generator = dc_execute_bash_tool_streaming(tool_input)
    return await dc_process_streaming_output(generator)

# Demo function for testing the streaming implementation
async def demo_streaming_bash():
    """Demo function to test the streaming bash implementation."""
    print("\nTesting streaming bash implementation\n")
    
    # Define a test command
    test_command = "ls -la /home/computeruse"
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    print(f"Executing command: {test_command}")
    print("Output:")
    
    # Execute with streaming
    async for chunk in dc_execute_bash_tool_streaming(
        {"command": test_command},
        progress_callback=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    print("\n\nDone!")

# Entry point for direct script execution
if __name__ == "__main__":
    asyncio.run(demo_streaming_bash())