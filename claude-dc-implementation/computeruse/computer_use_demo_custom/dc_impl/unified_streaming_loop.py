"""
Unified streaming agent loop for Claude DC.

This module provides a comprehensive implementation that combines:
1. Streaming responses - with incremental text output
2. Tool use during streaming - with real-time tool execution
3. Thinking capabilities - with proper integration

The implementation focuses on robustness, error handling, and a seamless user experience.
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
logger = logging.getLogger("unified_streaming")

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    from dc_setup import dc_initialize
    from dc_executor import dc_execute_tool
    from registry.dc_registry import dc_get_tool_definitions
    from streaming_enhancements import (
        EnhancedStreamingSession, 
        EnhancedStreamingCallbacks,
        StreamState
    )
except ImportError:
    # When imported as a package
    from .dc_setup import dc_initialize
    from .dc_executor import dc_execute_tool
    from .registry.dc_registry import dc_get_tool_definitions
    from .streaming_enhancements import (
        EnhancedStreamingSession, 
        EnhancedStreamingCallbacks,
        StreamState
    )

# Set up log directory
LOG_DIR = Path("/home/computeruse/computer_use_demo_custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Add file handler for streaming agent logs
file_handler = logging.FileHandler(LOG_DIR / "unified_streaming.log")
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

# Streaming response event types
class StreamEventType:
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_STOP = "content_block_stop"
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_STOP = "message_stop"
    THINKING = "thinking"
    ERROR = "error"

async def execute_streaming_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_id: str,
    session: EnhancedStreamingSession,
    enhanced_callbacks: EnhancedStreamingCallbacks
) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Execute a tool with streaming support, handling different tools appropriately.
    
    Args:
        tool_name: The name of the tool to execute
        tool_input: The input parameters for the tool
        tool_id: The ID of the tool use in the conversation
        session: The enhanced streaming session
        enhanced_callbacks: The enhanced callbacks
        
    Returns:
        Tuple of (tool_result, tool_result_content)
    """
    logger.info(f"Executing streaming tool: {tool_name}")
    
    # Mark the stream as interrupted during tool execution
    session.interrupt_stream(f"Executing tool: {tool_name}")
    
    # Notify about tool start
    await enhanced_callbacks.on_tool_start(tool_name, tool_input)
    
    # Initialize progress callback
    async def progress_callback(message, progress):
        await enhanced_callbacks.on_tool_progress(tool_name, message, progress)
    
    try:
        # Check for streaming bash implementation
        if tool_name == "dc_bash":
            try:
                # Try to import the streaming bash tool
                from tools.dc_bash import dc_execute_bash_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming bash implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_bash_tool_streaming(tool_input, progress_callback):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    enhanced_callbacks.on_text(chunk)
                
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
                
                # Notify about tool completion
                await enhanced_callbacks.on_tool_complete(tool_name, tool_input, tool_result)
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming bash implementation not available, falling back to standard")
                
        # Check for streaming file operations implementation
        elif tool_name == "dc_str_replace_editor":
            try:
                # Try to import the streaming file operations tool
                from tools.dc_file import dc_execute_file_tool_streaming, dc_process_streaming_output
                logger.info("Using streaming file operations implementation")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_file_tool_streaming(tool_input, progress_callback):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    enhanced_callbacks.on_text(chunk)
                
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
                
                # Notify about tool completion
                await enhanced_callbacks.on_tool_complete(tool_name, tool_input, tool_result)
                
                return tool_result, tool_result_content
            except ImportError:
                logger.warning("Streaming file operations implementation not available, falling back to standard")
        
        # Fallback to standard implementation for other tools
        logger.info(f"Using standard implementation for tool: {tool_name}")
        
        # Execute using standard tool implementation
        await progress_callback(f"Starting {tool_name} execution...", 0.0)
        
        # Execute the tool with namespace-isolated executor
        tool_result = await dc_execute_tool(
            tool_name=tool_name,
            tool_input=tool_input
        )
        
        # Report completion
        await progress_callback(f"Completed {tool_name} execution", 1.0)
        
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
        
        # Notify about tool completion
        await enhanced_callbacks.on_tool_complete(tool_name, tool_input, tool_result)
        
        return tool_result, tool_result_content
    
    except Exception as e:
        logger.error(f"Error executing tool during streaming: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Notify about error
        await enhanced_callbacks.on_error(f"Error executing {tool_name}: {str(e)}")
        
        # Return error result
        tool_result_content = [{
            "type": "text", 
            "text": f"Error executing tool: {str(e)}\n\n{traceback.format_exc()}"
        }]
        return None, tool_result_content

async def unified_streaming_agent_loop(
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
    Unified streaming agent loop that integrates streaming responses, tool use, and thinking.
    
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
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
        
    def default_on_thinking(thinking):
        print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
        
    def default_on_error(error, recoverable):
        print(f"\n[Error: {error}]", flush=True)
    
    # Create enhanced callbacks
    enhanced_callbacks = EnhancedStreamingCallbacks({
        "on_text": callbacks.get("on_text", default_on_text),
        "on_tool_use": callbacks.get("on_tool_use", default_on_tool_use),
        "on_tool_result": callbacks.get("on_tool_result", default_on_tool_result),
        "on_progress": callbacks.get("on_progress", default_on_progress),
        "on_thinking": callbacks.get("on_thinking", default_on_thinking),
        "on_error": callbacks.get("on_error", default_on_error)
    })
    
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
    
    logger.info(f"Starting unified streaming session with model: {model}")
    
    # Initialize streaming session
    session = EnhancedStreamingSession()
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
            # Process chunk based on type
            if hasattr(chunk, "type"):
                chunk_type = chunk.type
                
                # Content block start
                if chunk_type == StreamEventType.CONTENT_BLOCK_START:
                    block = chunk.content_block
                    
                    # Handle text blocks
                    if block.type == "text":
                        if block.text:
                            enhanced_callbacks.on_text(block.text)
                    
                    # Handle tool use blocks
                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = getattr(block, "id", "tool_1")
                        
                        # Execute tool immediately during streaming
                        tool_result, tool_result_content = await execute_streaming_tool(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_id=tool_id,
                            session=session,
                            enhanced_callbacks=enhanced_callbacks
                        )
                        
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
                        
                        # Resume the stream with updated conversation
                        resume_stream = await client.messages.create(
                            **{**api_params, "messages": conversation_history}
                        )
                        
                        # Continue processing the resumed stream
                        async for resume_chunk in resume_stream:
                            # Continue normal processing for resumed stream
                            if hasattr(resume_chunk, "type"):
                                resume_chunk_type = resume_chunk.type
                                
                                # Content block delta for text
                                if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                    if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                        enhanced_callbacks.on_text(resume_chunk.delta.text)
                                
                                # Handle thinking in resumed stream
                                elif resume_chunk_type == StreamEventType.THINKING:
                                    thinking_text = getattr(resume_chunk, "thinking", "")
                                    await enhanced_callbacks.on_thinking(thinking_text)
                                    session.add_thinking(thinking_text)
                
                # Content block delta
                elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        enhanced_callbacks.on_text(chunk.delta.text)
                
                # Thinking
                elif chunk_type == StreamEventType.THINKING:
                    thinking_text = getattr(chunk, "thinking", "")
                    await enhanced_callbacks.on_thinking(thinking_text)
                    session.add_thinking(thinking_text)
        
        # End streaming session
        session.end_session()
        
        # Add the assistant response to conversation history
        # Note: In a real implementation, we would build this from the stream
        # Here we're simplifying for clarity
        assistant_response = {
            "role": "assistant",
            "content": "Response would be constructed from actual stream chunks"
        }
        conversation_history.append(assistant_response)
        
        return conversation_history
    
    except (APIStatusError, APIResponseValidationError, APIError) as e:
        # Handle API errors
        logger.error(f"API error during streaming: {str(e)}")
        session.record_error(f"API error: {str(e)}")
        await enhanced_callbacks.on_error(f"API error: {str(e)}", False)
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": f"I encountered an API error: {str(e)}"
            }]
        })
        
        # End streaming session
        session.end_session()
        return conversation_history
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during streaming: {str(e)}")
        logger.error(traceback.format_exc())
        session.record_error(f"Unexpected error: {str(e)}", traceback.format_exc())
        await enhanced_callbacks.on_error(f"Unexpected error: {str(e)}", False)
        
        # Add error message to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": f"I encountered an unexpected error: {str(e)}"
            }]
        })
        
        # End streaming session
        session.end_session()
        return conversation_history

async def demo_unified_streaming():
    """Demo function to test the unified streaming implementation"""
    print("\nUnified Streaming Demo\n")
    print("Enter your query below, or 'exit' to quit\n")
    
    conversation_history = []
    
    while True:
        user_input = input("> ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        try:
            # Call the unified streaming agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                thinking_budget=2000
            )
            print("\n")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(demo_unified_streaming())