"""
Enhancements for the streaming agent loop to improve the MVP implementation.

This module provides additional functionality to enhance the streaming agent loop:
1. Better handling of streaming interruptions
2. Improved thinking integration
3. Stream resumption capability
4. Enhanced error recovery
"""

import asyncio
import logging
import time
import json
import traceback
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streaming_enhancements")

# Define event types for streaming state machine
class StreamState:
    """State machine for streaming sessions"""
    INITIALIZING = "initializing"
    STREAMING = "streaming"
    TOOL_EXECUTION = "tool_execution"
    STREAM_INTERRUPTED = "stream_interrupted"
    RESUMING = "resuming"
    COMPLETED = "completed"
    ERROR = "error"

class EnhancedStreamingSession:
    """
    Enhanced session management for streaming responses with improved
    handling of interruptions, thinking, and error recovery.
    """
    def __init__(self):
        self.state = StreamState.INITIALIZING
        self.message_buffer = []
        self.current_block = None
        self.current_text_buffer = ""
        self.active_tools = {}
        self.completed_tools = []
        self.thinking_buffer = []
        self.interrupted_at = None
        self.error_log = []
        self.stats = {
            "text_chunks": 0,
            "thinking_chunks": 0,
            "tool_executions": 0,
            "interruptions": 0,
            "resumptions": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def start_session(self):
        """Start a new streaming session"""
        self.state = StreamState.STREAMING
        self.stats["start_time"] = time.time()
        logger.info(f"Starting enhanced streaming session")
    
    def end_session(self):
        """End the current streaming session"""
        self.state = StreamState.COMPLETED
        self.stats["end_time"] = time.time()
        duration = self.stats["end_time"] - self.stats["start_time"]
        logger.info(f"Completed streaming session in {duration:.2f}s")
    
    def interrupt_stream(self, reason: str):
        """Mark a stream as interrupted for later resumption"""
        self.state = StreamState.STREAM_INTERRUPTED
        self.interrupted_at = time.time()
        self.stats["interruptions"] += 1
        logger.info(f"Stream interrupted: {reason}")
    
    def resume_stream(self):
        """Resume an interrupted stream"""
        if self.state == StreamState.STREAM_INTERRUPTED:
            self.state = StreamState.RESUMING
            self.stats["resumptions"] += 1
            interruption_duration = time.time() - self.interrupted_at
            logger.info(f"Resuming stream after {interruption_duration:.2f}s interruption")
            self.state = StreamState.STREAMING
            return True
        return False
    
    def record_error(self, error: str, traceback_info: str = None):
        """Record an error that occurred during streaming"""
        self.state = StreamState.ERROR
        self.stats["errors"] += 1
        error_entry = {"time": time.time(), "error": error}
        if traceback_info:
            error_entry["traceback"] = traceback_info
        self.error_log.append(error_entry)
        logger.error(f"Streaming error: {error}")
    
    def add_thinking(self, thinking_text: str):
        """Add thinking content to the session"""
        self.thinking_buffer.append(thinking_text)
        self.stats["thinking_chunks"] += 1
    
    def get_thinking_content(self) -> str:
        """Get the complete thinking content"""
        return "\n".join(self.thinking_buffer)
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get the current state of the session with detailed information"""
        return {
            "state": self.state,
            "active_tools": self.active_tools,
            "completed_tools": self.completed_tools,
            "has_thinking": len(self.thinking_buffer) > 0,
            "thinking_chunks": self.stats["thinking_chunks"],
            "text_chunks": self.stats["text_chunks"],
            "message_buffer_size": len(self.message_buffer),
            "current_text_buffer_size": len(self.current_text_buffer),
            "error_count": self.stats["errors"],
            "interruptions": self.stats["interruptions"],
            "duration": (time.time() - self.stats["start_time"]) if self.stats["start_time"] else 0
        }

# Enhanced streaming callbacks
class EnhancedStreamingCallbacks:
    """
    Enhanced callbacks for streaming sessions with better progress reporting,
    thinking integration, and error handling.
    """
    def __init__(self, base_callbacks: Dict[str, Callable] = None):
        self.callbacks = base_callbacks or {}
        self.ui_updates = 0
        self.last_thinking_update = 0
        self.thinking_update_interval = 0.5  # seconds
    
    def on_text(self, text: str):
        """Handle text output with rate limiting"""
        self.ui_updates += 1
        if "on_text" in self.callbacks:
            self.callbacks["on_text"](text)
    
    async def on_thinking(self, thinking_text: str):
        """Handle thinking output with rate limiting"""
        current_time = time.time()
        # Only update UI with thinking at certain intervals to avoid overwhelming it
        if current_time - self.last_thinking_update > self.thinking_update_interval:
            if "on_thinking" in self.callbacks:
                self.callbacks["on_thinking"](thinking_text)
            self.last_thinking_update = current_time
    
    async def on_tool_start(self, tool_name: str, tool_input: Dict[str, Any]):
        """Handle tool start event"""
        if "on_tool_use" in self.callbacks:
            self.callbacks["on_tool_use"](tool_name, tool_input)
    
    async def on_tool_progress(self, tool_name: str, message: str, progress: float):
        """Handle tool progress update"""
        if "on_progress" in self.callbacks:
            self.callbacks["on_progress"](message, progress)
    
    async def on_tool_complete(self, tool_name: str, tool_input: Dict[str, Any], tool_result: Any):
        """Handle tool completion"""
        if "on_tool_result" in self.callbacks:
            self.callbacks["on_tool_result"](tool_name, tool_input, tool_result)
    
    async def on_error(self, error: str, recoverable: bool = True):
        """Handle streaming errors"""
        if "on_error" in self.callbacks:
            self.callbacks["on_error"](error, recoverable)
        elif "on_text" in self.callbacks:
            self.callbacks["on_text"](f"\n[Error: {error}]")
    
    async def on_state_change(self, old_state: str, new_state: str):
        """Handle streaming state changes"""
        if "on_state_change" in self.callbacks:
            self.callbacks["on_state_change"](old_state, new_state)

async def create_resumable_streaming_session(
    client,
    api_params: Dict[str, Any],
    session: EnhancedStreamingSession,
    enhanced_callbacks: EnhancedStreamingCallbacks,
    additional_parameters: Dict[str, Any] = None
):
    """
    Create a resumable streaming session that can handle interruptions,
    tool execution, and thinking integration seamlessly.
    
    Args:
        client: The Anthropic API client
        api_params: The base API parameters
        session: The enhanced streaming session
        enhanced_callbacks: The enhanced callbacks
        additional_parameters: Additional parameters to include in the API call
        
    Returns:
        AsyncGenerator yielding response chunks
    """
    # Start the session
    session.start_session()
    
    # Create a copy of the API parameters
    request_params = api_params.copy()
    
    # Add any additional parameters
    if additional_parameters:
        request_params.update(additional_parameters)
    
    try:
        # Make the API call with streaming
        logger.info("Starting API call with streaming")
        stream = await client.messages.create(**request_params)
        
        # Process the stream
        async for chunk in stream:
            yield chunk
    except Exception as e:
        session.record_error(f"Error in streaming API call: {str(e)}", traceback.format_exc())
        await enhanced_callbacks.on_error(f"Streaming error: {str(e)}")
        yield {"type": "error", "error": str(e)}

async def resume_stream_after_tool(
    client,
    api_params: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    session: EnhancedStreamingSession,
    enhanced_callbacks: EnhancedStreamingCallbacks
):
    """
    Resume a stream after a tool execution by creating a new streaming request
    with the updated conversation history.
    
    Args:
        client: The Anthropic API client
        api_params: The base API parameters
        conversation_history: The updated conversation history
        session: The enhanced streaming session
        enhanced_callbacks: The enhanced callbacks
        
    Returns:
        AsyncGenerator yielding response chunks
    """
    if not session.resume_stream():
        session.record_error("Cannot resume stream - not in interrupted state")
        await enhanced_callbacks.on_error("Cannot resume stream")
        return
    
    # Create new request parameters with updated conversation history
    resume_params = api_params.copy()
    resume_params["messages"] = conversation_history
    
    # Create a resumption marker for the UI
    if "on_text" in enhanced_callbacks.callbacks:
        enhanced_callbacks.callbacks["on_text"]("\n[Resuming response...]\n")
    
    # Make a new streaming request
    async for chunk in create_resumable_streaming_session(
        client, resume_params, session, enhanced_callbacks
    ):
        yield chunk

# Example usage
async def demo_enhanced_streaming():
    """Demonstrate enhanced streaming functionality"""
    from anthropic import AsyncAnthropic
    
    # Initialize session and callbacks
    session = EnhancedStreamingSession()
    
    def on_text(text):
        print(text, end="", flush=True)
    
    def on_thinking(thinking):
        print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
    
    callbacks = {
        "on_text": on_text,
        "on_thinking": on_thinking,
    }
    
    enhanced_callbacks = EnhancedStreamingCallbacks(callbacks)
    
    # Set up API parameters
    api_key = "your-api-key"  # Replace with actual key
    
    api_params = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": "Tell me about streaming APIs"}],
        "system": "You are Claude, an AI assistant.",
        "stream": True,
        "anthropic_beta": "thinking-2023-05-24"
    }
    
    # Add thinking budget
    api_params["thinking"] = {
        "type": "enabled",
        "budget_tokens": 1000
    }
    
    # Create Anthropic client
    client = AsyncAnthropic(api_key=api_key)
    
    # Start streaming session
    print("Starting enhanced streaming demo...\n")
    
    try:
        async for chunk in create_resumable_streaming_session(
            client, api_params, session, enhanced_callbacks
        ):
            # Process the chunk (handled by callbacks)
            pass
            
        # Report session stats
        print("\n\nSession Stats:")
        print(json.dumps(session.get_session_state(), indent=2))
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(demo_enhanced_streaming())