"""
Tool adapters with namespace isolation for safely integrating with production tools.
"""

import logging
import time
import os
import sys
import importlib
import asyncio
import base64
import traceback
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dc_models import DCToolResult
except ImportError:
    # When imported as a package
    from ..models.dc_models import DCToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dc_tool_adapters.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dc_tool_adapters")

# Production tool cache
_production_tools = {}

def get_production_tool(tool_name: str) -> Optional[Any]:
    """
    Safely retrieves a production tool instance with caching.
    """
    global _production_tools
    
    # Return cached version if available
    if tool_name in _production_tools:
        logger.debug(f"Using cached instance of {tool_name} tool")
        return _production_tools[tool_name]
    
    try:
        # Add production directory to path temporarily
        prod_dir = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo_custom")
        if str(prod_dir) not in sys.path:
            sys.path.insert(0, str(prod_dir))
        
        # Map tool names to their import paths and classes
        tool_map = {
            "computer": ("tools.computer", "ComputerTool20250124"),
            "bash": ("tools.bash", "BashTool20250124"),
            "edit": ("tools.edit", "StrReplaceEditorTool20250124")
        }
        
        if tool_name not in tool_map:
            logger.error(f"Unknown tool: {tool_name}")
            return None
        
        module_path, class_name = tool_map[tool_name]
        
        # Import the tool
        module = importlib.import_module(module_path)
        tool_class = getattr(module, class_name)
        tool_instance = tool_class()
        
        # Cache the tool
        _production_tools[tool_name] = tool_instance
        logger.info(f"Successfully imported {tool_name} tool")
        
        return tool_instance
    except ImportError as e:
        logger.error(f"Could not import {tool_name} tool: {str(e)}")
    except AttributeError as e:
        logger.error(f"Could not find class for {tool_name} tool: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error importing {tool_name} tool: {str(e)}")
        logger.error(traceback.format_exc())
    
    return None

async def dc_execute_computer_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Production-ready adapter for computer tool implementation with namespace isolation.
    Includes enhanced screenshot functionality with error handling and metrics.
    """
    logger.info(f"DC Computer Tool - Action: {tool_input.get('action')}")
    action = tool_input.get("action")
    
    # Check for required action parameter
    if not action:
        logger.error("Missing required 'action' parameter")
        return DCToolResult(error="Missing required 'action' parameter")
    
    start_time = time.time()
    
    # Try to use the production tool if available
    computer_tool = get_production_tool("computer")
    
    # If production tool is available, use it
    if computer_tool:
        try:
            if action == "screenshot":
                logger.info("Taking screenshot using production tool")
                # The screenshot method doesn't require additional parameters
                result = await computer_tool.screenshot()
                
                # Measure execution time
                execution_time = time.time() - start_time
                logger.info(f"Screenshot taken in {execution_time:.2f} seconds")
                
                if result.error:
                    logger.error(f"Screenshot error: {result.error}")
                    return DCToolResult(error=f"Screenshot failed: {result.error}")
                
                # Check if we got a base64 image
                if not result.base64_image:
                    logger.warning("Screenshot did not return base64 image")
                    return DCToolResult(
                        output="Screenshot taken but no image data returned",
                        error="No image data in result"
                    )
                
                # Verify image data is valid base64
                try:
                    # Just test decoding a small part to validate it's proper base64
                    base64.b64decode(result.base64_image[:100])
                except Exception as e:
                    logger.error(f"Invalid base64 image data: {str(e)}")
                    return DCToolResult(
                        error=f"Invalid screenshot image data: {str(e)}"
                    )
                
                # Success - return the screenshot image
                return DCToolResult(
                    output="Screenshot taken successfully",
                    base64_image=result.base64_image
                )
            elif action == "move_mouse":
                if "coordinates" not in tool_input:
                    return DCToolResult(error="Missing required 'coordinates' parameter")
                
                coordinates = tool_input.get("coordinates")
                logger.info(f"Moving mouse to: {coordinates}")
                
                # Validate coordinates
                if not isinstance(coordinates, list) or len(coordinates) != 2:
                    return DCToolResult(error="Invalid coordinates format. Expected [x, y]")
                
                # Call production tool with proper parameters
                result = await computer_tool.mouse_move(coordinate=coordinates)
                
                if result.error:
                    return DCToolResult(error=f"Mouse movement failed: {result.error}")
                
                return DCToolResult(output=f"Mouse moved to {coordinates}")
            elif action == "type_text":
                if "text" not in tool_input:
                    return DCToolResult(error="Missing required 'text' parameter")
                
                text = tool_input.get("text")
                logger.info(f"Typing text: {text}")
                
                # Call production tool with proper parameters
                result = await computer_tool.type(text=text)
                
                if result.error:
                    return DCToolResult(error=f"Text typing failed: {result.error}")
                
                return DCToolResult(output=f"Typed text: {text}")
            else:
                # For other actions, use a generic approach with parameter passing
                # This is a more flexible approach that will work with various actions
                logger.info(f"Executing {action} with parameters: {tool_input}")
                
                # Get the method from the tool
                method = getattr(computer_tool, action, None)
                if not method:
                    return DCToolResult(error=f"Unsupported action: {action}")
                
                # Prepare parameters (remove action)
                params = {k: v for k, v in tool_input.items() if k != "action"}
                
                # Call the method with parameters
                result = await method(**params)
                
                if result.error:
                    return DCToolResult(error=f"{action} failed: {result.error}")
                
                return DCToolResult(
                    output=result.output,
                    base64_image=result.base64_image
                )
        except Exception as e:
            logger.error(f"Error in production tool: {str(e)}")
            logger.error(traceback.format_exc())
            # Fall back to mock implementation
            logger.info("Falling back to mock implementation")
    
    # Mock implementation (fallback or when production tool is unavailable)
    logger.info(f"Using mock implementation for {action}")
    
    # Safe mock implementation with improved output
    if action == "screenshot":
        logger.info("Taking mock screenshot")
        return DCToolResult(output="Mock screenshot taken (production tool unavailable)")
    elif action == "move_mouse":
        coordinates = tool_input.get("coordinates", [0, 0])
        logger.info(f"Moving mock mouse to: {coordinates}")
        return DCToolResult(output=f"Mock mouse moved to {coordinates}")
    elif action == "type_text":
        text = tool_input.get("text", "")
        logger.info(f"Typing mock text: {text}")
        return DCToolResult(output=f"Mock text typed: {text}")
    else:
        return DCToolResult(output=f"Mock {action} executed")

async def dc_execute_bash_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Production-ready adapter for bash tool implementation with namespace isolation.
    Includes enhanced security features:
    - Strict command whitelisting for safety
    - Timeout mechanisms to prevent hung processes
    - Output sanitization for binary data and special characters
    - Resource limits to prevent excessive CPU/memory usage
    - Read-only command enforcement
    """
    logger.info(f"DC Bash Tool - Command: {tool_input.get('command')}")
    command = tool_input.get("command", "")
    start_time = time.time()
    
    # Check for required command parameter
    if not command:
        logger.error("Missing or empty 'command' parameter")
        return DCToolResult(error="Missing or empty 'command' parameter")
    
    # Validate the command is a read-only command
    is_valid, validation_message = dc_validate_read_only_command(command)
    if not is_valid:
        logger.error(f"Command validation failed: {validation_message}")
        return DCToolResult(error=f"Command validation failed: {validation_message}")
    
    # Try to use the production tool if available
    bash_tool = get_production_tool("bash")
    
    # Define execution timeout (in seconds)
    timeout = 15.0
    
    # Set resource limits
    resource_limited_command = f"ulimit -t 10 -v 500000; {command}"
    
    # If production tool is available, use it
    if bash_tool:
        try:
            logger.info(f"Executing command using production tool: {command}")
            
            # Execute command with timeout
            try:
                # Use asyncio.wait_for to enforce timeout
                result = await asyncio.wait_for(
                    bash_tool(command=resource_limited_command),
                    timeout=timeout
                )
                
                # Measure execution time
                execution_time = time.time() - start_time
                logger.info(f"Command executed in {execution_time:.2f} seconds")
                
                if result.error:
                    logger.error(f"Command error: {result.error}")
                    return DCToolResult(error=f"Command execution failed: {result.error}")
                
                # Sanitize output to handle binary data or special characters
                sanitized_output = dc_sanitize_command_output(result.output)
                
                # Success - return the sanitized output
                return DCToolResult(
                    output=sanitized_output
                )
            except asyncio.TimeoutError:
                logger.error(f"Command timed out after {timeout} seconds")
                # Attempt to clean up by restarting the bash tool
                try:
                    await bash_tool(restart=True)
                except Exception:
                    pass
                return DCToolResult(
                    error=f"Command timed out after {timeout} seconds"
                )
        except Exception as e:
            logger.error(f"Error in production tool: {str(e)}")
            logger.error(traceback.format_exc())
            # Fall back to mock implementation
            logger.info("Falling back to mock implementation")
    
    # Mock implementation (fallback or when production tool is unavailable)
    logger.info(f"Using mock implementation for command: {command}")
    
    # Safe mock implementation with improved output for common read-only commands
    if command.startswith("ls"):
        # Simulate directory listing
        parts = command.split()
        directory = "/"
        for i, part in enumerate(parts):
            if i > 0 and not part.startswith("-"):
                directory = part
                break
        
        return DCToolResult(output=f"Mock directory listing for {directory}:\nfile1.txt\nfile2.txt\ndirectory1/")
    elif command.startswith("cat"):
        # Simulate file content
        parts = command.split()
        filename = "unknown"
        for i, part in enumerate(parts):
            if i > 0 and not part.startswith("-"):
                filename = part
                break
        
        return DCToolResult(output=f"Mock content of {filename}:\nThis is simulated content for {filename}\nLine 2\nLine 3")
    elif command.startswith("echo"):
        # Echo the text after "echo "
        return DCToolResult(output=command[5:].strip())
    elif command.startswith("pwd"):
        return DCToolResult(output="/mock/current/directory")
    elif command.startswith("grep"):
        return DCToolResult(output=f"Mock grep results for '{command}':\nLine 10: matching content\nLine 42: another match")
    elif command.startswith("find"):
        return DCToolResult(output=f"Mock find results for '{command}':\n/path/to/file1.txt\n/path/to/file2.txt")
    else:
        return DCToolResult(output=f"Mock execution of read-only command: {command}")

# Validator functions for parameter validation
def dc_validate_computer_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate computer tool parameters with namespace isolation.
    """
    # Check for required action parameter
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action")
    
    # Validate parameters based on action
    if action in ["move_mouse", "left_button_press"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, "Invalid coordinates format. Expected [x, y]"
    
    elif action == "type_text":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for type_text"
    
    return True, "Parameters valid"

def dc_validate_bash_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate bash tool parameters with namespace isolation.
    """
    # Check for required command parameter
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Validate it's a read-only command
    is_valid, validation_message = dc_validate_read_only_command(command)
    if not is_valid:
        return False, validation_message
    
    return True, "Parameters valid"

def dc_validate_read_only_command(command: str) -> tuple[bool, str]:
    """
    Validate that a command is safe and read-only.
    
    Uses multiple validation methods:
    1. Whitelist of approved commands
    2. Blacklist of dangerous operations
    3. Pattern matching for complex commands
    
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
    
    # 1. Whitelist of safe read-only commands
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
    
    # 2. Blacklist of dangerous patterns
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
    
    # 3. Command-specific validation
    if base_command in ["wget", "curl"]:
        # Only allow output to stdout, not to files
        if re.search(r"(?:-o|-O|--output|--output-document)\s+\S+", normalized_command) and \
           not re.search(r"(?:-o|-O|--output|--output-document)\s+-", normalized_command):
            return False, f"{base_command} cannot write to files, only to stdout"
    
    # 4. Check for potentially dangerous flags/arguments by command
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

def dc_sanitize_command_output(output: str) -> str:
    """
    Sanitize command output to handle binary data or special characters.
    
    Args:
        output: Command output string to sanitize
        
    Returns:
        Sanitized output string
    """
    if not output:
        return ""
    
    # Handle non-UTF-8 characters
    try:
        # Try to decode if it's bytes, otherwise use as is
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
    except (UnicodeDecodeError, AttributeError):
        # If there's an error, force replace problematic characters
        output = str(output).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    
    # Replace null bytes which can cause issues in string handling
    output = output.replace('\0', '␀')
    
    # Limit output length to prevent exceedingly large responses
    max_length = 10000
    if len(output) > max_length:
        truncated_message = f"\n\n[Output truncated, showing {max_length} of {len(output)} characters]"
        output = output[:max_length] + truncated_message
    
    # Filter out ANSI escape sequences (used for terminal colors and formatting)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    output = ansi_escape.sub('', output)
    
    # Replace unprintable characters with Unicode replacement character
    output = ''.join(char if char.isprintable() or char in '\n\r\t' else '�' for char in output)
    
    return output