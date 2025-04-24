"""
Test suite for streaming bash tool implementation.

This file contains tests for the bash_streaming.py module, ensuring proper
streaming functionality, error handling, and command validation.
"""

import os
import asyncio
import unittest
import logging
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the streaming bash implementation
from bash_streaming import (
    dc_execute_bash_tool_streaming,
    dc_execute_bash_tool,
    validate_read_only_command,
    DCToolResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_bash_streaming")

class TestBashStreaming(unittest.TestCase):
    """Test cases for streaming bash tool implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directory
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test file
        self.test_file = self.test_dir / "test_file.txt"
        with open(self.test_file, "w") as f:
            f.write("This is a test file.\nLine 2\nLine 3\nLine 4\nLine 5\n")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test file if it exists
        if self.test_file.exists():
            self.test_file.unlink()
    
    def test_validate_read_only_command(self):
        """Test command validation."""
        valid_commands = [
            "ls -la",
            "cat /etc/hostname",
            "grep -r 'test' /home/computeruse",
            "echo 'Hello world'",
            "find /home -name '*.py'",
        ]
        
        invalid_commands = [
            "rm -rf /",
            "sudo apt update",
            "cat /etc/shadow",
            "ls | rm",
            "curl -o output.txt https://example.com",
        ]
        
        # Run valid commands through the validator
        for cmd in valid_commands:
            is_valid, message = asyncio.run(validate_read_only_command(cmd))
            self.assertTrue(is_valid, f"Command should be valid: {cmd}, error: {message}")
        
        # Run invalid commands through the validator
        for cmd in invalid_commands:
            is_valid, message = asyncio.run(validate_read_only_command(cmd))
            self.assertFalse(is_valid, f"Command should be invalid: {cmd}")
    
    async def collect_streaming_output(self, command: str) -> List[str]:
        """Collect output from streaming command execution."""
        chunks = []
        async for chunk in dc_execute_bash_tool_streaming({"command": command}):
            chunks.append(chunk)
        return chunks
    
    def test_command_execution(self):
        """Test basic command execution."""
        # Test echo command
        result = asyncio.run(dc_execute_bash_tool({"command": "echo 'test message'"}))
        self.assertIsNotNone(result.output)
        self.assertIn("test message", result.output)
        self.assertIsNone(result.error)
        
        # Test ls command
        result = asyncio.run(dc_execute_bash_tool({"command": f"ls {self.test_dir}"}))
        self.assertIsNotNone(result.output)
        self.assertIn("test_file.txt", result.output)
        self.assertIsNone(result.error)
    
    def test_streaming_output(self):
        """Test streaming output functionality."""
        # Test echo command with streaming
        chunks = asyncio.run(self.collect_streaming_output("echo 'streaming test'"))
        self.assertTrue(chunks)
        self.assertEqual("streaming test\n", "".join(chunks))
        
        # Test cat command with streaming
        chunks = asyncio.run(self.collect_streaming_output(f"cat {self.test_file}"))
        self.assertTrue(chunks)
        combined = "".join(chunks)
        self.assertIn("This is a test file", combined)
        self.assertIn("Line 5", combined)
    
    def test_error_handling(self):
        """Test error handling in streaming mode."""
        # Test invalid command
        result = asyncio.run(dc_execute_bash_tool({"command": "invalid_command_123"}))
        self.assertIsNotNone(result.error)
        self.assertIn("Error", result.error)
        
        # Test validation failure
        result = asyncio.run(dc_execute_bash_tool({"command": "rm -rf /tmp/test"}))
        self.assertIsNotNone(result.error)
        self.assertIn("not in the whitelist", result.error)
        
        # Test empty command
        result = asyncio.run(dc_execute_bash_tool({"command": ""}))
        self.assertIsNotNone(result.error)
        self.assertIn("Empty command", result.error)
    
    def test_progress_reporting(self):
        """Test progress reporting in streaming mode."""
        progress_updates = []
        
        async def progress_callback(message, progress):
            progress_updates.append((message, progress))
        
        # Run a command with progress reporting
        async def run_with_progress():
            async for _ in dc_execute_bash_tool_streaming(
                {"command": f"cat {self.test_file}"},
                progress_callback=progress_callback
            ):
                pass
        
        asyncio.run(run_with_progress())
        
        # Verify progress was reported
        self.assertTrue(progress_updates)
        # Should have at least start and end progress
        self.assertGreaterEqual(len(progress_updates), 2)
        # First progress should be near 0
        self.assertLess(progress_updates[0][1], 0.1)
        # Last progress should be 1.0 (complete)
        self.assertEqual(progress_updates[-1][1], 1.0)

# For directly running the tests
if __name__ == "__main__":
    unittest.main()