"""
Test module for streaming file operations tool implementation.
"""

import pytest
import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the streaming file tool
from tools.dc_file import (
    dc_execute_file_tool_streaming,
    dc_process_streaming_output,
    dc_validate_file_parameters,
    ALLOWED_OPERATIONS
)

from models.dc_models import DCToolResult

@pytest.mark.asyncio
async def test_file_parameter_validation():
    """Test validation of file operation parameters."""
    # Valid parameters
    valid_params = [
        {"command": "view", "path": "/tmp/test.txt"},
        {"command": "create", "path": "/tmp/new_file.txt", "file_text": "test content"},
        {"command": "str_replace", "path": "/tmp/test.txt", "old_str": "old", "new_str": "new"},
        {"command": "insert", "path": "/tmp/test.txt", "insert_line": 1, "new_str": "insert"},
        {"command": "view", "path": "/tmp/test.txt", "view_range": [1, 10]}
    ]
    
    for params in valid_params:
        is_valid, message = dc_validate_file_parameters(params)
        assert is_valid, f"Parameters should be valid: {params}, error: {message}"
    
    # Invalid parameters
    invalid_params = [
        {},  # Missing command
        {"command": "view"},  # Missing path
        {"command": "invalid", "path": "/tmp/test.txt"},  # Invalid command
        {"command": "create", "path": "/tmp/test.txt"},  # Missing file_text
        {"command": "str_replace", "path": "/tmp/test.txt", "new_str": "new"},  # Missing old_str
        {"command": "insert", "path": "/tmp/test.txt", "new_str": "insert"},  # Missing insert_line
        {"command": "view", "path": "../forbidden.txt"}  # Directory traversal attempt
    ]
    
    for params in invalid_params:
        is_valid, message = dc_validate_file_parameters(params)
        assert not is_valid, f"Parameters should be invalid: {params}"

@pytest.mark.asyncio
async def test_streaming_output_collection():
    """Test collection of streaming output."""
    async def dummy_stream():
        yield "File: test.txt\n"
        yield "Size: 100 bytes\n"
        yield "1: Line 1\n"
        yield "2: Line 2\n"
    
    result = await dc_process_streaming_output(dummy_stream())
    assert isinstance(result, DCToolResult)
    assert "File: test.txt" in result.output
    assert "Line 1" in result.output
    assert result.error is None

@pytest.mark.asyncio
async def test_streaming_error_collection():
    """Test collection of streaming errors."""
    async def dummy_error_stream():
        yield "Error: File not found\n"
        yield "More error details\n"
    
    result = await dc_process_streaming_output(dummy_error_stream())
    assert isinstance(result, DCToolResult)
    assert result.error == "Error: File not found\nMore error details\n"
    assert result.output is None

@pytest.mark.asyncio
async def test_file_view_operation():
    """Test streaming view operation on a file."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("Line 1: Test content\n")
        test_file.write("Line 2: More test content\n")
        test_file.write("Line 3: Final test content\n")
        test_path = test_file.name
    
    try:
        # Progress tracking
        progress_updates = []
        
        async def track_progress(message, progress):
            progress_updates.append((message, progress))
        
        # Collect output
        output = []
        async for chunk in dc_execute_file_tool_streaming(
            {"command": "view", "path": test_path},
            progress_callback=track_progress
        ):
            output.append(chunk)
        
        # Check output
        combined_output = "".join(output)
        assert "File:" in combined_output
        assert "Line 1: Test content" in combined_output
        assert "Line 3: Final test content" in combined_output
        
        # Check that progress was reported
        assert len(progress_updates) > 0
        # First update should be about reading
        assert progress_updates[0][0].startswith("Reading file")
        assert progress_updates[0][1] == 0.0
        # Last update should be completed
        assert progress_updates[-1][0].startswith("Completed")
        assert progress_updates[-1][1] == 1.0
    
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
        except:
            pass

@pytest.mark.asyncio
async def test_file_create_operation():
    """Test streaming create operation."""
    # Define a temporary file path
    test_path = tempfile.gettempdir() + "/streaming_create_test.txt"
    
    try:
        # Make sure file doesn't exist
        if os.path.exists(test_path):
            os.unlink(test_path)
        
        # Progress tracking
        progress_updates = []
        
        async def track_progress(message, progress):
            progress_updates.append((message, progress))
        
        # Test content
        test_content = "This is line 1\nThis is line 2\nThis is line 3\n"
        
        # Collect output
        output = []
        async for chunk in dc_execute_file_tool_streaming(
            {"command": "create", "path": test_path, "file_text": test_content},
            progress_callback=track_progress
        ):
            output.append(chunk)
        
        # Check output
        combined_output = "".join(output)
        assert "Creating file:" in combined_output
        assert "File created successfully" in combined_output
        
        # Check that progress was reported
        assert len(progress_updates) > 0
        
        # Verify file was created with correct content
        assert os.path.exists(test_path)
        with open(test_path, "r") as f:
            content = f.read()
            assert content == test_content
    
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
        except:
            pass

@pytest.mark.asyncio
async def test_file_str_replace_operation():
    """Test streaming str_replace operation."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("Line 1: Test content to replace\n")
        test_file.write("Line 2: More test content\n")
        test_file.write("Line 3: Test content to replace again\n")
        test_path = test_file.name
    
    try:
        # Progress tracking
        progress_updates = []
        
        async def track_progress(message, progress):
            progress_updates.append((message, progress))
        
        # Collect output
        output = []
        async for chunk in dc_execute_file_tool_streaming(
            {
                "command": "str_replace", 
                "path": test_path, 
                "old_str": "Test content to replace", 
                "new_str": "REPLACED CONTENT"
            },
            progress_callback=track_progress
        ):
            output.append(chunk)
        
        # Check output
        combined_output = "".join(output)
        assert "Replacing text in file" in combined_output
        assert "Replacement completed" in combined_output
        assert "2 occurrence(s)" in combined_output
        
        # Check that progress was reported
        assert len(progress_updates) > 0
        
        # Verify file was modified correctly
        with open(test_path, "r") as f:
            content = f.read()
            assert "REPLACED CONTENT" in content
            assert "Test content to replace" not in content
    
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
        except:
            pass

@pytest.mark.asyncio
async def test_file_insert_operation():
    """Test streaming insert operation."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("Line 1: First line\n")
        test_file.write("Line 2: Second line\n")
        test_path = test_file.name
    
    try:
        # Progress tracking
        progress_updates = []
        
        async def track_progress(message, progress):
            progress_updates.append((message, progress))
        
        # Collect output
        output = []
        async for chunk in dc_execute_file_tool_streaming(
            {
                "command": "insert", 
                "path": test_path, 
                "insert_line": 1, 
                "new_str": "INSERTED LINE\n"
            },
            progress_callback=track_progress
        ):
            output.append(chunk)
        
        # Check output
        combined_output = "".join(output)
        assert "Inserting text in file" in combined_output
        assert "Insertion completed" in combined_output
        
        # Check that progress was reported
        assert len(progress_updates) > 0
        
        # Verify file was modified correctly
        with open(test_path, "r") as f:
            content = f.read().splitlines()
            assert len(content) == 3
            assert content[0] == "Line 1: First line"
            assert content[1] == "INSERTED LINE"
            assert content[2] == "Line 2: Second line"
    
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
        except:
            pass

@pytest.mark.asyncio
async def test_file_error_handling():
    """Test error handling for file operations."""
    # Test with non-existent file
    output = []
    async for chunk in dc_execute_file_tool_streaming(
        {"command": "view", "path": "/non/existent/file.txt"}
    ):
        output.append(chunk)
    
    combined_output = "".join(output)
    assert "Error: File not found" in combined_output
    
    # Test with invalid operation
    output = []
    async for chunk in dc_execute_file_tool_streaming(
        {"command": "invalid_op", "path": "/tmp/test.txt"}
    ):
        output.append(chunk)
    
    combined_output = "".join(output)
    assert "Error: Invalid command" in combined_output

if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))