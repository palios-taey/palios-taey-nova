"""
Unified streaming agent loop with tool integration.

This module implements a streaming-compatible agent loop that enables
token-by-token output with seamless tool integration. It supports
real-time progress reporting, thinking capabilities, and graceful
error handling.
"""

import os
import sys
import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_streaming_agent_loop")

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    from dc_setup import dc_initialize
    from dc_executor import dc_execute_tool
    from registry.dc_registry import dc_get_tool_definitions
    from models.dc_models import DCToolResult
except ImportError:
    # When imported as a package
    from .dc_setup import dc_initialize
    from .dc_executor import dc_execute_tool
    from .registry.dc_registry import dc_get_tool_definitions
    from .models.dc_models import DCToolResult

# Set up log directory
LOG_DIR = Path("/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Add file handler for streaming agent logs
file_handler = logging.FileHandler(LOG_DIR / "dc_streaming_agent_loop.log")
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

class DcStreamingSession:
    """
    Manages a streaming session with Claude, including tool execution state,
    progress tracking, and streaming buffers.
    """
    
    def __init__(
        self,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
        model: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = 16000,
        thinking_budget: Optional[int] = 4000,
        use_real_adapters: bool = False,
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
            use_real_adapters: Whether to use real adapters or mock implementations
            callbacks: Optional callbacks for UI integration
        """
        # Initialize session parameters
        self.conversation_history = conversation_history or []
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.use_real_adapters = use_real_adapters
        self.callbacks = callbacks or {}
        
        # Stream state tracking
        self.current_stream = None
        self.is_streaming = False
        self.current_tool_use = None
        self.is_interrupted = False
        self.streaming_buffer = []
        self.active_tools = {}
        
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
        
        # Initialize the DC implementation
        dc_initialize(use_real_adapters=self.use_real_adapters)
    
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
        tools = dc_get_tool_definitions()
        
        # Set up beta flags
        beta_flags = ["computer-use-2025-01-24"]  # Required for computer use tools
        if self.thinking_budget is not None:
            beta_flags.append("thinking-2023-05-24")  # Enable thinking
        
        # Create API parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": self.conversation_history,
            "system": DC_SYSTEM_PROMPT,
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
                self.streaming_buffer.append({
                    "type": "text",
                    "text": text
                })
            
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
                self.streaming_buffer.append(block.model_dump())
                
                # Return True to indicate a tool use was detected
                return True
        
        # Process content block delta
        elif hasattr(chunk, "type") and chunk.type == "content_block_delta":
            if hasattr(chunk.delta, "text") and chunk.delta.text:
                text = chunk.delta.text
                if self._callback("on_text", text):
                    pass  # Callback handled the text
                
                # Update the last text block or create a new one
                if self.streaming_buffer and self.streaming_buffer[-1].get("type") == "text":
                    self.streaming_buffer[-1]["text"] += text
                else:
                    self.streaming_buffer.append({
                        "type": "text",
                        "text": text
                    })
        
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
    
    async def execute_tool_streaming(self, tool_name: str, tool_input: Dict[str, Any]) -> DCToolResult:
        """
        Execute a tool with streaming progress updates.
        
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
            # Execute the tool with our executor
            # For now we don't have streaming tool execution directly integrated
            tool_result = await dc_execute_tool(
                tool_name=tool_name,
                tool_input=tool_input
            )
            
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
            
            return DCToolResult(error=f"Tool execution error: {str(e)}")
    
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
        self.streaming_buffer = []
        self.current_tool_use = None
        
        try:
            # Get API parameters
            api_params = await self.get_stream_parameters(user_input)
            
            # Make API call with streaming
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
            assistant_response["content"] = self.streaming_buffer
            self.conversation_history.append(assistant_response)
            
            # Execute tool if needed
            if self.current_tool_use:
                logger.info(f"Executing tool: {self.current_tool_use['name']}")
                
                # Execute the tool
                tool_result = await self.execute_tool_streaming(
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

async def dc_streaming_agent_loop(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 16000,
    thinking_budget: Optional[int] = 4000,
    use_real_adapters: bool = False,
    callbacks: Optional[Dict[str, Callable]] = None
) -> List[Dict[str, Any]]:
    """
    Main streaming agent loop for Claude with computer use capabilities.
    Uses namespace isolation to avoid conflicts with production code.
    
    Args:
        user_input: The user's message
        conversation_history: The conversation history
        api_key: The Anthropic API key
        model: The Claude model to use
        max_tokens: Maximum number of tokens in the response
        thinking_budget: Number of tokens to allocate for thinking
        use_real_adapters: Whether to use real adapters or mock implementations
        callbacks: Optional callbacks for UI integration
        
    Returns:
        The updated conversation history
    """
    # Initialize the streaming session
    session = DcStreamingSession(
        conversation_history=conversation_history,
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        thinking_budget=thinking_budget,
        use_real_adapters=use_real_adapters,
        callbacks=callbacks
    )
    
    # Default callbacks that print to console
    def default_on_text(text):
        print(text, end="", flush=True)
        
    def default_on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        
    def default_on_tool_result(tool_name, tool_input, tool_result):
        print(f"\nTool output: {tool_result.output or tool_result.error}", flush=True)
    
    # Get callbacks or use defaults
    on_text = callbacks.get("on_text", default_on_text)
    on_tool_use = callbacks.get("on_tool_use", default_on_tool_use)
    on_tool_result = callbacks.get("on_tool_result", default_on_tool_result)
    
    # Start the streaming process
    logger.info(f"Starting streaming agent loop with model: {model}")
    
    # Process the streaming response
    async for _ in session.stream(user_input):
        pass  # The callbacks handle the output
    
    # Return the updated conversation history
    return session.conversation_history

async def dc_streaming_main():
    """
    Main entry point for CLI usage of streaming agent loop.
    """
    print("\nClaude DC Streaming Agent (Namespace Isolated)\n")
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
                use_real_adapters=True  # Use real adapters if available
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