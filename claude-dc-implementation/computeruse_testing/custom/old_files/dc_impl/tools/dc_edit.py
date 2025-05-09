"""
Streaming-compatible file editing tool implementation for Claude DC.

This module provides a secure, isolated file editor tool that supports streaming
capabilities. It includes validation, safety controls, and proper error handling
for file operations executed in the Claude DC environment.
"""

import asyncio
import logging
import time
import os
import re
import traceback
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

# Set up logging
logger = logging.getLogger("dc_edit")
logger.setLevel(logging.INFO)

# Add file handler for edit logs if directory exists
logs_dir = Path("/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/logs")
logs_dir.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(logs_dir / "dc_edit.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Constants for security controls
MAX_FILE_SIZE = 1024 * 1024 * 10  # 10MB maximum file size
SAFE_PATH_PREFIXES = [
    "/home/computeruse",
    "/home/jesse",
    "/tmp"
]

# Validator for file paths
def dc_validate_file_path(file_path: str) -> Tuple[bool, str]:
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

# Validator for edit tool parameters
def dc_validate_edit_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
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
    path_valid, path_message = dc_validate_file_path(path)
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

async def dc_execute_edit_tool_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a file editing operation with streaming output.
    
    Args:
        tool_input: The tool input parameters
        progress_callback: Optional callback for progress updates
        
    Yields:
        Operation output chunks as they become available
    """
    # Extract parameters
    command = tool_input.get("command", "")
    path = tool_input.get("path", "")
    
    if not command or not path:
        yield "Error: Missing command or path"
        return
    
    logger.info(f"Executing edit command: {command} on path: {path}")
    start_time = time.time()
    
    # Validate parameters
    valid, message = dc_validate_edit_parameters(tool_input)
    if not valid:
        logger.warning(f"Parameter validation failed: {message}")
        yield f"Error: {message}"
        return
    
    # Report initial progress
    if progress_callback:
        await progress_callback(f"Starting {command} operation on {path}", 0.0)
    
    try:
        # Execute the appropriate command
        if command == "view":
            # View file content
            yield from dc_view_file_streaming(path, progress_callback)
        
        elif command == "create":
            # Create a new file
            content = tool_input.get("content", "")
            yield from dc_create_file_streaming(path, content, progress_callback)
        
        elif command == "str_replace":
            # Replace string in file
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")
            expected_replacements = tool_input.get("expected_replacements", 1)
            yield from dc_str_replace_streaming(path, old_string, new_string, expected_replacements, progress_callback)
        
        elif command == "insert":
            # Insert content in file
            content = tool_input.get("content", "")
            position = tool_input.get("position", "end")
            yield from dc_insert_content_streaming(path, content, position, progress_callback)
        
        else:
            yield f"Error: Unsupported command: {command}"
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed {command} operation on {path}", 1.0)
    
    except Exception as e:
        logger.error(f"Error executing edit command: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Report error in progress
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)
        
        # Yield error message
        yield f"Error executing {command} operation: {str(e)}\n{traceback.format_exc()}"

async def dc_view_file_streaming(
    path: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    View file content with streaming output.
    
    Args:
        path: The file path
        progress_callback: Optional callback for progress updates
        
    Yields:
        File content chunks as they become available
    """
    file_path = Path(path).resolve()
    
    try:
        # Check if file exists
        if not file_path.exists():
            yield f"Error: File not found: {path}"
            return
        
        # Check if it's a file (not a directory)
        if not file_path.is_file():
            yield f"Error: Not a file: {path}"
            return
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            yield f"Warning: File size ({file_size} bytes) exceeds maximum allowed size. Showing first part only.\n\n"
        
        # Read file in chunks
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Read in chunks of 4KB
            chunk_size = 4096
            bytes_read = 0
            line_number = 1
            
            # Start with a header
            yield f"File: {path}\n"
            yield f"Size: {file_size} bytes\n\n"
            
            # Read and yield file content in chunks
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
                
                # Yield the formatted chunk
                yield formatted_chunk
                
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
                    yield f"\n\nFile truncated at {MAX_FILE_SIZE} bytes. Full size: {file_size} bytes"
                    break
                
                # Small delay to allow for cancellation
                await asyncio.sleep(0.01)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"Completed reading file: {path}", 1.0)
    
    except UnicodeDecodeError:
        yield f"Error: Unable to read file as text: {path}. It may be a binary file."
    
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        yield f"Error reading file: {str(e)}"

async def dc_create_file_streaming(
    path: str,
    content: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Create a new file with streaming progress.
    
    Args:
        path: The file path
        content: The content to write
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates as the operation progresses
    """
    file_path = Path(path).resolve()
    
    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initial progress update
        if progress_callback:
            await progress_callback(f"Creating file: {path}", 0.25)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"File created: {path}", 1.0)
        
        # Calculate stats
        file_size = file_path.stat().st_size
        line_count = content.count('\n') + 1
        
        # Yield success message
        yield f"File created: {path}\n"
        yield f"Size: {file_size} bytes\n"
        yield f"Lines: {line_count}"
    
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}")
        yield f"Error creating file: {str(e)}"

async def dc_str_replace_streaming(
    path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Replace text in a file with streaming progress.
    
    Args:
        path: The file path
        old_string: The text to replace
        new_string: The replacement text
        expected_replacements: Expected number of replacements
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates as the operation progresses
    """
    file_path = Path(path).resolve()
    
    try:
        # Check if file exists
        if not file_path.exists():
            yield f"Error: File not found: {path}"
            return
        
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
            yield f"Error: Expected {expected_replacements} replacements, but found {occurrences} occurrences of the string to replace"
            return
        
        # Perform replacement
        new_content = content.replace(old_string, new_string, expected_replacements)
        
        # Check if any changes were made
        if new_content == content:
            yield f"No changes made: The specified string was not found in {path}"
            return
        
        # Write back to file
        if progress_callback:
            await progress_callback(f"Writing changes to {path}", 0.7)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Final progress update
        if progress_callback:
            await progress_callback(f"Replacement completed in {path}", 1.0)
        
        # Yield success message
        yield f"Successfully replaced {occurrences} occurrence(s) in {path}"
    
    except Exception as e:
        logger.error(f"Error replacing text in file: {str(e)}")
        yield f"Error replacing text in file: {str(e)}"

async def dc_insert_content_streaming(
    path: str,
    content: str,
    position: str = "end",
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Insert content into a file with streaming progress.
    
    Args:
        path: The file path
        content: The content to insert
        position: Where to insert the content (start, end, or line number)
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates as the operation progresses
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
            
            yield f"Created new file with content: {path}"
            return
        
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
        
        # Yield success message
        yield f"Successfully inserted content at {position} in {path}"
    
    except Exception as e:
        logger.error(f"Error inserting content in file: {str(e)}")
        yield f"Error inserting content in file: {str(e)}"

# Function to process streaming output for tool results
async def dc_process_edit_streaming_output(
    generator: AsyncGenerator[str, None]
) -> DCToolResult:
    """
    Process streaming output and collect it into a DCToolResult.
    
    Args:
        generator: An async generator yielding operation output
        
    Returns:
        DCToolResult with collected output/error
    """
    output_chunks = []
    error_chunks = []
    
    try:
        async for chunk in generator:
            # Check if this is an error message
            if chunk.startswith("Error:"):
                error_chunks.append(chunk)
            else:
                output_chunks.append(chunk)
    except Exception as e:
        error_chunks.append(f"Error processing output: {str(e)}")
    
    if error_chunks:
        return DCToolResult(error="".join(error_chunks))
    else:
        return DCToolResult(output="".join(output_chunks))

# Function to execute edit command and convert to DCToolResult (for compatibility)
async def dc_execute_edit_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Execute edit command and return DCToolResult (non-streaming wrapper).
    
    Args:
        tool_input: The input parameters
        
    Returns:
        DCToolResult with operation output/error
    """
    # Validate input parameters
    valid, message = dc_validate_edit_parameters(tool_input)
    if not valid:
        return DCToolResult(error=message)
    
    # Execute command with streaming and collect results
    generator = dc_execute_edit_tool_streaming(tool_input)
    return await dc_process_edit_streaming_output(generator)

# Demo function for testing
async def demo_edit_streaming():
    """Demo function to test the streaming edit implementation."""
    print("\nTesting DC streaming edit implementation\n")
    
    # Create a test file
    test_file = "/tmp/dc_edit_test_file.txt"
    test_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    print(f"Created test file: {test_file}")
    
    # Test viewing file
    print("\nViewing file:")
    async for chunk in dc_execute_edit_tool_streaming(
        {"command": "view", "path": test_file},
        progress_callback=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    # Test string replacement
    print("\n\nReplacing 'Line 3' with 'REPLACED LINE':")
    async for chunk in dc_execute_edit_tool_streaming(
        {
            "command": "str_replace", 
            "path": test_file,
            "old_string": "Line 3", 
            "new_string": "REPLACED LINE",
            "expected_replacements": 1
        },
        progress_callback=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    # View the file again to see the changes
    print("\n\nViewing file after replacement:")
    async for chunk in dc_execute_edit_tool_streaming(
        {"command": "view", "path": test_file},
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
    asyncio.run(demo_edit_streaming())