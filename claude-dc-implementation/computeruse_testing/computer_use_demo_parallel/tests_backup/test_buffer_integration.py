"""
Test script for verifying the buffer pattern integration in unified_streaming_loop.py.

This script simulates events that would occur during streaming to test
the buffer pattern implementation.
"""

import unittest
import asyncio
import json
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock, patch

from streaming.buffer_pattern import ToolCallBuffer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_buffer")

class TestBufferIntegration(unittest.TestCase):
    """Test the buffer pattern integration."""
    
    def setUp(self):
        """Set up each test."""
        self.buffer = ToolCallBuffer()
    
    def create_mock_delta(self, partial_json=None, type="input_json_delta", tool_use_id=None):
        """Create a mock delta event."""
        delta = MagicMock()
        delta.type = type
        delta.partial_json = partial_json
        delta.tool_use_id = tool_use_id
        return delta
    
    def test_buffer_initialization(self):
        """Test that the buffer initializes correctly."""
        self.assertEqual({}, self.buffer.json_buffers)
        self.assertEqual({}, self.buffer.tool_use_ids)
        self.assertEqual(0, self.buffer.attempt_count)
    
    def test_process_content_block_delta(self):
        """Test processing a content block delta event."""
        delta = self.create_mock_delta(partial_json='{"command":')
        
        # Process the delta
        result = self.buffer.process_content_block_delta(0, delta)
        
        # Check the result
        self.assertEqual("partial_tool_call", result["type"])
        self.assertEqual(False, result["is_complete"])
        self.assertEqual('{"command":', result["buffer"])
    
    def test_process_content_block_delta_with_tool_id(self):
        """Test processing with tool_use_id."""
        delta = self.create_mock_delta(partial_json='{"command":', tool_use_id="test_tool_id")
        
        # Process the delta
        result = self.buffer.process_content_block_delta(0, delta)
        
        # Check that tool_use_id is tracked
        self.assertEqual("test_tool_id", result["tool_use_id"])
    
    def test_process_content_block_stop_complete_json(self):
        """Test processing a stop event with complete JSON."""
        # Setup buffer with content
        delta = self.create_mock_delta(partial_json='{"command": "ls -la"}')
        self.buffer.process_content_block_delta(0, delta)
        
        # Process stop event
        result = self.buffer.process_content_block_stop(0)
        
        # Check the result
        self.assertEqual("complete_tool_call", result["type"])
        self.assertEqual(True, result["is_complete"])
        self.assertEqual("dc_bash", result["tool_name"])
        self.assertEqual({"command": "ls -la"}, result["tool_params"])
    
    def test_process_content_block_stop_invalid_json(self):
        """Test processing a stop event with invalid JSON."""
        # Setup buffer with invalid content
        delta = self.create_mock_delta(partial_json='{"command": "ls -la"')
        self.buffer.process_content_block_delta(0, delta)
        
        # Process stop event
        result = self.buffer.process_content_block_stop(0)
        
        # Check the result
        self.assertEqual("tool_call_error", result["type"])
        self.assertEqual(False, result["is_complete"])
        self.assertIn("Invalid JSON", result["error"])
    
    def test_validate_tool_parameters_missing_command(self):
        """Test parameter validation with missing command."""
        # Test with missing command
        params = {}
        is_valid, message, fixed_params = self.buffer.validate_tool_parameters("dc_bash", params)
        
        # Check results
        self.assertEqual(False, is_valid)
        self.assertIn("Missing required 'command' parameter", message)
    
    def test_validate_tool_parameters_recover_command(self):
        """Test parameter recovery with alternative fields."""
        # Test with alternative field
        params = {"bash": "ls -la"}
        is_valid, message, fixed_params = self.buffer.validate_tool_parameters("dc_bash", params)
        
        # Check that command was recovered
        self.assertEqual(True, is_valid)
        self.assertEqual("ls -la", fixed_params["command"])
    
    def test_should_break_execution(self):
        """Test the execution break condition."""
        # Initially should not break
        self.assertEqual(False, self.buffer.should_break_execution())
        
        # After max attempts, should break
        self.buffer.attempt_count = self.buffer.max_attempts
        self.assertEqual(True, self.buffer.should_break_execution())
    
    def test_reset_attempts(self):
        """Test resetting attempt counter."""
        self.buffer.attempt_count = 2
        self.buffer.reset_attempts()
        self.assertEqual(0, self.buffer.attempt_count)
    
    def test_xml_function_call(self):
        """Test processing an XML function call."""
        # Setup buffer with XML content
        xml_content = """<function_calls>
            <invoke name="dc_bash">
                <parameter name="command">ls -la</parameter>
            </invoke>
        </function_calls>"""
        
        delta = self.create_mock_delta(partial_json=xml_content)
        self.buffer.process_content_block_delta(0, delta)
        
        # Process stop event
        result = self.buffer.process_content_block_stop(0)
        
        # Check the result
        self.assertEqual("complete_tool_call", result["type"])
        self.assertEqual("dc_bash", result["tool_name"])
        self.assertEqual({"command": "ls -la"}, result["tool_params"])

if __name__ == "__main__":
    unittest.main()