"""
Test script for the DC implementation.
"""

import unittest
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the system path
current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent  # dc_impl directory
sys.path.insert(0, str(parent_dir))

# Import from our namespace-isolated modules directly
from dc_setup import dc_initialize
from dc_executor import dc_execute_tool

class TestDCTools(unittest.TestCase):
    """Test case for DC tools implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test case by initializing the DC implementation."""
        dc_initialize()
    
    def test_computer_tool_screenshot(self):
        """Test the computer tool screenshot action."""
        result = asyncio.run(dc_execute_tool(
            tool_name="dc_computer",
            tool_input={"action": "screenshot"}
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output)
        self.assertIn("screenshot", result.output)
    
    def test_computer_tool_move_mouse(self):
        """Test the computer tool move_mouse action."""
        result = asyncio.run(dc_execute_tool(
            tool_name="dc_computer",
            tool_input={"action": "move_mouse", "coordinates": [100, 200]}
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output)
        self.assertIn("mouse moved", result.output)
    
    def test_computer_tool_invalid_params(self):
        """Test the computer tool with invalid parameters."""
        result = asyncio.run(dc_execute_tool(
            tool_name="dc_computer",
            tool_input={"action": "move_mouse"}  # Missing coordinates
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error)
        self.assertIn("Missing required 'coordinates'", result.error)
    
    def test_bash_tool(self):
        """Test the bash tool."""
        result = asyncio.run(dc_execute_tool(
            tool_name="dc_bash",
            tool_input={"command": "echo Hello World"}
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output)
        self.assertIn("Hello World", result.output)
    
    def test_bash_tool_invalid_params(self):
        """Test the bash tool with invalid parameters."""
        result = asyncio.run(dc_execute_tool(
            tool_name="dc_bash",
            tool_input={}  # Missing command
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error)
        self.assertIn("Missing required 'command'", result.error)
    
    def test_unknown_tool(self):
        """Test an unknown tool."""
        result = asyncio.run(dc_execute_tool(
            tool_name="unknown_tool",
            tool_input={}
        ))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error)
        self.assertIn("Unknown tool", result.error)

if __name__ == "__main__":
    unittest.main()