#!/usr/bin/env python3
"""
Test script for the ToolCallBuffer class.

This script tests the buffer pattern implementation that handles partial function calls 
during streaming, ensuring they are only processed when complete.
"""

import unittest
import json
from typing import Dict, List, Any

# Import the class to test
from streaming.buffer_pattern import ToolCallBuffer

class TestToolCallBuffer(unittest.TestCase):
    """Tests for the ToolCallBuffer class."""

    def setUp(self):
        """Set up a fresh buffer for each test."""
        self.buffer = ToolCallBuffer()

    def test_xml_function_call_across_multiple_events(self):
        """Test processing partial XML function calls across multiple events."""
        # Simulate streaming XML in chunks
        chunks = [
            "<function_calls>",
            "<invoke name=\"dc_bash\">",
            "<parameter name=\"command\">ls -la</parameter>",
            "</invoke>",
            "</function_calls>"
        ]
        
        index = 0
        # Process all but the last chunk
        for i in range(len(chunks) - 1):
            result = self.buffer.process_content_block_delta(index, chunks[i], "test-id-1")
            self.assertEqual(result["type"], "partial_xml")
            self.assertEqual(result["index"], index)
            self.assertIn(chunks[i], result["buffer"])
            
        # Process the last chunk and the content_block_stop
        self.buffer.process_content_block_delta(index, chunks[-1], "test-id-1")
        result = self.buffer.process_content_block_stop(index)
        
        # Verify the result
        self.assertEqual(result["type"], "complete_xml")
        self.assertEqual(result["tool_name"], "dc_bash")
        self.assertEqual(result["tool_params"]["command"], "ls -la")
        self.assertEqual(result["tool_use_id"], "test-id-1")

    def test_json_function_call_across_multiple_events(self):
        """Test processing partial JSON function calls across multiple events."""
        # Simulate streaming JSON in chunks
        chunks = [
            '{"tool": "dc_bash", ',
            '"parameters": {',
            '"command": "pwd"',
            '}}',
        ]
        
        index = 1
        # Process all but the last chunk
        for i in range(len(chunks) - 1):
            result = self.buffer.process_content_block_delta(index, chunks[i], "test-id-2")
            self.assertIn("partial", result["type"])
            self.assertEqual(result["index"], index)
            
        # Process the last chunk and the content_block_stop
        self.buffer.process_content_block_delta(index, chunks[-1], "test-id-2")
        result = self.buffer.process_content_block_stop(index)
        
        # Verify the result
        self.assertEqual(result["type"], "complete_json")
        self.assertEqual(result["tool_name"], "dc_bash")
        self.assertEqual(result["tool_params"]["command"], "pwd")
        self.assertEqual(result["tool_use_id"], "test-id-2")

    def test_malformed_xml(self):
        """Test handling malformed XML."""
        # Simulate malformed XML
        xml = """<function_calls>
                <invoke name="dc_bash">
                <parameter name="command">ls -la
                </invoke>
                </function_calls>"""
        
        index = 2
        self.buffer.process_content_block_delta(index, xml, "test-id-3")
        result = self.buffer.process_content_block_stop(index)
        
        # Verify the result
        self.assertEqual(result["type"], "tool_call_error")
        self.assertIn("error", result)
        # Tags are not properly closed
        self.assertEqual(result["format"], "xml_malformed") 

    def test_malformed_json(self):
        """Test handling malformed JSON."""
        # Simulate malformed JSON
        json_str = '{"tool": "dc_bash", "parameters": {"command": "pwd" '  # Missing closing braces
        
        index = 3
        self.buffer.process_content_block_delta(index, json_str, "test-id-4")
        result = self.buffer.process_content_block_stop(index)
        
        # Verify the result
        self.assertEqual(result["type"], "complete_text")  # Falls back to text since it's not valid JSON
        self.assertEqual(result["content"], json_str)
        self.assertEqual(result["tool_id"], "test-id-4")

    def test_validate_tool_parameters(self):
        """Test parameter validation for different tools."""
        # Test valid dc_bash parameters
        valid, msg, params = self.buffer.validate_tool_parameters("dc_bash", {"command": "ls"})
        self.assertTrue(valid)
        self.assertEqual(params["command"], "ls")
        
        # Test invalid dc_bash parameters (missing command)
        valid, msg, params = self.buffer.validate_tool_parameters("dc_bash", {})
        self.assertFalse(valid)
        self.assertIn("Missing required 'command'", msg)
        
        # Test parameter recovery for dc_bash
        valid, msg, params = self.buffer.validate_tool_parameters("dc_bash", {"cmd": "pwd"})
        self.assertTrue(valid)
        self.assertEqual(params["command"], "pwd")
        
        # Test dc_computer validation
        valid, msg, params = self.buffer.validate_tool_parameters("dc_computer", {"action": "click"})
        self.assertTrue(valid)
        
        # Test invalid dc_computer parameters
        valid, msg, params = self.buffer.validate_tool_parameters("dc_computer", {})
        self.assertFalse(valid)
        self.assertIn("Missing required 'action'", msg)
        
        # Test dc_str_replace_editor validation
        valid, msg, params = self.buffer.validate_tool_parameters(
            "dc_str_replace_editor", 
            {"command": "write", "path": "/tmp/test.txt"}
        )
        self.assertTrue(valid)
        
        # Test invalid dc_str_replace_editor parameters
        valid, msg, params = self.buffer.validate_tool_parameters(
            "dc_str_replace_editor", 
            {"command": "write"}  # Missing path
        )
        self.assertFalse(valid)
        self.assertIn("Missing required 'path'", msg)

    def test_break_execution(self):
        """Test the execution break functionality to prevent infinite loops."""
        # Create a test case that executes multiple tool calls
        for i in range(3):
            index = i
            self.buffer.process_content_block_delta(index, f'<function_calls><invoke name="dc_bash"><parameter name="command">ls -{i}</parameter></invoke></function_calls>', f"test-id-{i}")
            result = self.buffer.process_content_block_stop(index)
            self.assertEqual(result["type"], "complete_xml")
            
        # After 3 attempts, should_break_execution should return True
        self.assertTrue(self.buffer.should_break_execution())
        
        # Reset attempts and check that it's reset properly
        self.buffer.reset_attempts()
        self.assertFalse(self.buffer.should_break_execution())

    def test_xml_with_multiple_parameters(self):
        """Test XML function calls with multiple parameters."""
        xml = """<function_calls>
                <invoke name="dc_str_replace_editor">
                <parameter name="command">write</parameter>
                <parameter name="path">/tmp/test.txt</parameter>
                <parameter name="content">Hello, world!</parameter>
                </invoke>
                </function_calls>"""
                
        index = 10
        self.buffer.process_content_block_delta(index, xml, "test-id-10")
        result = self.buffer.process_content_block_stop(index)
        
        # Verify the result
        self.assertEqual(result["type"], "complete_xml")
        self.assertEqual(result["tool_name"], "dc_str_replace_editor")
        self.assertEqual(result["tool_params"]["command"], "write")
        self.assertEqual(result["tool_params"]["path"], "/tmp/test.txt")
        self.assertEqual(result["tool_params"]["content"], "Hello, world!")

if __name__ == "__main__":
    unittest.main()