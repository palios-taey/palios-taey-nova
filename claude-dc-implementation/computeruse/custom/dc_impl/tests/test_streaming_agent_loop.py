"""
Test script for the streaming agent loop implementation.
"""

import os
import sys
import asyncio
import unittest
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the streaming agent loop
from dc_streaming_agent_loop import dc_streaming_agent_loop, DcStreamingSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_streaming_agent_loop")

class TestStreamingAgentLoop(unittest.TestCase):
    """Test cases for streaming agent loop implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Get API key from environment
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.skipTest("ANTHROPIC_API_KEY not set in environment")
        
        # Set up mock callbacks
        self.text_chunks = []
        self.tool_uses = []
        self.tool_results = []
        self.thinking_chunks = []
        
        self.callbacks = {
            "on_text": lambda text: self.text_chunks.append(text),
            "on_tool_use": lambda name, input: self.tool_uses.append((name, input)),
            "on_tool_result": lambda name, input, result: self.tool_results.append((name, input, result)),
            "on_thinking": lambda text: self.thinking_chunks.append(text)
        }
    
    async def collect_streaming_output(self, user_input):
        """Collect output from streaming agent loop."""
        conversation_history = await dc_streaming_agent_loop(
            user_input=user_input,
            api_key=self.api_key,
            use_real_adapters=False,  # Use mock implementations for testing
            callbacks=self.callbacks
        )
        return conversation_history
    
    def test_basic_streaming(self):
        """Test basic streaming response."""
        # Reset tracking
        self.text_chunks = []
        self.tool_uses = []
        self.tool_results = []
        
        # Run streaming agent loop with simple query
        conversation_history = asyncio.run(
            self.collect_streaming_output("What is the current date?")
        )
        
        # Verify text was received
        self.assertTrue(self.text_chunks, "No text chunks received")
        
        # Verify conversation history was updated
        self.assertEqual(len(conversation_history), 2)  # user + assistant
        self.assertEqual(conversation_history[0]["role"], "user")
        self.assertEqual(conversation_history[1]["role"], "assistant")
    
    def test_tool_use_streaming(self):
        """Test streaming with tool use."""
        # Reset tracking
        self.text_chunks = []
        self.tool_uses = []
        self.tool_results = []
        
        # Run streaming agent loop with tool use query
        conversation_history = asyncio.run(
            self.collect_streaming_output("Run the command 'ls -la'")
        )
        
        # Verify tool use was detected
        self.assertTrue(self.tool_uses, "No tool uses detected")
        
        # Verify at least one tool was dc_bash
        bash_tools = [t for t in self.tool_uses if t[0] == "dc_bash"]
        self.assertTrue(bash_tools, "No bash tool uses detected")
        
        # Verify conversation history contains tool use and result
        self.assertGreaterEqual(len(conversation_history), 3)  # user + assistant + tool result
    
    def test_streaming_session(self):
        """Test the streaming session class."""
        # Create a streaming session
        session = DcStreamingSession(
            api_key=self.api_key,
            use_real_adapters=False,  # Use mock implementations for testing
            callbacks=self.callbacks
        )
        
        # Test getting stream parameters
        async def test_params():
            params = await session.get_stream_parameters("Hello")
            self.assertIn("model", params)
            self.assertIn("stream", params)
            self.assertTrue(params["stream"])
            self.assertIn("tools", params)
        
        asyncio.run(test_params())
    
    def test_streaming_interrupt(self):
        """Test interrupting a streaming session."""
        # Create a streaming session
        session = DcStreamingSession(
            api_key=self.api_key,
            use_real_adapters=False,  # Use mock implementations for testing
            callbacks=self.callbacks
        )
        
        # Test interruption
        async def test_interrupt():
            # Start streaming in a task
            stream_task = asyncio.create_task(session.stream("Tell me about artificial intelligence"))
            
            # Wait a short time then interrupt
            await asyncio.sleep(0.5)
            session.interrupt()
            
            # Process the stream to completion
            chunks = []
            async for chunk in stream_task:
                chunks.append(chunk)
            
            # Verify streaming was interrupted
            self.assertTrue(session.is_interrupted)
        
        asyncio.run(test_interrupt())

if __name__ == "__main__":
    unittest.main()