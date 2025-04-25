#!/usr/bin/env python3
"""
Integration tests that combine multiple tool operations.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the adapters
from tools.dc_adapters import dc_execute_computer_tool, dc_execute_bash_tool
from models.dc_models import DCToolResult


class TestToolIntegration(unittest.TestCase):
    """Test integration between different tools."""

    def setUp(self):
        """Set up the test environment."""
        # Create event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    async def screenshot_move_click_workflow(self):
        """Test a workflow that combines screenshot, move, and click."""
        # Step 1: Take a screenshot
        screenshot_result = await dc_execute_computer_tool({"action": "screenshot"})
        self.assertIsNone(screenshot_result.error)
        self.assertIsNotNone(screenshot_result.output)
        
        # In a real scenario, we might analyze the screenshot to find elements
        
        # Step 2: Move mouse to specific coordinates
        move_result = await dc_execute_computer_tool({
            "action": "mouse_move", 
            "coordinates": [100, 200]
        })
        self.assertIsNone(move_result.error)
        self.assertIn("mouse moved", move_result.output.lower())
        
        # Step 3: Perform a click
        click_result = await dc_execute_computer_tool({"action": "left_click"})
        self.assertIsNone(click_result.error)
        self.assertIn("left_click", click_result.output.lower())
        
        # In a real scenario, we would take another screenshot to verify the result
        return True

    async def bash_screenshot_workflow(self):
        """Test a workflow that combines bash commands and screenshots."""
        # Step 1: Run a bash command to list files
        bash_result = await dc_execute_bash_tool({"command": "ls -la"})
        self.assertIsNone(bash_result.error)
        self.assertIsNotNone(bash_result.output)
        
        # Step 2: Take a screenshot
        screenshot_result = await dc_execute_computer_tool({"action": "screenshot"})
        self.assertIsNone(screenshot_result.error)
        self.assertIsNotNone(screenshot_result.output)
        
        # In a real scenario, we might do something with the command output
        return True

    async def drag_click_bash_workflow(self):
        """Test a workflow that combines drag, click, and bash commands."""
        # Step 1: Perform a drag operation
        drag_result = await dc_execute_computer_tool({
            "action": "left_click_drag", 
            "start_coordinate": [100, 200],
            "coordinate": [300, 400]
        })
        self.assertIsNone(drag_result.error)
        self.assertIn("drag", drag_result.output.lower())
        
        # Step 2: Perform a click
        click_result = await dc_execute_computer_tool({"action": "right_click"})
        self.assertIsNone(click_result.error)
        self.assertIn("right_click", click_result.output.lower())
        
        # Step 3: Run a bash command
        bash_result = await dc_execute_bash_tool({"command": "echo 'Integration test successful'"})
        self.assertIsNone(bash_result.error)
        self.assertIn("integration test successful", bash_result.output.lower())
        
        return True

    def test_screenshot_move_click_workflow(self):
        """Run the screenshot-move-click workflow test."""
        result = self.loop.run_until_complete(self.screenshot_move_click_workflow())
        self.assertTrue(result)

    def test_bash_screenshot_workflow(self):
        """Run the bash-screenshot workflow test."""
        result = self.loop.run_until_complete(self.bash_screenshot_workflow())
        self.assertTrue(result)

    def test_drag_click_bash_workflow(self):
        """Run the drag-click-bash workflow test."""
        result = self.loop.run_until_complete(self.drag_click_bash_workflow())
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()