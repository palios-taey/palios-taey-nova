"""
Main agent loop with streaming support for Claude DC.

This module provides a robust, production-ready agent loop implementation with:
- Token-by-token streaming output
- Seamless tool use integration during streaming
- Thinking capabilities
- Comprehensive error handling and recovery
- Session state management

This is a full replacement implementation designed to provide a stable foundation
for Claude DC with enhanced streaming capabilities.
"""

import os
import sys
import json
import time
import asyncio
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, AsyncGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_loop.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_loop")

# Import tool registry and models
from models.tool_models import ToolResult, Message
from tools.registry import get_tool_registry, get_tool_definitions, initialize_tools
from utils.error_handling import handle_api_error, handle_tool_error
from utils.streaming import StreamBuffer

# Default system prompt
SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You are running in a Linux environment with the following tools:

1. computer - For interacting with the computer GUI
   * ALWAYS include the 'action' parameter
   * For mouse actions that need coordinates, ALWAYS include the 'coordinates' parameter
   * For text input actions, ALWAYS include the 'text' parameter

2. bash - For executing shell commands
   * ALWAYS include the 'command' parameter with the specific command to execute

3. str_replace_editor - For viewing, creating, and editing files
   * ALWAYS include the 'command' and 'path' parameters
   * Different commands need different additional parameters

Be precise and careful with tool parameters. Always include all required parameters for each tool.
When using tools, wait for their output before continuing.
"""

class StreamingSession:
    """
    Manages a streaming session with Claude, including tool execution state,
    progress tracking, and streaming buffers.
    """
    
    def __init__(
        self,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
        model: str = "claude-3-7-sonnet-20240425",
        max_tokens: int = 16000,
        thinking_budget: Optional[int] = 4000,
        system_prompt: Optional[str] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize a streaming session.
        
        Args:
            conversation_history: The conversation history
            api_key: The Anthropic API key
            model: The Claude model to use
            max_tokens: Maximum number of tokens in the response
            thinking_budget: Number of tokens to allocate for thinking
            system_prompt: Custom system prompt (uses default if None)
            callbacks: Optional callbacks for UI integration
        """
        # Initialize session parameters
        self.conversation_history = conversation_history or []
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.callbacks = callbacks or {}
        
        # Stream state tracking
        self.current_stream = None
        self.is_streaming = False
        self.current_tool_use = None
        self.is_interrupted = False
        self.stream_buffer = StreamBuffer()
        self.active_tools = {}
        self.session_id = str(uuid.uuid4())
        
        # Get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("No API key provided and ANTHROPIC_API_KEY not set in environment")
        
        # Initialize Anthropic client
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
            raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")
        
        # Initialize the tool registry
        initialize_tools()
    
    async def get_stream_parameters(self, user_input: str) -> Dict[str, Any]:
        """
        Prepare parameters for the streaming API call.
        
        Args:
            user_input: The user's message
            
        Returns:
            Parameters for the API call
        """
        # Add the user message to the conversation if provided
        if user_input:
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
        
        # Get tool definitions from our registry
        tools = get_tool_definitions()
        
        # Set up beta flags
        beta_flags = ["computer-use-2025-01-24"]  # Required for computer use tools
        if self.thinking_budget is not None:
            beta_flags.append("thinking-2023-05-24")  # Enable thinking
        
        # Create API parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": self.conversation_history,
            "system": self.system_prompt,
            "tools": tools,
            "stream": True,
            "anthropic_beta": ",".join(beta_flags)
        }
        
        # Add thinking parameters if enabled
        if self.thinking_budget is not None:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
        
        return api_params
    
    async def process_streaming_chunk(self, chunk) -> bool:
        """
        Process a single streaming chunk from the API.
        
        Args:
            chunk: A streaming chunk from the Anthropic API
            
        Returns:
            True if a tool use was encountered, False otherwise
        """
        # Process content block start
        if hasattr(chunk, "type") and chunk.type == "content_block_start":
            block = chunk.content_block
            
            # Handle text blocks
            if block.type == "text":
                text = block.text
                if self._callback("on_text", text):
                    pass  # Callback handled the text
                self.stream_buffer.add_text(text)
            
            # Handle tool use blocks
            elif block.type == "tool_use":
                self.current_tool_use = {
                    "name": block.name,
                    "input": block.input,
                    "id": getattr(block, "id", f"tool_{uuid.uuid4()}")
                }
                
                # Call the tool use callback
                if self._callback("on_tool_use", self.current_tool_use["name"], self.current_tool_use["input"]):
                    pass  # Callback handled the tool use
                
                # Add to streaming buffer
                self.stream_buffer.add_tool_use(
                    block.name, 
                    block.input,
                    getattr(block, "id", f"tool_{uuid.uuid4()}")
                )
                
                # Return True to indicate a tool use was detected
                return True
        
        # Process content block delta
        elif hasattr(chunk, "type") and chunk.type == "content_block_delta":
            if hasattr(chunk.delta, "text") and chunk.delta.text:
                text = chunk.delta.text
                if self._callback("on_text", text):
                    pass  # Callback handled the text
                
                # Add to streaming buffer
                self.stream_buffer.append_text(text)
        
        # Process thinking blocks if present
        elif hasattr(chunk, "type") and chunk.type == "thinking":
            thinking_text = getattr(chunk, "thinking", "")
            if self._callback("on_thinking", thinking_text):
                pass  # Callback handled the thinking
        
        # No tool use detected in this chunk
        return False
    
    def _callback(self, callback_name: str, *args, **kwargs) -> bool:
        """
        Execute a callback if it exists.
        
        Args:
            callback_name: The name of the callback
            *args: Arguments for the callback
            **kwargs: Keyword arguments for the callback
            
        Returns:
            True if callback was executed, False otherwise
        """
        if callback_name in self.callbacks:
            try:
                self.callbacks[callback_name](*args, **kwargs)
                return True
            except Exception as e:
                logger.error(f"Error executing callback {callback_name}: {str(e)}")
        return False
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool with progress updates.
        
        Args:
            tool_name: The name of the tool to execute
            tool_input: The input parameters for the tool
            
        Returns:
            The tool result
        """
        tool_id = f"{tool_name}_{uuid.uuid4()}"
        
        # Track the active tool
        self.active_tools[tool_id] = {
            "name": tool_name,
            "start_time": time.time(),
            "status": "running",
            "progress": 0.0
        }
        
        # Define progress callback for real-time updates
        async def progress_callback(message: str, progress: float):
            self.active_tools[tool_id]["progress"] = progress
            self.active_tools[tool_id]["status"] = message
            if self._callback("on_tool_progress", tool_name, tool_input, message, progress):
                pass  # Callback handled the progress update
        
        try:
            # Look up the tool in the registry
            tool_registry = get_tool_registry()
            if tool_name not in tool_registry:
                logger.error(f"Tool not found: {tool_name}")
                return ToolResult(error=f"Tool not found: {tool_name}")
            
            # Get the executor and validator functions
            executor = tool_registry[tool_name]["executor"]
            validator = tool_registry[tool_name]["validator"]
            
            # Validate the parameters
            is_valid, error_message = validator(tool_input)
            if not is_valid:
                logger.error(f"Invalid tool parameters: {error_message}")
                return ToolResult(error=f"Invalid parameters: {error_message}")
            
            # Execute the tool with progress callback
            try:
                # Check if the tool supports streaming
                if hasattr(executor, "streaming") and executor.streaming:
                    # Use streaming execution if supported
                    tool_result = await executor(tool_input, progress_callback=progress_callback)
                else:
                    # Use regular execution
                    tool_result = await executor(tool_input)
                    # Add progress update after completion
                    await progress_callback("Completed", 1.0)
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                return handle_tool_error(tool_name, e)
            
            # Update active tool status
            self.active_tools[tool_id]["status"] = "completed"
            self.active_tools[tool_id]["progress"] = 1.0
            
            # Calculate execution time
            execution_time = time.time() - self.active_tools[tool_id]["start_time"]
            logger.info(f"Tool {tool_name} executed in {execution_time:.2f}s")
            
            # Call tool result callback
            if self._callback("on_tool_result", tool_name, tool_input, tool_result):
                pass  # Callback handled the tool result
            
            return tool_result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            self.active_tools[tool_id]["status"] = "error"
            self.active_tools[tool_id]["progress"] = 1.0
            
            # Report error in callback
            if self._callback("on_tool_error", tool_name, tool_input, str(e)):
                pass  # Callback handled the error
            
            return ToolResult(error=f"Tool execution error: {str(e)}")
    
    async def stream(self, user_input: str = "") -> AsyncGenerator[str, None]:
        """
        Stream a response to the user's input, handling tool use events.
        
        Args:
            user_input: The user's message
            
        Yields:
            Text chunks from Claude's response
        """
        # Initialize stream state
        self.is_streaming = True
        self.is_interrupted = False
        self.stream_buffer = StreamBuffer()
        self.current_tool_use = None
        
        try:
            # Get API parameters
            api_params = await self.get_stream_parameters(user_input)
            
            # Make API call with streaming
            logger.info(f"Starting streaming request to Claude API with model: {self.model}")
            self.current_stream = await self.client.messages.create(**api_params)
            
            # Process the stream
            assistant_response = {"role": "assistant", "content": []}
            
            async for chunk in self.current_stream:
                # Check if streaming was interrupted
                if self.is_interrupted:
                    logger.info("Streaming was interrupted")
                    break
                
                # Process the chunk
                tool_use_detected = await self.process_streaming_chunk(chunk)
                
                # If a tool use was detected, stop streaming and execute the tool
                if tool_use_detected:
                    logger.info(f"Tool use detected: {self.current_tool_use['name']}")
                    break
            
            # Add the assistant response to conversation history
            assistant_response["content"] = self.stream_buffer.get_content_blocks()
            self.conversation_history.append(assistant_response)
            
            # Execute tool if needed
            if self.current_tool_use:
                logger.info(f"Executing tool: {self.current_tool_use['name']}")
                
                # Execute the tool
                tool_result = await self.execute_tool(
                    tool_name=self.current_tool_use["name"],
                    tool_input=self.current_tool_use["input"]
                )
                
                # Format the tool result
                tool_result_content = []
                if tool_result.error:
                    tool_result_content = [{"type": "text", "text": tool_result.error}]
                else:
                    if tool_result.output:
                        tool_result_content.append({
                            "type": "text",
                            "text": tool_result.output
                        })
                    if tool_result.base64_image:
                        tool_result_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": tool_result.base64_image
                            }
                        })
                
                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": self.current_tool_use["id"],
                        "content": tool_result_content
                    }]
                })
                
                # Continue streaming with the tool result
                # Recursively call stream with empty user input
                async for chunk in self.stream(""):
                    yield chunk
            
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            
            # Call text callback with error
            if self._callback("on_text", f"\n{error_msg}"):
                pass  # Callback handled the error
            
            # Add error message to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": error_msg
                }]
            })
            
            # Yield the error message
            yield error_msg
        
        finally:
            # Reset streaming state
            self.is_streaming = False
            self.current_stream = None
    
    def interrupt(self):
        """
        Interrupt the current streaming response.
        """
        if self.is_streaming:
            self.is_interrupted = True
            logger.info("Interrupting streaming response")

async def agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    model: str = "claude-3-7-sonnet-20240425",
    max_tokens: int = 16000,
    thinking_budget: Optional[int] = 4000,
    system_prompt: Optional[str] = None,
    callbacks: Optional[Dict[str, Callable]] = None
) -> List[Dict[str, Any]]:
    """
    Main streaming agent loop for Claude with computer use capabilities.
    
    Args:
        user_input: The user's message
        conversation_history: The conversation history
        api_key: The Anthropic API key
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking
        system_prompt: Custom system prompt (uses default if None)
        callbacks: Optional callbacks for UI integration
        
    Returns:
        The updated conversation history
    """
    # Initialize the streaming session
    session = StreamingSession(
        conversation_history=conversation_history,
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        thinking_budget=thinking_budget,
        system_prompt=system_prompt,
        callbacks=callbacks
    )
    
    # Default callbacks that print to console
    def default_on_text(text):
        print(text, end="", flush=True)
        
    def default_on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        
    def default_on_tool_result(tool_name, tool_input, tool_result):
        output = tool_result.output or tool_result.error
        print(f"\nTool output: {output[:1000]}{'...' if len(output) > 1000 else ''}", flush=True)
    
    def default_on_tool_progress(tool_name, tool_input, message, progress):
        print(f"\r[{tool_name} progress: {progress:.0%}] {message}", end="", flush=True)
    
    def default_on_thinking(thinking_text):
        print(f"\n[Thinking: {thinking_text[:100]}...]", end="", flush=True)
    
    # Get callbacks or use defaults
    callbacks = callbacks or {}
    on_text = callbacks.get("on_text", default_on_text)
    on_tool_use = callbacks.get("on_tool_use", default_on_tool_use)
    on_tool_result = callbacks.get("on_tool_result", default_on_tool_result)
    on_tool_progress = callbacks.get("on_tool_progress", default_on_tool_progress)
    on_thinking = callbacks.get("on_thinking", default_on_thinking)
    
    # Start the streaming process
    logger.info(f"Starting agent loop with model: {model}")
    
    try:
        # Process the streaming response and collect output
        collected_text = []
        async for chunk in session.stream(user_input):
            collected_text.append(chunk)
    except Exception as e:
        logger.error(f"Error in agent loop: {str(e)}")
        # Handle API errors using the error handling utility
        handle_api_error(e)
    
    # Return the updated conversation history
    return session.conversation_history

async def main():
    """
    Main entry point for CLI usage of agent loop.
    """
    print("\nClaude Streaming Agent\n")
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
        user_input = input("\n> ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        # Process user input in the agent loop
        try:
            conversation_history = await agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                api_key=api_key
            )
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)