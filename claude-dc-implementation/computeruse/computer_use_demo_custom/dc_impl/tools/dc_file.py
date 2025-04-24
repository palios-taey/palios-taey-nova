"""
Streaming-compatible file operations tool for Claude DC.

This module provides a secure, isolated file operations tool that supports
streaming for viewing, creating, and editing files with progress reporting.
"""

import asyncio
import logging
import time
import re
import traceback
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
    use_streaming_file = toggles.is_enabled("use_streaming_file")
    use_large_file_support = toggles.is_enabled("use_large_file_support")
except ImportError:
    logging.warning("Could not import feature toggles, using defaults")
    use_streaming_file = True
    use_large_file_support = True

# Set up logging
logger = logging.getLogger("dc_file")
logger.setLevel(logging.INFO)

# Add file handler for file operations logs if directory exists
logs_dir = Path("/home/computeruse/computer_use_demo_custom/dc_impl/logs")
logs_dir.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(logs_dir / "dc_file.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Constants for file operations
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB maximum file size for streaming
CHUNK_SIZE = 8192  # 8KB chunks for streaming
LINE_NUMBERED_VIEW = True  # Whether to add line numbers when viewing files
MAX_LINES_PER_CHUNK = 100  # Maximum lines to yield at once
ALLOWED_OPERATIONS = ["view", "create", "str_replace", "insert", "undo_edit"]  # Allowed operations

def dc_validate_file_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate parameters for file operations.
    
    Args:
        tool_input: The tool input parameters
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required parameters
    if "command" not in tool_input:
        return False, "Missing required 'command' parameter"
    
    command = tool_input.get("command")
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Check if command is allowed
    if command not in ALLOWED_OPERATIONS:
        return False, f"Invalid command: {command}. Allowed commands: {', '.join(ALLOWED_OPERATIONS)}"
    
    # Check for required path parameter
    if "path" not in tool_input:
        return False, "Missing required 'path' parameter"
    
    path = tool_input.get("path")
    if not path or not isinstance(path, str):
        return False, "Path must be a non-empty string"
    
    # Validate path
    try:
        path_obj = Path(path).resolve()
        
        # Check for directory traversal attempts
        if "../" in path or ".." in path_obj.parts:
            return False, "Path cannot contain directory traversal"
        
        # Check if path is within allowed directories (add more restrictions if needed)
        allowed_prefixes = [
            "/home/computeruse/",
            "/tmp/",
        ]
        if not any(str(path_obj).startswith(prefix) for prefix in allowed_prefixes):
            return False, f"Path must be within allowed directories: {', '.join(allowed_prefixes)}"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"
    
    # Command-specific validation
    if command == "view":
        # Check if path exists for view operation
        if tool_input.get("view_range") and not isinstance(tool_input.get("view_range"), list):
            return False, "view_range must be a list of two integers"
    
    elif command == "create":
        # Check for file_text for create operation
        if "file_text" not in tool_input:
            return False, "Missing required 'file_text' parameter for create command"
        
        # Check if path already exists for create operation
        if Path(path).exists():
            return False, f"Cannot create file: path already exists ({path})"
    
    elif command == "str_replace":
        # Check for required parameters for str_replace
        if "old_str" not in tool_input:
            return False, "Missing required 'old_str' parameter for str_replace command"
        
        if "new_str" not in tool_input:
            # new_str can be empty, but must be present
            tool_input["new_str"] = ""
        
        # Check if path exists for str_replace
        if not Path(path).exists():
            return False, f"Cannot replace string: file does not exist ({path})"
    
    elif command == "insert":
        # Check for required parameters for insert
        if "insert_line" not in tool_input:
            return False, "Missing required 'insert_line' parameter for insert command"
        
        if "new_str" not in tool_input:
            return False, "Missing required 'new_str' parameter for insert command"
        
        # Validate insert_line is a valid integer
        try:
            insert_line = int(tool_input.get("insert_line"))
            if insert_line < 0:
                return False, "insert_line must be a non-negative integer"
        except (ValueError, TypeError):
            return False, "insert_line must be an integer"
        
        # Check if path exists for insert
        if not Path(path).exists():
            return False, f"Cannot insert: file does not exist ({path})"
    
    return True, "Parameters valid"

async def dc_file_view_streaming(
    path: str,
    view_range: Optional[List[int]] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Stream the contents of a file, optionally with line numbers and range limiting.
    
    Args:
        path: Path to the file
        view_range: Optional line range to view [start, end]
        progress_callback: Optional callback for progress updates
        
    Yields:
        File content chunks
    """
    try:
        file_path = Path(path).resolve()
        
        # Check if file exists
        if not file_path.exists():
            yield f"Error: File not found: {path}"
            return
        
        # Check if it's a file
        if not file_path.is_file():
            yield f"Error: Not a file: {path}"
            return
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE and not use_large_file_support:
            yield f"Error: File too large ({file_size} bytes). Maximum size: {MAX_FILE_SIZE} bytes"
            return
        
        # Report start
        if progress_callback:
            await progress_callback(f"Reading file: {path}", 0.0)
            
        # Yield file info header
        yield f"File: {path}\n"
        yield f"Size: {file_size} bytes\n"
        
        # Process view range
        start_line = 1
        max_lines = None  # No limit by default
        
        if view_range and len(view_range) == 2:
            start_line = max(1, view_range[0])
            if view_range[1] > 0:
                max_lines = view_range[1] - start_line + 1
        
        # Stream file contents
        bytes_read = 0
        line_count = 0
        digits = 6  # Default width for line numbers
        
        logger.info(f"Starting file view streaming with params: start_line={start_line}, max_lines={max_lines}")
        
        # Open file and read line by line
        with open(file_path, 'r', errors='replace') as f:
            # Skip lines before start_line
            for _ in range(1, start_line):
                line = f.readline()
                if not line:
                    break
                bytes_read += len(line)
            
            # Read lines in the specified range
            buffer = []
            current_line = start_line
            
            while True:
                # Check if we've reached the maximum number of lines
                if max_lines is not None and line_count >= max_lines:
                    break
                
                # Read next line
                line = f.readline()
                if not line:
                    break  # End of file
                
                # Update counters
                bytes_read += len(line)
                line_count += 1
                
                # Format line with number if enabled
                if LINE_NUMBERED_VIEW:
                    formatted_line = f"{current_line:>{digits}}: {line}"
                else:
                    formatted_line = line
                
                buffer.append(formatted_line)
                current_line += 1
                
                # Yield buffer when it reaches the chunk size
                if len(buffer) >= MAX_LINES_PER_CHUNK:
                    chunk = "".join(buffer)
                    yield chunk
                    buffer = []
                    
                    # Report progress if callback provided
                    if progress_callback and file_size > 0:
                        progress = min(0.99, bytes_read / file_size)
                        await progress_callback(
                            f"Reading {path} ({line_count} lines, {bytes_read/1024:.1f}KB)", 
                            progress
                        )
            
            # Yield any remaining lines in the buffer
            if buffer:
                chunk = "".join(buffer)
                yield chunk
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed reading {path}", 1.0)
            
        # Yield summary footer
        yield f"\n{line_count} lines read"
    
    except Exception as e:
        logger.error(f"Error reading file {path}: {str(e)}")
        logger.error(traceback.format_exc())
        yield f"Error reading file: {str(e)}"
        
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)

async def dc_file_create_streaming(
    path: str,
    file_text: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Create a new file with streaming progress updates.
    
    Args:
        path: Path to create the file
        file_text: Content to write to the file
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates on the file creation
    """
    try:
        file_path = Path(path).resolve()
        
        # Check if file already exists
        if file_path.exists():
            yield f"Error: File already exists: {path}"
            return
        
        # Check directory
        parent_dir = file_path.parent
        if not parent_dir.exists():
            yield f"Creating directory: {parent_dir}"
            parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Report start
        if progress_callback:
            await progress_callback(f"Creating file: {path}", 0.0)
        
        yield f"Creating file: {path}\n"
        
        # Get content size
        content_size = len(file_text)
        yield f"Content size: {content_size} bytes\n"
        
        # Simulate processing for very large content
        if content_size > 100000:
            yield "Processing large content..."
            
            # Report progress at intervals
            if progress_callback:
                await progress_callback(f"Processing content for {path}", 0.3)
            
            # Small delay to allow processing
            await asyncio.sleep(0.1)
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(file_text)
        
        # Report progress
        if progress_callback:
            await progress_callback(f"Writing content to {path}", 0.8)
        
        # Calculate line count
        line_count = file_text.count('\n') + 1
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed creating {path}", 1.0)
        
        yield f"File created successfully: {path}\n"
        yield f"Wrote {line_count} lines, {content_size} bytes"
    
    except Exception as e:
        logger.error(f"Error creating file {path}: {str(e)}")
        logger.error(traceback.format_exc())
        yield f"Error creating file: {str(e)}"
        
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)

async def dc_file_str_replace_streaming(
    path: str,
    old_str: str,
    new_str: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Replace a string in a file with streaming progress updates.
    
    Args:
        path: Path to the file
        old_str: String to replace
        new_str: New string
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates on the string replacement
    """
    try:
        file_path = Path(path).resolve()
        
        # Check if file exists
        if not file_path.exists():
            yield f"Error: File not found: {path}"
            return
            
        # Check if it's a file
        if not file_path.is_file():
            yield f"Error: Not a file: {path}"
            return
        
        # Report start
        if progress_callback:
            await progress_callback(f"Reading file for replacement: {path}", 0.0)
        
        yield f"Replacing text in file: {path}\n"
        
        # Read file content
        with open(file_path, 'r', errors='replace') as f:
            content = f.read()
        
        # Check if old_str exists in the file
        if old_str not in content:
            yield f"Error: String to replace not found in file"
            return
        
        # Count occurrences
        count = content.count(old_str)
        
        # Report progress
        if progress_callback:
            await progress_callback(f"Found {count} occurrences in {path}", 0.3)
        
        yield f"Found {count} occurrence(s) of the string to replace\n"
        
        # Calculate size difference
        size_diff = len(new_str) - len(old_str)
        new_size = len(content) + (size_diff * count)
        
        yield f"Original size: {len(content)} bytes\n"
        yield f"Estimated new size: {new_size} bytes\n"
        
        # Report progress before replacement
        if progress_callback:
            await progress_callback(f"Replacing strings in {path}", 0.6)
        
        # Perform replacement
        new_content = content.replace(old_str, new_str)
        
        # Write updated content
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        # Report progress after writing
        if progress_callback:
            await progress_callback(f"Writing changes to {path}", 0.9)
        
        yield f"Replacement completed\n"
        yield f"Replaced {count} occurrence(s)"
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed updating {path}", 1.0)
    
    except Exception as e:
        logger.error(f"Error replacing string in file {path}: {str(e)}")
        logger.error(traceback.format_exc())
        yield f"Error replacing string: {str(e)}"
        
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)

async def dc_file_insert_streaming(
    path: str,
    insert_line: int,
    new_str: str,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Insert a string at a specific line in a file with streaming progress updates.
    
    Args:
        path: Path to the file
        insert_line: Line number after which to insert
        new_str: String to insert
        progress_callback: Optional callback for progress updates
        
    Yields:
        Status updates on the insertion
    """
    try:
        file_path = Path(path).resolve()
        
        # Check if file exists
        if not file_path.exists():
            yield f"Error: File not found: {path}"
            return
            
        # Check if it's a file
        if not file_path.is_file():
            yield f"Error: Not a file: {path}"
            return
        
        # Report start
        if progress_callback:
            await progress_callback(f"Reading file for insertion: {path}", 0.0)
        
        yield f"Inserting text in file: {path}\n"
        
        # Read lines from file
        with open(file_path, 'r', errors='replace') as f:
            lines = f.readlines()
        
        # Check if insert_line is valid
        if insert_line < 0 or insert_line > len(lines):
            yield f"Error: Invalid insert_line {insert_line}. File has {len(lines)} lines"
            return
        
        # Ensure new_str ends with a newline if not empty
        if new_str and not new_str.endswith('\n'):
            new_str += '\n'
        
        # Report progress
        if progress_callback:
            await progress_callback(f"Inserting text at line {insert_line}", 0.5)
        
        yield f"Preparing to insert after line {insert_line}\n"
        
        # Perform the insertion
        lines.insert(insert_line, new_str)
        
        # Write updated content
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        # Report completion
        if progress_callback:
            await progress_callback(f"Completed inserting at line {insert_line}", 1.0)
        
        yield f"Insertion completed\n"
        yield f"New file has {len(lines)} lines"
    
    except Exception as e:
        logger.error(f"Error inserting in file {path}: {str(e)}")
        logger.error(traceback.format_exc())
        yield f"Error inserting text: {str(e)}"
        
        if progress_callback:
            await progress_callback(f"Error: {str(e)}", 1.0)

async def dc_execute_file_tool_streaming(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a file operation with streaming output.
    
    Args:
        tool_input: The input parameters
        progress_callback: Optional callback for progress updates
        
    Yields:
        Operation output chunks as they become available
    """
    # Validate parameters
    is_valid, message = dc_validate_file_parameters(tool_input)
    if not is_valid:
        logger.warning(f"File operation validation failed: {message}")
        yield f"Error: {message}"
        return
    
    command = tool_input.get("command")
    path = tool_input.get("path")
    
    logger.info(f"Executing file operation: {command} on {path}")
    
    # Execute the appropriate command
    if command == "view":
        view_range = tool_input.get("view_range")
        async for chunk in dc_file_view_streaming(path, view_range, progress_callback):
            yield chunk
    
    elif command == "create":
        file_text = tool_input.get("file_text", "")
        async for chunk in dc_file_create_streaming(path, file_text, progress_callback):
            yield chunk
    
    elif command == "str_replace":
        old_str = tool_input.get("old_str", "")
        new_str = tool_input.get("new_str", "")
        async for chunk in dc_file_str_replace_streaming(path, old_str, new_str, progress_callback):
            yield chunk
    
    elif command == "insert":
        insert_line = int(tool_input.get("insert_line", 0))
        new_str = tool_input.get("new_str", "")
        async for chunk in dc_file_insert_streaming(path, insert_line, new_str, progress_callback):
            yield chunk
    
    elif command == "undo_edit":
        # For now, we'll return an informational message
        yield "The undo_edit operation is not yet implemented in streaming mode"
    
    else:
        # This shouldn't happen due to validation, but just in case
        yield f"Error: Unknown command: {command}"

async def dc_process_streaming_output(
    generator: AsyncGenerator[str, None]
) -> DCToolResult:
    """
    Process streaming output and collect it into a DCToolResult.
    
    Args:
        generator: An async generator yielding file operation output
        
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

# Non-streaming function for compatibility
async def dc_execute_file_tool(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Execute file operation and return DCToolResult (non-streaming wrapper).
    
    Args:
        tool_input: The input parameters
        
    Returns:
        DCToolResult with operation output/error
    """
    generator = dc_execute_file_tool_streaming(tool_input)
    return await dc_process_streaming_output(generator)

# Demo function for testing the streaming implementation
async def demo_streaming_file():
    """Demo function to test the streaming file implementation."""
    print("\nTesting streaming file implementation\n")
    
    # Create a test file
    test_file = "/tmp/streaming_test.txt"
    with open(test_file, "w") as f:
        f.write("Line 1: This is a test file for streaming file operations.\n")
        f.write("Line 2: It contains multiple lines of text.\n")
        f.write("Line 3: We'll use this to test the streaming functionality.\n")
        for i in range(4, 20):
            f.write(f"Line {i}: Additional test content for line {i}.\n")
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    print(f"Testing view operation on {test_file}")
    print("-" * 50)
    
    # Execute with streaming
    async for chunk in dc_execute_file_tool_streaming(
        {"command": "view", "path": test_file},
        progress_callback=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    print("\n\nDone!")

# Entry point for direct script execution
if __name__ == "__main__":
    asyncio.run(demo_streaming_file())