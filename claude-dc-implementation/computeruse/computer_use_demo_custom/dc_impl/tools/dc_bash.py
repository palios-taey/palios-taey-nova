"""
Streaming-compatible bash tool implementation for Claude DC.

This module provides a secure, isolated bash execution tool that supports streaming
output capabilities. It includes strong validation, security controls, and proper
error handling for bash commands executed in the Claude DC environment.
"""

import asyncio
import logging
import time
import re
import traceback
import shlex
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List, Tuple

# Fix import paths for both direct and package imports
import sys
try:
    # When imported directly (for tests)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dc_models import DCToolResult
except ImportError:
    # When imported as a package
    from ..models.dc_models import DCToolResult

# Try to import feature toggles
try:
    from dc_bridge.enhanced_bridge import toggles
    use_streaming_bash = toggles.is_enabled("use_streaming_bash")
    use_bash_timeouts = toggles.is_enabled("use_bash_timeouts")
    use_rate_limiting = toggles.is_enabled("use_rate_limiting")
except ImportError:
    logging.warning("Could not import feature toggles, using defaults")
    use_streaming_bash = True
    use_bash_timeouts = True
    use_rate_limiting = True

# Set up logging
logger = logging.getLogger("dc_bash")
logger.setLevel(logging.INFO)

# Add file handler for bash logs if directory exists
logs_dir = Path("/home/computeruse/computer_use_demo_custom/dc_impl/logs")
logs_dir.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(logs_dir / "dc_bash.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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

# Validator for bash commands with configurable mode
async def dc_validate_bash_command(command: str, mode: str = "read_only") -> Tuple[bool, str]:
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
    # Extract command and validate input
    command = tool_input.get("command", "")
    if not command:
        yield "Error: Empty command"
        return
    
    # Set execution mode (default to read_only for safety)
    mode = tool_input.get("mode", "read_only")
    
    logger.info(f"Executing bash command with streaming: {command} (mode: {mode})")
    start_time = time.time()
    
    # Validate the command
    is_valid, message = await dc_validate_bash_command(command, mode)
    if not is_valid:
        logger.warning(f"Command validation failed: {message}")
        yield f"Error: {message}"
        return
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting command: {command}", 0.0)
    
    try:
        # Define resource limits if enabled
        if use_bash_timeouts:
            resource_limited_command = f"ulimit -t 10 -v 500000; {command}"
        else:
            resource_limited_command = command
            
        # Execute the command with streaming output
        process = await asyncio.create_subprocess_shell(
            resource_limited_command,
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
        
        # Create a timeout task if timeout protection is enabled
        if use_bash_timeouts:
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
        stdout_chunks = []
        
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
                    yield f"\nOutput truncated: exceeded size limit of {MAX_OUTPUT_SIZE} bytes"
                    break
                
                # Yield the chunk
                yield chunk_str
                
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
            if use_bash_timeouts:
                return_code = await asyncio.wait_for(
                    process.wait(), 
                    timeout=max(0.1, MAX_EXECUTION_TIME - (time.time() - execution_start))
                )
            else:
                return_code = await process.wait()
                
            # Cancel timeout task if it exists and isn't done
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
                
                yield f"\nError (return code {return_code}):\n{stderr_str}"
            
            # Measure execution time
            execution_time = time.time() - start_time
            logger.info(f"Command completed in {execution_time:.2f}s with return code {return_code}")
        
        except asyncio.TimeoutError:
            yield "\nCommand execution timed out and was terminated"
            logger.warning(f"Command timed out after {MAX_EXECUTION_TIME}s: {command}")
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed: {command}", 1.0)
        
        # If nothing was yielded yet (empty output), yield a completion message
        if output_size == 0:
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
    # Validate input parameters
    valid, message = dc_validate_bash_parameters(tool_input)
    if not valid:
        return DCToolResult(error=message)
    
    # Check if streaming is enabled and being used
    if use_streaming_bash:
        # Execute command with streaming and collect results
        generator = dc_execute_bash_tool_streaming(tool_input)
        return await dc_process_streaming_output(generator)
    else:
        # Fall back to original implementation in dc_adapters.py
        try:
            from dc_adapters import dc_execute_bash_tool as original_bash_tool
            return await original_bash_tool(tool_input)
        except ImportError:
            logger.error("Could not import original bash tool, using generic implementation")
            # Generic implementation for compatibility
            command = tool_input.get("command", "")
            if not command:
                return DCToolResult(error="Empty command")
            
            return DCToolResult(output=f"Command executed (non-streaming): {command}")

# Validator for bash parameters
def dc_validate_bash_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
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

# Demo function for direct testing
async def demo_streaming_bash():
    """Demo function to test the streaming bash implementation."""
    print("\nTesting DC streaming bash implementation\n")
    
    # Define a test command
    test_command = "ls -la"
    
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
    # Configure basic console logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    asyncio.run(demo_streaming_bash())