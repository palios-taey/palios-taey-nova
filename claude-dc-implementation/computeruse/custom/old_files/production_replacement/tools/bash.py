"""
Bash tool for executing shell commands with streaming support.

This module provides a streaming-compatible bash tool that allows executing shell
commands with real-time output and progress reporting.
"""

import asyncio
import logging
import time
import re
import traceback
import shlex
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List, Tuple, Union

from models.tool_models import ToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bash_tool")

# Constants for security controls
MAX_EXECUTION_TIME = 30.0  # Maximum execution time in seconds
MAX_OUTPUT_SIZE = 1024 * 1024 * 5  # 5MB maximum output size
READ_ONLY_COMMANDS = {
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
    
    # Development tools
    "git", "python", "python3", "npm", "node", "pip", "pip3",
    
    # Others
    "echo", "which", "whereis", "type", "man", "help"
}

# Validator for bash commands
async def validate_bash_command(command: str, mode: str = "read_only") -> Tuple[bool, str]:
    """
    Validate that a command is safe according to the specified mode.
    
    Args:
        command: The command to validate
        mode: Validation mode - "read_only" (default), "standard", or "development"
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Strip leading/trailing whitespace
    command = command.strip()
    
    # Normalize command by removing extra whitespace
    normalized_command = ' '.join(command.split())
    command_parts = shlex.split(normalized_command)
    base_command = command_parts[0] if command_parts else ""
    
    logger.info(f"Validating command: {base_command} (mode: {mode})")
    
    # Mode-specific validation
    if mode == "read_only":
        # In read-only mode, only explicitly whitelisted commands are allowed
        if base_command not in READ_ONLY_COMMANDS:
            return False, f"Command '{base_command}' is not in the whitelist of read-only commands"
    
    # Blacklist of dangerous patterns (applied to all modes)
    dangerous_patterns = [
        # Command chaining/piping to dangerous commands
        r"[;&`\\](?:\s*sudo|\s*rm|\s*mkfs|\s*dd|\s*mv|\s*cp|\s*chmod|\s*chown)",
        
        # Dangerous system commands
        r"\s+(/etc/(passwd|shadow|crontab|sudoers)|/var/log/auth.log)",
        
        # Sensitive commands disguised as arguments
        r"\s+-[a-zA-Z]*[eE][a-zA-Z]*\s+.*\(",  # Commands with exec flags
        
        # Environment variables that might contain secrets
        r"\$\{?SECRET|\$\{?PASSWORD|\$\{?KEY|\$\{?TOKEN|\$\{?PRIVATE",
        
        # URLs with write-capable protocols
        r"(ftp|sftp|ssh|rsync)://",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, normalized_command):
            return False, f"Command contains potentially dangerous pattern: {pattern}"
    
    # Command-specific validation
    if base_command in ["wget", "curl"]:
        # Only allow output to stdout for these commands
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
        for flag in command_flag_blacklist[base_command]:
            if flag in command_parts:
                return False, f"Dangerous flag '{flag}' detected for command '{base_command}'"
    
    return True, "Command validated successfully"

# Validator for bash parameters
def validate_bash_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate bash tool parameters.
    
    Args:
        tool_input: The input parameters
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required command parameter
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Validate mode parameter if present
    if "mode" in tool_input:
        mode = tool_input.get("mode")
        if mode not in ["read_only", "standard", "development"]:
            return False, f"Invalid mode: {mode}. Must be one of: read_only, standard, development"
    
    return True, "Parameters valid"

# Mark function as supporting streaming
async def execute_bash_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Union[AsyncGenerator[str, None], ToolResult]:
    """
    Execute a bash command with streaming output.
    
    Args:
        tool_input: The input parameters
        progress_callback: Optional callback for progress updates
        
    Returns:
        Either an async generator yielding output chunks or a ToolResult
    """
    # Extract command and validate input
    command = tool_input.get("command", "")
    if not command:
        return ToolResult(error="Empty command")
    
    # Set execution mode (default to read_only for safety)
    mode = tool_input.get("mode", "read_only")
    
    logger.info(f"Executing bash command with streaming: {command} (mode: {mode})")
    start_time = time.time()
    
    # Validate the command
    is_valid, message = await validate_bash_command(command, mode)
    if not is_valid:
        logger.warning(f"Command validation failed: {message}")
        return ToolResult(error=message)
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting command: {command}", 0.0)
    
    output_chunks = []
    
    try:
        # Execute the command with streaming output
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Track execution stats
        output_size = 0
        line_count = 0
        chunk_count = 0
        
        # Monitor process execution time using a task
        execution_start = time.time()
        timeout_task = None
        
        # Create a timeout task
        async def check_timeout():
            try:
                while (time.time() - execution_start) < MAX_EXECUTION_TIME:
                    await asyncio.sleep(0.5)
                
                # If we get here, timeout occurred
                logger.warning(f"Command timeout after {MAX_EXECUTION_TIME}s: {command}")
                try:
                    process.terminate()
                    await asyncio.sleep(0.1)
                    process.kill()
                except Exception as e:
                    logger.error(f"Error killing process: {str(e)}")
            except asyncio.CancelledError:
                # Task was canceled, which is expected when process completes normally
                pass
        
        # Start timeout monitoring
        timeout_task = asyncio.create_task(check_timeout())
        
        # Stream stdout
        if process.stdout:
            while True:
                # Read in reasonably sized chunks rather than lines
                chunk = await process.stdout.read(4096)
                if not chunk:
                    break
                
                # Decode the chunk
                try:
                    chunk_str = chunk.decode('utf-8')
                except UnicodeDecodeError:
                    # Handle binary data or encoding issues
                    chunk_str = chunk.decode('utf-8', errors='replace')
                
                # Update stats
                chunk_count += 1
                output_size += len(chunk_str)
                line_count += chunk_str.count('\n')
                
                # Check if output exceeds size limit
                if output_size > MAX_OUTPUT_SIZE:
                    logger.warning(f"Output size exceeds limit ({output_size} bytes)")
                    output_chunks.append(f"\nOutput truncated: exceeded size limit of {MAX_OUTPUT_SIZE} bytes")
                    break
                
                # Add the chunk to output
                output_chunks.append(chunk_str)
                
                # Report progress
                if progress_callback:
                    elapsed = time.time() - execution_start
                    progress = min(0.95, elapsed / MAX_EXECUTION_TIME)
                    await progress_callback(
                        f"Running: {command} ({line_count} lines, {output_size/1024:.1f}KB)", 
                        progress
                    )
        
        # Wait for completion or timeout
        try:
            return_code = await asyncio.wait_for(
                process.wait(), 
                timeout=max(0.1, MAX_EXECUTION_TIME - (time.time() - execution_start))
            )
            
            # Cancel timeout task
            if timeout_task and not timeout_task.done():
                timeout_task.cancel()
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass
            
            # Get stderr if there was an error
            if return_code != 0 and process.stderr:
                stderr = await process.stderr.read()
                try:
                    stderr_str = stderr.decode('utf-8')
                except UnicodeDecodeError:
                    stderr_str = stderr.decode('utf-8', errors='replace')
                
                output_chunks.append(f"\nError (return code {return_code}):\n{stderr_str}")
            
            # Measure execution time
            execution_time = time.time() - start_time
            logger.info(f"Command completed in {execution_time:.2f}s with return code {return_code}")
        
        except asyncio.TimeoutError:
            output_chunks.append("\nCommand execution timed out and was terminated")
            logger.warning(f"Command timed out after {MAX_EXECUTION_TIME}s: {command}")
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed: {command}", 1.0)
        
        # If nothing was output yet (empty output), add a completion message
        if not output_chunks:
            output_chunks.append("Command completed successfully with no output.")
        
        # Join all chunks into a single output
        output = "".join(output_chunks)
        return ToolResult(output=output)
    
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Report error in progress
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)
        
        # Return error message
        return ToolResult(error=f"Error executing command: {str(e)}\n{traceback.format_exc()}")

# Set streaming attribute
execute_bash_streaming.streaming = True

async def execute_bash(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a bash command and return a ToolResult.
    
    This is a non-streaming wrapper around execute_bash_streaming.
    
    Args:
        tool_input: The input parameters
        
    Returns:
        ToolResult with command output or error
    """
    # Call the streaming implementation
    return await execute_bash_streaming(tool_input)

# Test function for direct execution
async def test_bash_tool():
    """Test the bash tool."""
    print("\nTesting bash tool...\n")
    
    # Test commands
    test_commands = [
        "echo 'Hello, World!'",
        "ls -la",
        "pwd",
        "date",
        "invalid_command",
        "rm -rf /",  # This should fail validation
    ]
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Test each command
    for command in test_commands:
        print(f"\nExecuting: {command}")
        result = await execute_bash({"command": command})
        
        if result.error:
            print(f"Error: {result.error}")
        else:
            print(f"Output: {result.output}")
    
    # Test streaming
    print("\nTesting streaming output...")
    
    result = await execute_bash_streaming(
        {"command": "ls -la /"},
        progress_callback=progress_callback
    )
    
    if isinstance(result, ToolResult):
        if result.error:
            print(f"\nError: {result.error}")
        else:
            print(f"\nOutput: {result.output}")
    else:
        print("\nUnexpected result type")

if __name__ == "__main__":
    asyncio.run(test_bash_tool())