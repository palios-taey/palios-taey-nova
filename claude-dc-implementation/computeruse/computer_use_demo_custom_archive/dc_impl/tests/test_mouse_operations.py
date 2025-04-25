#!/usr/bin/env python3
"""
Unit tests for the mouse operations adapter.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the adapter
from tools.dc_adapters import (
    dc_execute_computer_tool,
    dc_validate_coordinates,
    dc_check_rate_limit,
    dc_check_click_interval
)
from models.dc_models import DCToolResult


class TestMouseOperationsAdapter(unittest.TestCase):
    """Test the mouse operations adapter functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_coordinate_validation(self):
        """Test coordinate validation."""
        # Valid coordinates
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates([100, 200])
        )
        self.assertTrue(is_valid)
        self.assertEqual(validated, [100, 200])
        
        # Invalid coordinates - not a list
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates("not a list")
        )
        self.assertFalse(is_valid)
        
        # Invalid coordinates - wrong length
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates([100, 200, 300])
        )
        self.assertFalse(is_valid)
        
        # Invalid coordinates - negative values
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates([-10, 200])
        )
        self.assertFalse(is_valid)
        
        # Invalid coordinates - out of bounds
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates([2000, 200])
        )
        self.assertFalse(is_valid)
        
        # Invalid coordinates - not integers
        is_valid, message, validated = self.loop.run_until_complete(
            dc_validate_coordinates(["a", "b"])
        )
        self.assertFalse(is_valid)

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Rate limiting should allow initial operations
        is_allowed = self.loop.run_until_complete(dc_check_rate_limit())
        self.assertTrue(is_allowed)
        
        # Click interval should initially be allowed
        is_allowed = self.loop.run_until_complete(dc_check_click_interval())
        self.assertTrue(is_allowed)
        
        # Rapid successive calls to click interval might be limited
        # This is time-based, so we'll just test that the function runs without error
        is_allowed = self.loop.run_until_complete(dc_check_click_interval())
        self.assertIsInstance(is_allowed, bool)

    def test_mouse_move_parameters(self):
        """Test parameter validation for mouse move action."""
        # Missing coordinates
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "mouse_move"})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("coordinates", result.error.lower())
        
        # Invalid coordinates format
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "mouse_move", "coordinates": "invalid"})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("invalid", result.error.lower())
        
        # Valid parameters (will use mock implementation in test)
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "mouse_move", "coordinates": [100, 200]})
        )
        self.assertIsNone(result.error)
        self.assertIn("mouse moved", result.output.lower())

    def test_mouse_click_parameters(self):
        """Test parameter validation for mouse click actions."""
        # Basic left click (no coordinates specified)
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "left_click"})
        )
        self.assertIsNone(result.error)
        self.assertIn("left_click", result.output.lower())
        
        # Click with coordinates
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "left_click", "coordinates": [100, 200]})
        )
        self.assertIsNone(result.error)
        self.assertIn("left_click", result.output.lower())
        self.assertIn("100, 200", result.output)
        
        # Click with invalid coordinates
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "left_click", "coordinates": [-100, 200]})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("coordinates", result.error.lower())
        
        # Other click types
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "right_click"})
        )
        self.assertIsNone(result.error)
        self.assertIn("right_click", result.output.lower())
        
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "double_click"})
        )
        self.assertIsNone(result.error)
        self.assertIn("double_click", result.output.lower())

    def test_mouse_drag_parameters(self):
        """Test parameter validation for mouse drag action."""
        # Missing start coordinates
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "left_click_drag", "coordinate": [200, 300]})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("start", result.error.lower())
        
        # Missing end coordinates
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "left_click_drag", "start_coordinate": [100, 200]})
        )
        self.assertIsNotNone(result.error)
        self.assertIn("coordinate", result.error.lower())
        
        # Valid parameters (will use mock implementation in test)
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({
                "action": "left_click_drag", 
                "start_coordinate": [100, 200],
                "coordinate": [200, 300]
            })
        )
        self.assertIsNone(result.error)
        self.assertIn("drag", result.output.lower())
        self.assertIn("100, 200", result.output)
        self.assertIn("200, 300", result.output)


if __name__ == "__main__":
    unittest.main()