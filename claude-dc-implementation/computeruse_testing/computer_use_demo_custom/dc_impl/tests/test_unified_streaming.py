"""
Integration tests for the unified streaming implementation.

Tests the three key components of the unified streaming MVP:
1. Streaming responses
2. Tool use during streaming
3. Thinking capabilities
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the unified streaming implementation
from unified_streaming_loop import unified_streaming_agent_loop
from streaming_enhancements import EnhancedStreamingSession, EnhancedStreamingCallbacks

@pytest.mark.asyncio
async def test_basic_streaming_response():
    """Test basic streaming response without tools or thinking."""
    # Captured output
    captured_text = []
    
    # Callbacks
    def on_text(text):
        captured_text.append(text)
    
    # Run a simple query
    conversation = await unified_streaming_agent_loop(
        user_input="Hello, what is your name?",
        callbacks={"on_text": on_text},
        max_tokens=100  # Small token limit for test
    )
    
    # Check that we received some text chunks
    assert captured_text, "Should have received text chunks"
    assert len("".join(captured_text)) > 0, "Should have received non-empty text"
    
    # Check that conversation history was updated
    assert len(conversation) == 2, "Should have user message and assistant response"
    assert conversation[0]["role"] == "user", "First message should be from user"

@pytest.mark.asyncio
async def test_streaming_with_thinking():
    """Test streaming response with thinking capability."""
    # Captured output
    captured_text = []
    thinking_chunks = []
    
    # Callbacks
    def on_text(text):
        captured_text.append(text)
    
    def on_thinking(text):
        thinking_chunks.append(text)
    
    # Run a query that requires thinking
    conversation = await unified_streaming_agent_loop(
        user_input="What is 15 * 17? Show your work.",
        callbacks={
            "on_text": on_text,
            "on_thinking": on_thinking
        },
        thinking_budget=1000  # Enable thinking
    )
    
    # Check that we received thinking chunks
    assert thinking_chunks, "Should have received thinking chunks"
    
    # Check that we also received text chunks
    assert captured_text, "Should have received text chunks"
    
    # Check that conversation history was updated
    assert len(conversation) == 2, "Should have user message and assistant response"

@pytest.mark.asyncio
async def test_streaming_with_bash_tool():
    """Test streaming response with bash tool use."""
    # Captured output
    captured_text = []
    tool_executions = []
    
    # Callbacks
    def on_text(text):
        captured_text.append(text)
    
    def on_tool_use(tool_name, tool_input):
        tool_executions.append((tool_name, tool_input))
    
    # Run a query that should use the bash tool
    conversation = await unified_streaming_agent_loop(
        user_input="Run the 'ls' command to list files in the current directory.",
        callbacks={
            "on_text": on_text,
            "on_tool_use": on_tool_use
        }
    )
    
    # Check that we executed the bash tool
    assert tool_executions, "Should have executed at least one tool"
    assert any(tool_name == "dc_bash" for tool_name, _ in tool_executions), "Should have used bash tool"
    
    # Check that conversation history includes tool results
    tool_results = [
        msg for msg in conversation 
        if msg["role"] == "user" and isinstance(msg["content"], list) and msg["content"] and "tool_result" in msg["content"][0]
    ]
    assert tool_results, "Should have tool results in conversation history"

@pytest.mark.asyncio
async def test_streaming_with_file_operations():
    """Test streaming response with file operations."""
    # Captured output
    captured_text = []
    tool_executions = []
    
    # Callbacks
    def on_text(text):
        captured_text.append(text)
    
    def on_tool_use(tool_name, tool_input):
        tool_executions.append((tool_name, tool_input))
    
    # Create a temporary test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write("This is a test file for streaming file operations.")
        temp_path = temp_file.name
    
    try:
        # Run a query that should use the file operations tool
        conversation = await unified_streaming_agent_loop(
            user_input=f"View the contents of the file at {temp_path}",
            callbacks={
                "on_text": on_text,
                "on_tool_use": on_tool_use
            }
        )
        
        # Check that we executed the file operations tool
        assert tool_executions, "Should have executed at least one tool"
        assert any(tool_name == "dc_str_replace_editor" for tool_name, _ in tool_executions), "Should have used file operations tool"
    
    finally:
        # Clean up the test file
        try:
            os.unlink(temp_path)
        except:
            pass

@pytest.mark.asyncio
async def test_unified_streaming_integration():
    """
    Test the complete unified streaming implementation with all components:
    - Streaming response
    - Thinking capabilities
    - Tool use during streaming
    """
    # Captured output
    captured_text = []
    thinking_chunks = []
    tool_executions = []
    progress_updates = []
    
    # Callbacks
    def on_text(text):
        captured_text.append(text)
    
    def on_thinking(text):
        thinking_chunks.append(text)
    
    def on_tool_use(tool_name, tool_input):
        tool_executions.append((tool_name, tool_input))
    
    def on_progress(message, progress):
        progress_updates.append((message, progress))
    
    # Run a complex query that should use all capabilities
    conversation = await unified_streaming_agent_loop(
        user_input="Run the command 'ls -la' and explain what each column in the output means.",
        callbacks={
            "on_text": on_text,
            "on_thinking": on_thinking,
            "on_tool_use": on_tool_use,
            "on_progress": on_progress
        },
        thinking_budget=2000  # Enable thinking
    )
    
    # Check that we received thinking chunks
    assert thinking_chunks, "Should have received thinking chunks"
    
    # Check that we executed tools
    assert tool_executions, "Should have executed at least one tool"
    
    # Check that we received progress updates
    assert progress_updates, "Should have received progress updates"
    
    # Check that we received text chunks
    assert captured_text, "Should have received text chunks"
    
    # Check that conversation history was properly updated
    assert len(conversation) > 2, "Should have multiple turns in conversation history"
    
    # Check for completed response
    assert any("column" in "".join(captured_text) for text in captured_text), "Response should explain file listing columns"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])