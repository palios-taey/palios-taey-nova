#!/usr/bin/env python3
"""
Tests for the agent_loop module
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import from agent_loop
from agent_loop import (
    agent_loop,
    execute_tool,
    validate_tool_parameters,
    ToolResult,
    COMPUTER_USE_TOOL,
    BASH_TOOL
)

class TestToolValidation(unittest.TestCase):
    """Test tool parameter validation"""
    
    def test_validate_computer_tool_missing_action(self):
        """Test validation fails with missing action parameter"""
        valid, _ = validate_tool_parameters("computer_20250124", {})
        self.assertFalse(valid)
    
    def test_validate_computer_tool_missing_coordinates(self):
        """Test validation fails with missing coordinates for mouse actions"""
        valid, _ = validate_tool_parameters("computer_20250124", {"action": "move_mouse"})
        self.assertFalse(valid)
    
    def test_validate_computer_tool_valid(self):
        """Test validation succeeds with valid parameters"""
        valid, _ = validate_tool_parameters(
            "computer_20250124", 
            {"action": "move_mouse", "coordinates": [100, 200]}
        )
        self.assertTrue(valid)
    
    def test_validate_bash_tool_missing_command(self):
        """Test validation fails with missing command parameter"""
        valid, _ = validate_tool_parameters("bash", {})
        self.assertFalse(valid)
    
    def test_validate_bash_tool_valid(self):
        """Test validation succeeds with valid parameters"""
        valid, _ = validate_tool_parameters("bash", {"command": "ls"})
        self.assertTrue(valid)

class TestToolExecution(unittest.TestCase):
    """Test tool execution"""
    
    async def test_execute_computer_tool(self):
        """Test execution of computer use tool"""
        result = await execute_tool(
            "computer_20250124", 
            {"action": "screenshot"}
        )
        self.assertIsInstance(result, ToolResult)
        self.assertIsNotNone(result.output)
    
    async def test_execute_bash_tool(self):
        """Test execution of bash tool"""
        result = await execute_tool(
            "bash", 
            {"command": "echo 'test'"}
        )
        self.assertIsInstance(result, ToolResult)
        self.assertIsNotNone(result.output)
    
    async def test_execute_unknown_tool(self):
        """Test execution of unknown tool returns error"""
        result = await execute_tool(
            "unknown_tool", 
            {"param": "value"}
        )
        self.assertIsInstance(result, ToolResult)
        self.assertIsNotNone(result.error)

class TestAgentLoop(unittest.TestCase):
    """Test the main agent loop functionality"""
    
    @patch('agent_loop.stream_to_claude')
    async def test_agent_loop_text_response(self, mock_stream):
        """Test agent loop with text response"""
        # Set up mock response
        mock_chunk = MagicMock()
        mock_chunk.type = "content_block_delta"
        mock_chunk.delta.text = "Hello world"
        
        mock_stop = MagicMock()
        mock_stop.type = "message_stop"
        
        mock_stream.return_value = [mock_chunk, mock_stop]
        
        # Test callbacks
        callback_output = []
        callbacks = {
            "on_text": lambda text: callback_output.append(text)
        }
        
        # Run agent loop
        result = await agent_loop(
            "Hello", 
            conversation_history=[],
            callbacks=callbacks
        )
        
        # Verify results
        self.assertEqual(callback_output, ["Hello world"])
        self.assertEqual(len(result), 2)  # User message + assistant response
        
    @patch('agent_loop.stream_to_claude')
    @patch('agent_loop.execute_tool')
    async def test_agent_loop_tool_use(self, mock_execute_tool, mock_stream):
        """Test agent loop with tool use"""
        # Set up mock response for tool use
        mock_start = MagicMock()
        mock_start.type = "content_block_start"
        mock_start.content_block.type = "tool_use"
        mock_start.content_block.name = "computer_20250124"
        mock_start.content_block.input = {"action": "screenshot"}
        mock_start.content_block.id = "tool_1"
        
        mock_stop = MagicMock()
        mock_stop.type = "message_stop"
        
        # Set up tool execution mock
        mock_execute_tool.return_value = ToolResult(output="Screenshot captured")
        
        # Mock streams for initial and continuation response
        mock_stream.side_effect = [
            [mock_start, mock_stop],  # Initial response with tool use
            [mock_stop]  # Continuation response (empty)
        ]
        
        # Test callbacks
        tool_use_calls = []
        tool_result_calls = []
        callbacks = {
            "on_tool_use": lambda name, input_data: tool_use_calls.append((name, input_data)),
            "on_tool_result": lambda name, input_data, result: tool_result_calls.append((name, result.output))
        }
        
        # Run agent loop
        result = await agent_loop(
            "Take a screenshot", 
            conversation_history=[],
            callbacks=callbacks
        )
        
        # Verify results
        self.assertEqual(len(tool_use_calls), 1)
        self.assertEqual(tool_use_calls[0][0], "computer_20250124")
        
        self.assertEqual(len(tool_result_calls), 1)
        self.assertEqual(tool_result_calls[0][1], "Screenshot captured")
        
        self.assertTrue(mock_execute_tool.called)
        self.assertEqual(mock_execute_tool.call_count, 1)

def run_async_test(test_case):
    """Run an async test function"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case())

if __name__ == "__main__":
    unittest.main()