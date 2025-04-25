"""
File editing tool with streaming support.

This module provides a streaming-compatible tool for viewing, creating, and editing files.
It includes proper validation, safety controls, and real-time progress updates.
"""

import asyncio
import logging
import time
import os
import re
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List, Tuple, Union

from models.tool_models import ToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("edit_tool")

# Constants for security controls
MAX_FILE_SIZE = 1024 * 1024 * 10  # 10MB maximum file size
SAFE_PATH_PREFIXES = [
    "/home/computeruse",
    "/home/jesse",
    "/tmp"
]

# Validator for file paths
def validate_file_path(file_path: str) -> Tuple[bool, str]:
    """
    Validate that a file path is safe.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not file_path:
        return False, "Empty file path"
    
    # Convert to absolute path
    path = Path(file_path).resolve()
    path_str = str(path)
    
    # Check if path is within allowed directories
    if not any(path_str.startswith(prefix) for prefix in SAFE_PATH_PREFIXES):
        return False, f"Path must be within allowed directories: {', '.join(SAFE_PATH_PREFIXES)}"
    
    # Check for potentially dangerous paths
    dangerous_patterns = [
        r"/etc/(passwd|shadow|sudoers)",
        r"/var/log/auth\.log",
        r"/root/",
        r"/sys/",
        r"/boot/",
        r"\.ssh/",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, path_str):
            return False, f"Path matches potentially dangerous pattern: {pattern}"
    
    return True, "Path validated"

# Validator for edit parameters
def validate_edit_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for the edit tool.
    
    Args:
        tool_input: The tool input parameters
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required parameters
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    if "path" not in tool_input:
        return False, "Missing required 'path' parameter"
    
    # Validate command
    command = tool_input.get("command")
    valid_commands = ["view", "create", "str_replace", "insert", "undo_edit"]
    if command not in valid_commands:
        return False, f"Invalid command: {command}. Valid commands: {', '.join(valid_commands)}"
    
    # Validate path
    path = tool_input.get("path")
    path_valid, path_message = validate_file_path(path)
    if not path_valid:
        return False, path_message
    
    # Command-specific validation
    if command == "str_replace":
        if "old_string" not in tool_input:
            return False, "Missing required 'old_string' parameter for str_replace"
        if "new_string" not in tool_input:
            return False, "Missing required 'new_string' parameter for str_replace"
    
    elif command == "insert":
        if "content" not in tool_input:
            return False, "Missing required 'content' parameter for insert"
    
    return True, "Parameters valid"

async def execute_edit_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> ToolResult:
    """
    Execute a file editing operation with streaming progress.
    
    Args:
        tool_input: The tool input parameters
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the operation result
    """
    # Extract parameters
    command = tool_input.get("command", "")
    path = tool_input.get("path", "")
    
    if not command or not path:
        return ToolResult(error="Missing command or path")
    
    logger.info(f"Executing edit command: {command} on path: {path}")
    start_time = time.time()
    
    # Validate parameters
    valid, message = validate_edit_parameters(tool_input)
    if not valid:
        logger.warning(f"Parameter validation failed: {message}")
        return ToolResult(error=message)
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting {command} operation on {path}", 0.0)
    
    try:
        # Execute the appropriate command
        if command == "view":
            # View file content
            result = await view_file(path, progress_callback)
        
        elif command == "create":
            # Create a new file
            content = tool_input.get("content", "")
            result = await create_file(path, content, progress_callback)
        
        elif command == "str_replace":
            # Replace string in file
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")
            expected_replacements = tool_input.get("expected_replacements", 1)
            result = await str_replace(path, old_string, new_string, expected_replacements, progress_callback)
        
        elif command == "insert":
            # Insert content in file
            content = tool_input.get("content", "")
            position = tool_input.get("position", "end")
            result = await insert_content(path, content, position, progress_callback)
        
        else:
            result = ToolResult(error=f"Unsupported command: {command}")
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed {command} operation on {path}", 1.0)
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing edit command: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Report error in progress
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)
        
        # Return error message
        return ToolResult(error=f"Error executing {command} operation: {str(e)}\n{traceback.format_exc()}")

# Mark function as supporting streaming
execute_edit_streaming.streaming = True

async def view_file(
    path: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> ToolResult:
    """
    View file content with streaming progress.
    
    Args:
        path: The file path
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with file content
    """
    file_path = Path(path).resolve()
    
    try:
        # Check if file exists
        if not file_path.exists():
            return ToolResult(error=f"File not found: {path}")
        
        # Check if it's a file (not a directory)
        if not file_path.is_file():
            return ToolResult(error=f"Not a file: {path}")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            warning = f"Warning: File size ({file_size} bytes) exceeds maximum allowed size. Showing first part only.\n\n"
        else:
            warning = ""
        
        # Initial progress update
        if progress_callback:
            await progress_callback(f"Reading file: {path}", 0.1)
        
        # Read file in chunks
        output = []
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Read in chunks of 4KB
            chunk_size = 4096
            bytes_read = 0
            line_number = 1
            
            # Start with a header
            output.append(f"File: {path}\n")
            output.append(f"Size: {file_size} bytes\n\n")
            
            if warning:
                output.append(warning)
            
            # Read and format file content
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                # Format with line numbers
                lines = chunk.split('\n')
                formatted_chunk = ""
                
                for i, line in enumerate(lines):
                    # Skip the last line if it's not complete (unless it's the end of the file)
                    if i == len(lines) - 1 and chunk_size == 4096:
                        # Check if we're at the end of the file
                        pos = f.tell()
                        if pos < file_size:
                            # We're not at the end yet, so this line is incomplete
                            f.seek(pos - len(lines[-1]))
                            break
                    
                    # Add line number
                    formatted_chunk += f"{line_number:6d} | {line}\n"
                    line_number += 1
                
                # Add the formatted chunk to output
                output.append(formatted_chunk)
                
                # Update bytes read
                bytes_read += len(chunk)
                
                # Update progress
                if progress_callback and file_size > 0:
                    progress = min(0.99, bytes_read / file_size)
                    await progress_callback(
                        f"Reading file: {path} ({bytes_read}/{file_size} bytes)", 
                        progress
                    )
                
                # Check if we've reached the size limit
                if bytes_read >= MAX_FILE_SIZE:
                    output.append(f"\n\nFile truncated at {MAX_FILE_SIZE} bytes. Full size: {file_size} bytes")
                    break
                
                # Small delay to allow for cancellation
                await asyncio.sleep(0.01)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"Completed reading file: {path}", 1.0)
        
        return ToolResult(output="".join(output))
    
    except UnicodeDecodeError:
        return ToolResult(error=f"Unable to read file as text: {path}. It may be a binary file.")
    
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return ToolResult(error=f"Error reading file: {str(e)}")

async def create_file(
    path: str,
    content: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> ToolResult:
    """
    Create a new file with streaming progress.
    
    Args:
        path: The file path
        content: The content to write
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with status
    """
    file_path = Path(path).resolve()
    
    try:
        # Initial progress update
        if progress_callback:
            await progress_callback(f"Creating file: {path}", 0.1)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Progress update before writing
        if progress_callback:
            await progress_callback(f"Writing content to file: {path}", 0.5)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"File created: {path}", 1.0)
        
        # Calculate stats
        file_size = file_path.stat().st_size
        line_count = content.count('\n') + 1
        
        return ToolResult(output=f"File created: {path}\nSize: {file_size} bytes\nLines: {line_count}")
    
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}")
        return ToolResult(error=f"Error creating file: {str(e)}")

async def str_replace(
    path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> ToolResult:
    """
    Replace text in a file with streaming progress.
    
    Args:
        path: The file path
        old_string: The text to replace
        new_string: The replacement text
        expected_replacements: Expected number of replacements
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with status
    """
    file_path = Path(path).resolve()
    
    try:
        # Check if file exists
        if not file_path.exists():
            return ToolResult(error=f"File not found: {path}")
        
        # Initial progress update
        if progress_callback:
            await progress_callback(f"Reading file for replacement: {path}", 0.1)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Perform replacement
        if progress_callback:
            await progress_callback(f"Performing replacements in {path}", 0.4)
        
        # Count occurrences before replacement
        occurrences = content.count(old_string)
        
        # Check if expected replacements matches actual occurrences
        if expected_replacements != occurrences:
            return ToolResult(error=f"Expected {expected_replacements} replacements, but found {occurrences} occurrences of the string to replace")
        
        # Perform replacement
        new_content = content.replace(old_string, new_string, expected_replacements)
        
        # Check if any changes were made
        if new_content == content:
            return ToolResult(output=f"No changes made: The specified string was not found in {path}")
        
        # Write back to file
        if progress_callback:
            await progress_callback(f"Writing changes to {path}", 0.7)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"Replacement completed in {path}", 1.0)
        
        return ToolResult(output=f"Successfully replaced {occurrences} occurrence(s) in {path}")
    
    except Exception as e:
        logger.error(f"Error replacing text in file: {str(e)}")
        return ToolResult(error=f"Error replacing text in file: {str(e)}")

async def insert_content(
    path: str,
    content: str,
    position: str = "end",
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> ToolResult:
    """
    Insert content into a file with streaming progress.
    
    Args:
        path: The file path
        content: The content to insert
        position: Where to insert the content (start, end, or line number)
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with status
    """
    file_path = Path(path).resolve()
    
    try:
        # Create file if it doesn't exist
        if not file_path.exists():
            if progress_callback:
                await progress_callback(f"Creating new file: {path}", 0.2)
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if progress_callback:
                await progress_callback(f"Created new file: {path}", 1.0)
            
            return ToolResult(output=f"Created new file with content: {path}")
        
        # Read existing content
        if progress_callback:
            await progress_callback(f"Reading file for insertion: {path}", 0.2)
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            existing_content = f.read()
        
        # Determine where to insert
        if progress_callback:
            await progress_callback(f"Inserting content in {path}", 0.5)
        
        if position == "start":
            # Insert at the beginning
            new_content = content + existing_content
        elif position == "end":
            # Insert at the end
            new_content = existing_content + content
        else:
            try:
                # Try to parse position as line number
                line_number = int(position)
                lines = existing_content.splitlines(True)
                
                if line_number <= 0:
                    # Insert at the beginning
                    new_content = content + existing_content
                elif line_number > len(lines):
                    # Insert at the end
                    new_content = existing_content + content
                else:
                    # Insert at the specified line
                    before = ''.join(lines[:line_number-1])
                    after = ''.join(lines[line_number-1:])
                    new_content = before + content + after
            except ValueError:
                # Invalid position, insert at the end
                new_content = existing_content + content
        
        # Write the new content
        if progress_callback:
            await progress_callback(f"Writing updated content to {path}", 0.8)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"Content insertion completed in {path}", 1.0)
        
        return ToolResult(output=f"Successfully inserted content at {position} in {path}")
    
    except Exception as e:
        logger.error(f"Error inserting content in file: {str(e)}")
        return ToolResult(error=f"Error inserting content in file: {str(e)}")

async def execute_edit(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute an edit command (non-streaming wrapper).
    
    Args:
        tool_input: The tool input parameters
        
    Returns:
        ToolResult with the operation result
    """
    return await execute_edit_streaming(tool_input)

# Test function for direct execution
async def test_edit_tool():
    """Test the edit tool."""
    print("\nTesting edit tool...\n")
    
    # Create a test file
    test_file = "/tmp/edit_tool_test.txt"
    test_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Test viewing file
    print("\nViewing file:")
    result = await execute_edit_streaming(
        {"command": "view", "path": test_file},
        progress_callback=progress_callback
    )
    
    if result.error:
        print(f"\nError: {result.error}")
    else:
        print(f"\nOutput: {result.output}")
    
    # Test string replacement
    print("\nReplacing 'Line 3' with 'REPLACED LINE':")
    result = await execute_edit_streaming(
        {
            "command": "str_replace",
            "path": test_file,
            "old_string": "Line 3",
            "new_string": "REPLACED LINE",
            "expected_replacements": 1
        },
        progress_callback=progress_callback
    )
    
    if result.error:
        print(f"\nError: {result.error}")
    else:
        print(f"\nOutput: {result.output}")
    
    # Clean up
    os.remove(test_file)
    print("\nTest completed and cleaned up.")

if __name__ == "__main__":
    asyncio.run(test_edit_tool())