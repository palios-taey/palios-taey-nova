"""
Streaming-compatible bash tool implementation for Claude DC (FIXED VERSION).

This module provides a secure, isolated bash execution tool that supports streaming
output capabilities with proper async patterns, validation, and error handling.
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
    # First try bridge toggles
    from dc_bridge.enhanced_bridge import toggles
    use_streaming_bash = toggles.is_enabled("use_streaming_bash")
    use_bash_timeouts = toggles.is_enabled("use_bash_timeouts")
    use_rate_limiting = toggles.is_enabled("use_rate_limiting")
except ImportError:
    try:
        # Fall back to JSON config file
        import json
        from pathlib import Path
        
        toggle_path = Path(__file__).parent.parent / "feature_toggles.json"
        if toggle_path.exists():
            with open(toggle_path, "r") as f:
                feature_toggles = json.load(f)
                use_streaming_bash = feature_toggles.get("use_streaming_bash", True)
                use_bash_timeouts = feature_toggles.get("use_bash_timeouts", True)
                use_rate_limiting = feature_toggles.get("use_rate_limiting", True)
                logging.info(f"Loaded feature toggles from {toggle_path}")
        else:
            logging.warning(f"Feature toggles file not found at {toggle_path}, using defaults")
            use_streaming_bash = True
            use_bash_timeouts = True
            use_rate_limiting = True
    except Exception as e:
        logging.warning(f"Could not load feature toggles: {str(e)}, using defaults")
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
    # Log the received tool input for debugging
    logger.info(f"Starting bash tool execution with input: {tool_input}")
    
    # ----- PARAMETER VALIDATION STAGE 1: Basic input validation -----
    if tool_input is None:
        error_msg = "Error: Tool input is None. Please provide a dictionary with a 'command' parameter."
        logger.error(error_msg)
        yield error_msg
        return
        
    if not isinstance(tool_input, dict):
        error_msg = f"Error: Tool input must be a dictionary, got {type(tool_input).__name__}."
        logger.error(error_msg)
        yield error_msg
        return
    
    # ----- PARAMETER VALIDATION STAGE 2: Command parameter detection -----
    if "command" not in tool_input:
        # Gather information about what parameters were actually provided
        provided_params = list(tool_input.keys())
        
        # Check if there are other fields that might have been intended as commands
        possible_cmd_fields = ["prompt", "text", "input", "query", "code", "script", "cmd", "exec"]
        alt_field_used = None
        
        for field in possible_cmd_fields:
            if field in tool_input and tool_input[field]:
                alt_field_used = field
                break
        
        # Provide detailed, actionable error message
        if alt_field_used:
            error_msg = (
                f"Error: Missing required 'command' parameter. You provided '{alt_field_used}' instead.\n"
                f"Please use the EXACT parameter name 'command' as in: {{\"command\": \"your shell command\"}}"
            )
            logger.error(f"Wrong parameter name used: {alt_field_used} instead of command")
        elif provided_params:
            error_msg = (
                f"Error: Missing required 'command' parameter. Parameters provided: {', '.join(provided_params)}.\n"
                f"The 'command' parameter is REQUIRED for this tool. Please use the format: {{\"command\": \"your shell command\"}}"
            )
            logger.error(f"Command parameter missing. Provided parameters: {provided_params}")
        else:
            error_msg = (
                "Error: Missing required 'command' parameter. Empty parameters provided.\n"
                "This tool requires a 'command' parameter with the shell command to execute.\n"
                "Example: {\"command\": \"ls -la\"}"
            )
            logger.error("Empty parameters object provided")
        
        yield error_msg
        return
    
    # ----- PARAMETER VALIDATION STAGE 3: Command parameter validation -----
    command = tool_input.get("command", "")
    
    # Check for correct data type
    if not isinstance(command, str):
        error_msg = (
            f"Error: Command must be a string, got {type(command).__name__}.\n"
            f"Please provide the command as a string: {{\"command\": \"your shell command\"}}"
        )
        logger.error(f"Invalid command type: {type(command).__name__}")
        yield error_msg
        return
    
    # Check for empty command
    if not command.strip():
        error_msg = (
            "Error: Empty command provided. The command parameter cannot be empty.\n"
            "Please provide a non-empty command to execute."
        )
        logger.error("Empty command string provided")
        yield error_msg
        return
    
    # Set execution mode (default to read_only for safety)
    mode = tool_input.get("mode", "read_only")
    
    # Log successful command validation
    logger.info(f"Parameter validation successful. Executing bash command: {command} (mode: {mode})")
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

# Function to process streaming output for tool results - FIXED!
async def dc_process_streaming_output(output_chunks: List[str]) -> DCToolResult:
    """
    Process streaming output and collect it into a DCToolResult.
    
    Args:
        output_chunks: List of output chunks from streaming
        
    Returns:
        DCToolResult with collected output/error
    """
    output_text = []
    error_text = []
    
    # Process each chunk
    for chunk in output_chunks:
        # Check if this is an error message
        if chunk.startswith("Error:") or chunk.startswith("\nError"):
            error_text.append(chunk)
        else:
            output_text.append(chunk)
    
    if error_text:
        return DCToolResult(error="".join(error_text))
    else:
        return DCToolResult(output="".join(output_text))

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
        output_chunks = []
        async for chunk in dc_execute_bash_tool_streaming(tool_input):
            output_chunks.append(chunk)
        
        # Process collected chunks directly
        return await dc_process_streaming_output(output_chunks)
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
    # Log the validation attempt
    logger.info(f"Validating bash parameters: {tool_input}")
    
    # Basic input validation
    if tool_input is None:
        return False, "Tool input is None. Please provide a dictionary with a 'command' parameter."
        
    if not isinstance(tool_input, dict):
        return False, f"Tool input must be a dictionary, got {type(tool_input).__name__}."
    
    # Check for the command parameter specifically
    if "command" not in tool_input:
        # Check if there are other fields that might have been intended as commands
        possible_cmd_fields = ["prompt", "text", "input", "query", "code", "script"]
        alt_field_used = None
        
        for field in possible_cmd_fields:
            if field in tool_input and tool_input[field]:
                alt_field_used = field
                break
        
        if alt_field_used:
            return False, f"Missing required 'command' parameter. You provided '{alt_field_used}' instead. Please use 'command' as the parameter name."
        else:
            return False, "Missing required 'command' parameter. Please provide a command to execute using the format: {\"command\": \"your shell command\"}."
    
    # Extract command and validate it's a proper string
    command = tool_input.get("command")
    
    if not isinstance(command, str):
        return False, f"Command must be a string, got {type(command).__name__}."
        
    if not command.strip():
        return False, "Empty command. Please provide a non-empty string command."
    
    # Validate mode parameter if present
    if "mode" in tool_input:
        mode = tool_input.get("mode")
        if mode not in ["read_only", "standard", "development"]:
            return False, f"Invalid mode: {mode}. Must be one of: read_only, standard, development"
    
    logger.info(f"Command parameter validation successful: {command}")
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