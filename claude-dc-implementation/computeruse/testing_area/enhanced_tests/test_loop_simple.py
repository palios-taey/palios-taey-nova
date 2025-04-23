#!/usr/bin/env python3
"""
Simple test suite for the fixed loop implementation.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add the testing_area directory to the path
current_dir = Path(__file__).parent
testing_area = current_dir.parent
sys.path.insert(0, str(testing_area))

# Import the fixed loop
from enhanced_tests.fixed_loop import sampling_loop, APIProvider
from enhanced_tests.mock_streamlit import MockStreamlit

# Import required tools module
repo_root = Path("/home/computeruse/github/palios-taey-nova")
claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import tool classes
from computer_use_demo.tools import ToolResult

class TestFixedLoopSimple(unittest.TestCase):
    """Simple test cases for the fixed loop implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_streamlit = MockStreamlit()
        
    def test_api_response_callback_accepts_none_request(self):
        """Test that api_response_callback accepts None for request parameter."""
        # Direct test of the callback
        self.mock_streamlit.api_response_callback(None, {"test": "response"}, None)
        
        # Check that no errors were recorded
        self.assertEqual(len(self.mock_streamlit.errors), 0)
        
        # Check that the callback was called with None request
        self.assertTrue(len(self.mock_streamlit.api_responses) > 0)
        self.assertIsNone(self.mock_streamlit.api_responses[0]['request'])
        self.assertIsNone(self.mock_streamlit.api_responses[0]['error'])
    
    def test_error_handling_in_callback(self):
        """Test that api_response_callback handles errors properly."""
        # Create a test error
        test_error = Exception("Test error")
        
        # Direct test of the callback with an error
        self.mock_streamlit.api_response_callback(None, None, test_error)
        
        # Check that the error was properly recorded
        self.assertTrue(len(self.mock_streamlit.api_responses) > 0)
        self.assertIsNotNone(self.mock_streamlit.api_responses[0]['error'])
        self.assertEqual(str(self.mock_streamlit.api_responses[0]['error']), "Test error")

if __name__ == "__main__":
    unittest.main()