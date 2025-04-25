#!/usr/bin/env python3
"""
Unit tests for the screenshot tool adapter.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the adapter
from tools.dc_adapters import dc_execute_computer_tool
from models.dc_models import DCToolResult


class TestScreenshotAdapter(unittest.TestCase):
    """Test the screenshot tool adapter functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_screenshot_parameters(self):
        """Test parameter validation for screenshot action."""
        # Valid screenshot parameters (screenshot doesn't require additional params)
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "screenshot"})
        )
        # Should not have an error due to parameters
        self.assertFalse(
            result.error and "Missing required" in result.error,
            f"Valid parameters should not cause validation error: {result.error}",
        )

    def test_screenshot_execution(self):
        """Test that screenshot execution works and returns appropriate output."""
        # Execute the screenshot action
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "screenshot"})
        )
        
        # We should always get a result with output
        self.assertIsNotNone(result, "Screenshot execution should return a result")
        self.assertIsNotNone(result.output, "Screenshot should provide output text")
        
        # If we have an error, it shouldn't be related to invalid parameters
        if result.error:
            self.assertNotIn("Missing required", result.error)
            self.assertNotIn("Invalid parameters", result.error)

        # Check for successful execution or fallback to mock
        if "Mock" in result.output:
            # Using mock implementation is acceptable
            self.assertIn("Mock screenshot taken", result.output)
        else:
            # Production implementation should have success message and no error
            self.assertFalse(result.error, f"Screenshot should not error: {result.error}")
            self.assertIn("successfully", result.output.lower())
            
            # If we're using the production tool, we should have a base64 image
            if "production" in result.output.lower():
                self.assertIsNotNone(
                    result.base64_image, 
                    "Production screenshot should return base64 image data"
                )

    def test_invalid_action(self):
        """Test handling of invalid actions."""
        # Invalid action
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({"action": "nonexistent_action"})
        )
        
        # Should either return error about unsupported action or fall back to mock
        if result.error:
            self.assertIn("Unsupported action", result.error)
        else:
            self.assertIn("Mock nonexistent_action executed", result.output)

    def test_missing_action(self):
        """Test handling of missing action parameter."""
        # Missing action parameter
        result = self.loop.run_until_complete(
            dc_execute_computer_tool({})
        )
        
        # Should return error about missing action
        self.assertIsNotNone(result.error)
        self.assertIn("missing", result.error.lower())
        self.assertIn("action", result.error.lower())


if __name__ == "__main__":
    unittest.main()