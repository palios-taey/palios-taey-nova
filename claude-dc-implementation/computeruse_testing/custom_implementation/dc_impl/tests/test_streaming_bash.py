"""
Test module for streaming bash tool implementation.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the streaming bash tool
from tools.dc_bash import (
    dc_execute_bash_tool_streaming,
    dc_process_streaming_output,
    dc_validate_bash_command,
    dc_validate_bash_parameters
)

from models.dc_models import DCToolResult

@pytest.mark.asyncio
async def test_bash_validation_valid_command():
    """Test validation of valid read-only commands."""
    valid_commands = [
        "ls -la",
        "echo hello world",
        "cat /etc/hostname",
        "grep 'test' file.txt",
        "ps aux",
        "curl -s https://example.com"
    ]
    
    for command in valid_commands:
        is_valid, message = await dc_validate_bash_command(command)
        assert is_valid, f"Command should be valid: {command}, error: {message}"

@pytest.mark.asyncio
async def test_bash_validation_invalid_command():
    """Test validation of invalid or dangerous commands."""
    invalid_commands = [
        "rm -rf /",
        "echo 'test' > file.txt",
        "sudo apt-get install package",
        "cat /etc/passwd",
        "wget -O /tmp/file http://example.com",
        "ls; rm file.txt"
    ]
    
    for command in invalid_commands:
        is_valid, message = await dc_validate_bash_command(command)
        assert not is_valid, f"Command should be invalid: {command}"

@pytest.mark.asyncio
async def test_bash_parameter_validation():
    """Test validation of tool input parameters."""
    # Valid parameters
    valid_params = [
        {"command": "ls -la"},
        {"command": "echo hello", "mode": "read_only"},
        {"command": "ps aux", "mode": "standard"}
    ]
    
    for params in valid_params:
        is_valid, message = dc_validate_bash_parameters(params)
        assert is_valid, f"Parameters should be valid: {params}, error: {message}"
    
    # Invalid parameters
    invalid_params = [
        {},  # Missing command
        {"command": ""},  # Empty command
        {"command": "ls", "mode": "invalid"},  # Invalid mode
        {"foo": "bar"}  # Missing required parameter
    ]
    
    for params in invalid_params:
        is_valid, message = dc_validate_bash_parameters(params)
        assert not is_valid, f"Parameters should be invalid: {params}"

@pytest.mark.asyncio
async def test_streaming_output_collection():
    """Test collection of streaming output."""
    async def dummy_stream():
        yield "Line 1\n"
        yield "Line 2\n"
        yield "Line 3\n"
    
    result = await dc_process_streaming_output(dummy_stream())
    assert isinstance(result, DCToolResult)
    assert result.output == "Line 1\nLine 2\nLine 3\n"
    assert result.error is None

@pytest.mark.asyncio
async def test_streaming_error_collection():
    """Test collection of streaming errors."""
    async def dummy_error_stream():
        yield "Error: Something went wrong\n"
        yield "More error details\n"
    
    result = await dc_process_streaming_output(dummy_error_stream())
    assert isinstance(result, DCToolResult)
    assert result.error == "Error: Something went wrong\nMore error details\n"
    assert result.output is None

@pytest.mark.asyncio
async def test_bash_streaming_echo():
    """Test streaming output of echo command."""
    # We'll use echo as it's safe and predictable
    command = "echo 'Hello, streaming bash!'"
    
    # Progress tracking
    progress_updates = []
    
    async def track_progress(message, progress):
        progress_updates.append((message, progress))
    
    # Collect output
    output = []
    async for chunk in dc_execute_bash_tool_streaming(
        {"command": command},
        progress_callback=track_progress
    ):
        output.append(chunk)
    
    # Check output
    assert "".join(output).strip() == "Hello, streaming bash!"
    
    # Check that progress was reported
    assert len(progress_updates) > 0
    # First update should be "Starting command"
    assert progress_updates[0][0].startswith("Starting command")
    assert progress_updates[0][1] == 0.0
    # Last update should be "Completed"
    assert progress_updates[-1][0].startswith("Completed")
    assert progress_updates[-1][1] == 1.0

@pytest.mark.asyncio
async def test_bash_streaming_invalid_command():
    """Test streaming output with invalid command."""
    # Use an invalid command
    command = "invalid_command_that_does_not_exist"
    
    # Collect output
    output = []
    async for chunk in dc_execute_bash_tool_streaming({"command": command}):
        output.append(chunk)
    
    # Output should contain error message
    assert any("command not found" in chunk or "Error" in chunk for chunk in output)

if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))