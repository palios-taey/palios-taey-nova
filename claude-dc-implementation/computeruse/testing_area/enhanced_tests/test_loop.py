#!/usr/bin/env python3
"""
Test suite for the fixed loop implementation.
This tests the streaming functionality with proper error handling.
"""

import os
import sys
import unittest
import asyncio
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

# Mock response for testing
class MockResponse:
    """Mock response class for testing."""
    def __init__(self, content_blocks=None):
        self.content_blocks = content_blocks or []
        
    def __iter__(self):
        """Return self as an iterator."""
        return self
        
    def __next__(self):
        """Simulate streaming events."""
        if not hasattr(self, '_event_index'):
            self._event_index = 0
        else:
            self._event_index += 1
            
        if self._event_index >= len(self._get_events()):
            raise StopIteration
            
        return self._get_events()[self._event_index]
    
    def _get_events(self):
        """Get all events for the response."""
        events = []
        
        # Add start event for a text block
        event = MagicMock()
        event.type = "content_block_start"
        event.content_block = MagicMock()
        event.content_block.type = "text"
        event.content_block.text = "Hello"
        events.append(event)
        
        # Add delta event
        event = MagicMock()
        event.type = "content_block_delta"
        event.index = 0
        event.delta = MagicMock()
        event.delta.text = ", world!"
        events.append(event)
        
        # Add message stop event
        event = MagicMock()
        event.type = "message_stop"
        events.append(event)
        
        return events

class TestFixedLoop(unittest.TestCase):
    """Test cases for the fixed loop implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_streamlit = MockStreamlit()
        
        # Set up basic test messages
        self.messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello, Claude!"
                    }
                ]
            }
        ]
    
    # Test methods will be defined below as class methods
    pass

    @patch('enhanced_tests.fixed_loop.Anthropic')
    async def test_api_response_callback_with_none_request(self, mock_anthropic):
        """Test that api_response_callback handles None request properly."""
        # Set up the mock
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MockResponse()
        mock_anthropic.return_value = mock_client
        
        # Run the sampling loop
        await sampling_loop(
            model="claude-3-sonnet-20240229",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=self.messages,
            output_callback=self.mock_streamlit.output_callback,
            tool_output_callback=self.mock_streamlit.tool_output_callback,
            api_response_callback=self.mock_streamlit.api_response_callback,
            api_key="dummy_key"
        )
        
        # Check that the callback was called with None request
        self.assertTrue(len(self.mock_streamlit.api_responses) > 0)
        self.assertIsNone(self.mock_streamlit.api_responses[0]['request'])
        self.assertIsNone(self.mock_streamlit.api_responses[0]['error'])
        
        # Check that no errors were recorded
        self.assertEqual(len(self.mock_streamlit.errors), 0)

    @patch('enhanced_tests.fixed_loop.Anthropic')
    async def test_api_error_handling(self, mock_anthropic):
        """Test that API errors are handled properly."""
        # Set up the mock to raise an error
        mock_client = MagicMock()
        from anthropic import APIError
        mock_error = APIError("Test error", request=None, body={})
        mock_client.messages.create.side_effect = mock_error
        mock_anthropic.return_value = mock_client
        
        # Run the sampling loop
        await sampling_loop(
            model="claude-3-sonnet-20240229",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=self.messages,
            output_callback=self.mock_streamlit.output_callback,
            tool_output_callback=self.mock_streamlit.tool_output_callback,
            api_response_callback=self.mock_streamlit.api_response_callback,
            api_key="dummy_key"
        )
        
        # Check that the error was passed to the callback
        self.assertTrue(len(self.mock_streamlit.api_responses) > 0)
        self.assertIsNotNone(self.mock_streamlit.api_responses[0]['error'])
        self.assertEqual(str(self.mock_streamlit.api_responses[0]['error']), "Test error")

    @patch('enhanced_tests.fixed_loop.Anthropic')
    async def test_streaming_output(self, mock_anthropic):
        """Test that streaming output is handled properly."""
        # Set up the mock
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MockResponse()
        mock_anthropic.return_value = mock_client
        
        # Run the sampling loop
        await sampling_loop(
            model="claude-3-sonnet-20240229",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=self.messages,
            output_callback=self.mock_streamlit.output_callback,
            tool_output_callback=self.mock_streamlit.tool_output_callback,
            api_response_callback=self.mock_streamlit.api_response_callback,
            api_key="dummy_key"
        )
        
        # Check that the messages were processed
        self.assertTrue(len(self.mock_streamlit.messages) > 0)
        self.assertEqual(self.mock_streamlit.messages[-1], "Hello, world!")

if __name__ == "__main__":
    unittest.main()