"""
Integration tests for streaming implementation.

This module provides tests that verify the integration between the streaming
tools and the streaming agent loop.
"""

import os
import asyncio
import unittest
import logging
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the streaming components
from bash_streaming import dc_execute_bash_tool_streaming
from streaming_adapters import StreamingToolAdapter, execute_streaming_bash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_integration")

class MockStreamingSession:
    """
    Mock streaming session for testing integration with tools.
    
    This simulates the key functionality of the streaming agent loop
    without requiring an actual API connection.
    """
    
    def __init__(self):
        self.messages = []
        self.tool_results = []
        self.active_tool = None
    
    async def add_tool_result(self, tool_name, tool_id, result_content):
        """Add a tool result to the session."""
        self.tool_results.append({
            "tool_name": tool_name,
            "tool_id": tool_id,
            "content": result_content
        })
    
    async def on_progress(self, message, progress):
        """Handle progress updates."""
        self.messages.append(f"Progress: {message} - {progress:.0%}")

class TestStreamingIntegration(unittest.TestCase):
    """Test cases for streaming component integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directory
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test file
        self.test_file = self.test_dir / "integration_test.txt"
        with open(self.test_file, "w") as f:
            f.write("Integration test file.\nLine 2\nLine 3\n")
        
        # Create a streaming adapter
        self.adapter = StreamingToolAdapter()
        
        # Create a mock session
        self.session = MockStreamingSession()
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test file if it exists
        if self.test_file.exists():
            self.test_file.unlink()
    
    async def execute_tool_and_collect(self, tool_name, tool_input):
        """Execute a tool and collect all output chunks."""
        chunks = []
        tool_id = f"test_tool_{len(chunks)}"
        
        async for chunk in self.adapter.execute_tool_streaming(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_id=tool_id,
            on_progress=self.session.on_progress
        ):
            chunks.append(chunk)
            
        return chunks, tool_id
    
    def test_bash_integration(self):
        """Test bash integration with streaming system."""
        # Test basic bash command
        chunks, tool_id = asyncio.run(self.execute_tool_and_collect(
            tool_name="dc_bash",
            tool_input={"command": "echo 'Integration test'"}
        ))
        
        # Verify we got output
        self.assertTrue(chunks)
        self.assertIn("Integration test", "".join(chunks))
        
        # Verify progress was tracked
        self.assertTrue(self.session.messages)
        self.assertIn("Progress", self.session.messages[0])
        
        # Verify tool status is tracked
        tool_status = self.adapter.get_tool_status(tool_id)
        self.assertIsNotNone(tool_status)
        self.assertEqual(tool_status["status"], "completed")
        self.assertEqual(tool_status["progress"], 1.0)
    
    def test_multiple_tools(self):
        """Test running multiple tools in sequence."""
        # First tool: echo
        chunks1, tool_id1 = asyncio.run(self.execute_tool_and_collect(
            tool_name="dc_bash",
            tool_input={"command": "echo 'First command'"}
        ))
        
        # Second tool: ls
        chunks2, tool_id2 = asyncio.run(self.execute_tool_and_collect(
            tool_name="dc_bash",
            tool_input={"command": f"ls {self.test_dir}"}
        ))
        
        # Verify both tools executed properly
        self.assertIn("First command", "".join(chunks1))
        self.assertIn("integration_test.txt", "".join(chunks2))
        
        # Verify tool status is tracked for both
        active_tools = self.adapter.get_active_tools()
        self.assertIn(tool_id1, active_tools)
        self.assertIn(tool_id2, active_tools)
    
    def test_utility_function(self):
        """Test the utility function for executing bash commands."""
        # Use the simplified utility function
        async def collect_bash_output(command):
            chunks = []
            async for chunk in execute_streaming_bash(command, self.session.on_progress):
                chunks.append(chunk)
            return chunks
        
        # Execute a command
        chunks = asyncio.run(collect_bash_output(f"cat {self.test_file}"))
        
        # Verify output
        output = "".join(chunks)
        self.assertIn("Integration test file", output)
        self.assertIn("Line 3", output)
        
        # Verify progress was tracked
        self.assertTrue(any("Progress" in msg for msg in self.session.messages))
    
    def test_error_handling(self):
        """Test error handling in the integration flow."""
        # Execute an invalid command
        chunks, tool_id = asyncio.run(self.execute_tool_and_collect(
            tool_name="dc_bash",
            tool_input={"command": "invalid_command_that_does_not_exist"}
        ))
        
        # Verify error output was captured
        output = "".join(chunks)
        self.assertIn("Error", output)
        
        # Verify tool status reflects the error
        tool_status = self.adapter.get_tool_status(tool_id)
        self.assertEqual(tool_status["progress"], 1.0)  # Should be marked complete

# For directly running the tests
if __name__ == "__main__":
    unittest.main()