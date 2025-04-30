#!/usr/bin/env python3
"""
Unit tests for the read-only bash commands adapter.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the adapter
from tools.dc_adapters import dc_execute_bash_tool, dc_validate_read_only_command, dc_sanitize_command_output
from models.dc_models import DCToolResult


class TestReadOnlyBashAdapter(unittest.TestCase):
    """Test the read-only bash commands adapter functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_parameter_validation(self):
        """Test parameter validation for bash commands."""
        # Missing command parameter
        result = self.loop.run_until_complete(
            dc_execute_bash_tool({})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("missing", result.error.lower())
        self.assertIn("command", result.error.lower())
        
        # Empty command
        result = self.loop.run_until_complete(
            dc_execute_bash_tool({"command": ""})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("missing", result.error.lower())
        self.assertIn("command", result.error.lower())

    def test_command_validation(self):
        """Test validation of read-only commands."""
        # Valid read-only commands
        valid_commands = [
            "ls -la", 
            "cat /etc/hostname",
            "ps aux",
            "echo Hello world",
            "grep pattern file.txt",
            "find . -name '*.py'",
            "pwd"
        ]
        
        for cmd in valid_commands:
            is_valid, _ = dc_validate_read_only_command(cmd)
            self.assertTrue(is_valid, f"Command should be valid: {cmd}")
        
        # Invalid commands (write operations or not in whitelist)
        invalid_commands = [
            "rm -rf /",
            "touch newfile.txt",
            "echo 'content' > file.txt",
            "chmod +x script.sh",
            "mv source target",
            "cp source target",
            "sudo apt update",
            "wget -O file.txt http://example.com",
            "curl -o file.txt http://example.com",
            "find . -exec rm {} \\;",
            "ls | rm",
            "> file.txt",
            "bash -c 'echo secret > file'"
        ]
        
        for cmd in invalid_commands:
            is_valid, msg = dc_validate_read_only_command(cmd)
            self.assertFalse(is_valid, f"Command should be invalid: {cmd}")
            self.assertIsNotNone(msg)

    def test_command_execution(self):
        """Test that command execution works and returns appropriate output."""
        # Execute a simple echo command
        result = self.loop.run_until_complete(
            dc_execute_bash_tool({"command": "echo Hello, world!"})
        )
        
        # We should always get a result with output
        self.assertIsNotNone(result, "Command execution should return a result")
        self.assertIsNotNone(result.output, "Command should provide output text")
        
        # If we have an error, it shouldn't be related to invalid parameters
        if result.error:
            self.assertNotIn("Missing required", result.error)
            self.assertNotIn("Invalid parameters", result.error)

        # Check for successful execution or fallback to mock
        if "Mock" in result.output:
            # Using mock implementation is acceptable
            self.assertIn("Hello, world!", result.output)
        else:
            # Production implementation should have the command output and no error
            self.assertFalse(result.error, f"Command should not error: {result.error}")
            self.assertIn("Hello, world!", result.output)

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        # Invalid command (not in whitelist)
        result = self.loop.run_until_complete(
            dc_execute_bash_tool({"command": "nonexistent_command"})
        )
        
        # Should return error about invalid command
        self.assertIsNotNone(result.error)
        self.assertIn("not in the whitelist", result.error.lower())

    def test_dangerous_command(self):
        """Test handling of dangerous commands."""
        # Write operation command
        result = self.loop.run_until_complete(
            dc_execute_bash_tool({"command": "rm -rf /tmp/test"})
        )
        
        # Should return error about non-read-only operation
        self.assertIsNotNone(result.error)
        self.assertIn("validation failed", result.error.lower())

    def test_command_output_sanitization(self):
        """Test sanitization of command output."""
        # Test handling of binary data
        binary_output = b"Hello\x00World\xFF\xFE"
        sanitized = dc_sanitize_command_output(binary_output)
        
        # Should be a string with unprintable chars replaced
        self.assertIsInstance(sanitized, str)
        self.assertIn("Hello", sanitized)
        self.assertIn("World", sanitized)
        self.assertNotIn("\x00", sanitized)  # Null byte should be replaced
        
        # Test truncation of very long output
        long_output = "x" * 15000
        truncated = dc_sanitize_command_output(long_output)
        
        # Should be truncated with a message
        self.assertLess(len(truncated), 15000)
        self.assertIn("Output truncated", truncated)


if __name__ == "__main__":
    unittest.main()