"""
Enhanced streaming agent loop implementation for Claude DC.
This module provides robust streaming support with essential tools integration.
"""

import os
import sys
import asyncio
import logging
import traceback
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, AsyncGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_streaming_agent")

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    from dc_setup import dc_initialize
    from dc_executor import dc_execute_tool
    from registry.dc_registry import dc_get_tool_definitions
except ImportError:
    # When imported as a package
    from .dc_setup import dc_initialize
    from .dc_executor import dc_execute_tool
    from .registry.dc_registry import dc_get_tool_definitions

# Set up log directory
LOG_DIR = Path("/home/computeruse/computer_use_demo/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Add file handler for streaming agent logs
file_handler = logging.FileHandler(LOG_DIR / "dc_streaming_agent.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Default system prompt with namespace-isolated tool names
DC_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. dc_computer - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter

2. dc_bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute

3. dc_str_replace_editor - For viewing, creating, and editing files
   * ALWAYS include the 'command' and 'path' parameters
   * Different commands need different additional parameters

Be precise and careful with tool parameters. Always include all required parameters for each tool.
When using tools, wait for their output before continuing.
"""

# Streaming response types
class StreamEventType:
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_STOP = "content_block_stop"
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_STOP = "message_stop"
    THINKING = "thinking"
    ERROR = "error"

class ToolState:
    """State management for tools during streaming"""
    def __init__(self):
        self.active_tool = None
        self.active_tool_id = None
        self.active_tool_input = None
        self.active_tool_output = None
        self.tool_history = []
    
    def start_tool(self, tool_name: str, tool_input: Dict[str, Any], tool_id: str):
        """Start a new tool execution"""
        self.active_tool = tool_name
        self.active_tool_input = tool_input
        self.active_tool_id = tool_id
        self.active_tool_output = None
    
    def complete_tool(self, output: Any):
        """Complete the current tool execution"""
        self.tool_history.append({
            "tool": self.active_tool,
            "input": self.active_tool_input,
            "output": output,
            "id": self.active_tool_id
        })
        self.active_tool = None
        self.active_tool_input = None
        self.active_tool_id = None
        self.active_tool_output = None
    
    def is_tool_active(self) -> bool:
        """Check if a tool is currently active"""
        return self.active_tool is not None

class StreamingSession:
    """Manages state for a streaming session"""
    def __init__(self):
        self.message_buffer = []
        self.current_block = None
        self.tool_state = ToolState()
        self.chunks_processed = 0
        self.thinking_tokens_used = 0
        self.reconnect_count = 0
        self.last_error = None
        self.session_start_time = None
        self.session_end_time = None
    
    def start_session(self):
        """Start a new streaming session"""
        import time
        self.session_start_time = time.time()
        self.message_buffer = []
        self.current_block = None
        self.chunks_processed = 0
        self.reconnect_count = 0
        self.last_error = None
    
    def end_session(self):
        """End the current streaming session"""
        import time
        self.session_end_time = time.time()
        session_time = self.session_end_time - self.session_start_time
        logger.info(f"Streaming session completed: {self.chunks_processed} chunks processed in {session_time:.2f} seconds")
    
    def add_message_chunk(self, chunk: Any):
        """Add a message chunk to the buffer"""
        self.chunks_processed += 1
        
        # Handle different chunk types
        if hasattr(chunk, "type"):
            chunk_type = chunk.type
            
            if chunk_type == StreamEventType.CONTENT_BLOCK_START:
                self.current_block = chunk.content_block
                
                # If starting a new text block, initialize with empty text
                if self.current_block.type == "text":
                    self.message_buffer.append({
                        "type": "text",
                        "text": ""
                    })
                # If starting a tool use block, initialize tool state
                elif self.current_block.type == "tool_use":
                    self.message_buffer.append(self.current_block.model_dump())
                    self.tool_state.start_tool(
                        self.current_block.name,
                        self.current_block.input,
                        getattr(self.current_block, "id", "tool_1")
                    )
            
            elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                # Handle text delta
                if hasattr(chunk.delta, "text") and chunk.delta.text:
                    if self.message_buffer and self.message_buffer[-1]["type"] == "text":
                        self.message_buffer[-1]["text"] += chunk.delta.text
            
            elif chunk_type == StreamEventType.THINKING:
                # Track thinking tokens
                thinking_text = getattr(chunk, "thinking", "")
                self.thinking_tokens_used += len(thinking_text.split()) // 4  # Rough token estimation
    
    def get_message_content(self) -> List[Dict[str, Any]]:
        """Get the current message content"""
        return self.message_buffer.copy()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session"""
        import time
        current_time = time.time()
        session_time = (self.session_end_time or current_time) - (self.session_start_time or current_time)
        
        return {
            "chunks_processed": self.chunks_processed,
            "thinking_tokens_used": self.thinking_tokens_used,
            "reconnect_count": self.reconnect_count,
            "session_time": session_time,
            "has_active_tool": self.tool_state.is_tool_active(),
            "active_tool": self.tool_state.active_tool,
            "tools_used": len(self.tool_state.tool_history)
        }

async def execute_tool_streaming(
    tool_name: str, 
    tool_input: Dict[str, Any],
    tool_id: str,
    on_progress: Optional[Callable[[str, float], None]] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Execute a tool with progress updates during streaming.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        tool_id: The ID of the tool use in the conversation
        on_progress: Optional callback for progress updates
        
    Returns:
        Tuple of (tool_result, tool_result_content)
    """
    logger.info(f"Executing tool during streaming: {tool_name}")
    
    # Report initial progress
    if on_progress:
        await on_progress(f"Starting {tool_name} execution...", 0.0)
    
    try:
        # Check if we have a streaming implementation for this tool
        if tool_name == "dc_bash":
            try:
                # Try to import the streaming bash tool
                from tools.dc_bash import dc_execute_bash_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming bash implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_bash_tool_streaming(tool_input, on_progress):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    if "on_text" in callbacks:
                        callbacks["on_text"](chunk)
                
                # Process the collected output
                tool_result = await dc_process_streaming_output(
                    # Create a generator that yields the collected chunks
                    (chunk for chunk in output_chunks).__aiter__()
                )
                
                # Format the streaming result
                if tool_result.error:
                    tool_result_content = [{"type": "text", "text": tool_result.error}]
                else:
                    tool_result_content = [{"type": "text", "text": tool_result.output}]
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming bash implementation not available, falling back to standard")
                # Fall back to standard implementation
        
        # For other tools or if streaming implementation is not available
        # Execute the tool with our namespace-isolated executor
        tool_result = await dc_execute_tool(
            tool_name=tool_name,
            tool_input=tool_input
        )
        
        # Report completion
        if on_progress:
            await on_progress(f"Completed {tool_name} execution", 1.0)
        
        # Format the tool result for the API
        tool_result_content = []
        if tool_result.error:
            # Add error content
            tool_result_content = [{
                "type": "text", 
                "text": tool_result.error
            }]
        else:
            # Add output content
            if tool_result.output:
                tool_result_content.append({
                    "type": "text",
                    "text": tool_result.output
                })
            
            # Add image content if available
            if tool_result.base64_image:
                tool_result_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": tool_result.base64_image
                    }
                })
        
        return tool_result, tool_result_content
    
    except Exception as e:
        logger.error(f"Error executing tool during streaming: {str(e)}")
        if on_progress:
            await on_progress(f"Error: {str(e)}", 1.0)
        
        # Return error result
        tool_result_content = [{
            "type": "text", 
            "text": f"Error executing tool: {str(e)}\n\n{traceback.format_exc()}"
        }]
        return None, tool_result_content

async def dc_streaming_agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    model: str = "claude-3-opus-20240229",
    max_tokens: int = 16000,
    thinking_budget: Optional[int] = 4000,
    use_real_adapters: bool = False,
    callbacks: Optional[Dict[str, Callable]] = None
) -> List[Dict[str, Any]]:
    """
    Enhanced streaming agent loop for Claude with computer use capabilities.
    
    Args:
        user_input: The user's message
        conversation_history: The conversation history
        api_key: The Anthropic API key
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking (None to disable)
        use_real_adapters: Whether to use real adapters or mock implementations
        callbacks: Optional callbacks for UI integration
        
    Returns:
        Updated conversation history
    """
    # Ensure the DC implementation is initialized
    dc_initialize(use_real_adapters=use_real_adapters)
    
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []
    
    # Initialize callbacks if not provided
    if callbacks is None:
        callbacks = {}
    
    # Default callbacks that print to console
    def default_on_text(text):
        print(text, end="", flush=True)
        
    def default_on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        
    def default_on_tool_result(tool_name, tool_input, tool_result):
        print(f"\nTool output: {tool_result.output or tool_result.error}", flush=True)
    
    def default_on_progress(message, progress):
        print(f"\n[Progress: {message} - {progress:.0%}]", flush=True)
    
    # Get callbacks or use defaults
    on_text = callbacks.get("on_text", default_on_text)
    on_tool_use = callbacks.get("on_tool_use", default_on_tool_use)
    on_tool_result = callbacks.get("on_tool_result", default_on_tool_result)
    on_progress = callbacks.get("on_progress", default_on_progress)
    
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key provided and ANTHROPIC_API_KEY not set in environment")
    
    # Import Anthropic client
    try:
        from anthropic import AsyncAnthropic, APIError, APIStatusError, APIResponseValidationError
    except ImportError:
        logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
        raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")
    
    # Add the user message to the conversation if non-empty
    if user_input:
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
    
    # Get tool definitions from our registry
    tools = dc_get_tool_definitions()
    
    # Set up beta flags
    beta_flags = ["computer-use-2025-01-24"]  # Required for computer use tools
    if thinking_budget is not None:
        beta_flags.append("thinking-2023-05-24")  # Enable thinking
    
    # Create API parameters
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": conversation_history,
        "system": DC_SYSTEM_PROMPT,
        "tools": tools,
        "stream": True,
        "anthropic_beta": ",".join(beta_flags)
    }
    
    # Add thinking parameters if enabled
    if thinking_budget is not None:
        api_params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
    
    logger.info(f"Starting streaming session with model: {model}")
    
    # Initialize streaming session
    session = StreamingSession()
    session.start_session()
    
    # Initialize the client
    client = AsyncAnthropic(api_key=api_key)
    
    # Initialize assistant response
    assistant_response = {"role": "assistant", "content": []}
    
    try:
        # Make API call with streaming
        stream = await client.messages.create(**api_params)
        
        # Process the stream
        async for chunk in stream:
            # Add chunk to session
            session.add_message_chunk(chunk)
            
            # Process chunk based on type
            if hasattr(chunk, "type"):
                chunk_type = chunk.type
                
                # Content block start
                if chunk_type == StreamEventType.CONTENT_BLOCK_START:
                    block = chunk.content_block
                    
                    # Handle text blocks
                    if block.type == "text":
                        if block.text:
                            on_text(block.text)
                    
                    # Handle tool use blocks
                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = getattr(block, "id", "tool_1")
                        
                        on_tool_use(tool_name, tool_input)
                        
                        # Execute tool immediately during streaming
                        tool_result, tool_result_content = await execute_tool_streaming(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_id=tool_id,
                            on_progress=on_progress
                        )
                        
                        if tool_result:
                            on_tool_result(tool_name, tool_input, tool_result)
                        
                        # Add tool result to conversation
                        tool_result_message = {
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": tool_result_content
                            }]
                        }
                        
                        # Update conversation history with tool result
                        conversation_history.append(tool_result_message)
                        
                        # Add the expected output to the session's tool state
                        session.tool_state.complete_tool(tool_result_content)
                
                # Content block delta
                elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        text = chunk.delta.text
                        on_text(text)
                
                # Thinking
                elif chunk_type == StreamEventType.THINKING:
                    thinking_text = getattr(chunk, "thinking", "")
                    if "on_thinking" in callbacks:
                        callbacks["on_thinking"](thinking_text)
                    logger.info(f"Thinking: {thinking_text[:100]}...")
        
        # End streaming session
        session.end_session()
        
        # Add the assistant response to conversation history
        assistant_response["content"] = session.get_message_content()
        conversation_history.append(assistant_response)
        
        return conversation_history
    
    except (APIStatusError, APIResponseValidationError, APIError) as e:
        # Handle API errors
        logger.error(f"API error during streaming: {str(e)}")
        session.last_error = str(e)
        
        error_msg = f"I encountered an API error: {str(e)}"
        if "on_text" in callbacks:
            callbacks["on_text"](f"\n{error_msg}")
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        })
        
        # End streaming session
        session.end_session()
        return conversation_history
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during streaming: {str(e)}")
        session.last_error = str(e)
        
        error_msg = f"I encountered an unexpected error: {str(e)}"
        if "on_text" in callbacks:
            callbacks["on_text"](f"\n{error_msg}")
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        })
        
        # End streaming session
        session.end_session()
        return conversation_history

async def dc_streaming_main():
    """
    Main entry point for CLI usage with streaming.
    """
    print("\nClaude DC Custom Agent with Streaming\n")
    print("Enter your message (or 'exit' to quit):")
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set in environment")
        api_key = input("Enter your Anthropic API key: ")
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        # Get user input
        user_input = input("> ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        # Process user input in the streaming agent loop
        try:
            conversation_history = await dc_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                api_key=api_key,
                use_real_adapters=True  # Try to use real adapters if available
            )
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(dc_streaming_main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")