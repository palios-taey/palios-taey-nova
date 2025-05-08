"""
Test the buffer pattern integration in unified_streaming_loop.py.

This test verifies that the unified_streaming_loop properly uses the buffer
pattern to handle partial function calls during streaming.
"""

import os
import unittest
import asyncio
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_unified_streaming")

# Import modules to test
from streaming.unified_streaming_loop import unified_streaming_agent_loop
from streaming.buffer_pattern import ToolCallBuffer

class TestUnifiedStreamingBufferIntegration(unittest.TestCase):
    """Test buffer pattern integration in unified_streaming_loop."""
    
    @patch('streaming.unified_streaming_loop.dc_execute_tool')
    @patch('streaming.unified_streaming_loop.dc_get_tool_definitions')
    @patch('streaming.unified_streaming_loop.AsyncAnthropic')
    @patch('streaming.unified_streaming_loop.dc_initialize')
    async def test_buffer_handles_partial_function_calls(
        self, mock_initialize, mock_anthropic, mock_get_tools, mock_execute_tool
    ):
        """Test that buffer correctly handles partial function calls."""
        # Setup mocks
        mock_initialize.return_value = None
        mock_get_tools.return_value = [
            {
                "name": "dc_bash",
                "description": "Execute bash commands",
                "input_schema": {
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }
        ]
        
        # Mock AsyncAnthropic and streaming
        mock_client = AsyncMock()
        mock_messages = AsyncMock()
        mock_client.messages.create = mock_messages.create
        
        # Setup mock response chunks
        async def mock_stream():
            """Generate mock streaming response."""
            # Message start
            yield MagicMock(type="message_start")
            
            # Content block start
            start_chunk = MagicMock(type="content_block_start")
            start_chunk.content_block = MagicMock(type="text", text="Hello! I'll help you execute that command.")
            yield start_chunk
            
            # Text delta
            text_delta = MagicMock(type="content_block_delta")
            text_delta.delta = MagicMock(text=" Let me run that for you.")
            yield text_delta
            
            # Function call start (partial JSON)
            json_delta1 = MagicMock(type="content_block_delta", index=1)
            json_delta1.delta = MagicMock(type="input_json_delta", partial_json='{"command": "')
            yield json_delta1
            
            # Function call continuation
            json_delta2 = MagicMock(type="content_block_delta", index=1)
            json_delta2.delta = MagicMock(type="input_json_delta", partial_json='ls -la"')
            yield json_delta2
            
            # Function call completion
            json_delta3 = MagicMock(type="content_block_delta", index=1)
            json_delta3.delta = MagicMock(type="input_json_delta", partial_json='}')
            yield json_delta3
            
            # Content block stop (trigger function call execution)
            stop_chunk = MagicMock(type="content_block_stop", index=1)
            yield stop_chunk
            
            # Message stop
            yield MagicMock(type="message_stop")
        
        # Set up the mock response
        mock_messages.create.return_value = mock_stream()
        mock_anthropic.return_value = mock_client
        
        # Mock tool execution result
        tool_result = MagicMock()
        tool_result.output = "total 12\ndrwxr-xr-x 2 user user 4096 May 8 12:34 ."
        tool_result.error = None
        mock_execute_tool.return_value = tool_result
        
        # Call the function under test
        with patch('streaming.unified_streaming_loop.EnhancedStreamingCallbacks'):
            # Run the agent loop
            await unified_streaming_agent_loop(
                user_input="Please run ls -la",
                api_key="fake_api_key",
                use_real_adapters=False,
                callbacks={}
            )
        
        # Verify that execute_tool was called with the correct parameters
        mock_execute_tool.assert_called_once()
        args, kwargs = mock_execute_tool.call_args
        self.assertEqual("dc_bash", kwargs.get("tool_name"))
        self.assertEqual({"command": "ls -la"}, kwargs.get("tool_input"))
        
        print("Buffer pattern successfully integrated with unified_streaming_loop!")

if __name__ == "__main__":
    asyncio.run(unittest.main())