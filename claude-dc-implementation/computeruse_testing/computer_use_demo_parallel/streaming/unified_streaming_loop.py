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
import re
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
    from tool_use_buffer import ToolUseBuffer
    from xml_function_prompt import XML_SYSTEM_PROMPT
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
    from .tool_use_buffer import ToolUseBuffer
    from .xml_function_prompt import XML_SYSTEM_PROMPT

# Set up log directory
LOG_DIR = Path("/home/computeruse/computer_use_demo_custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Add file handler for streaming agent logs
file_handler = logging.FileHandler(LOG_DIR / "unified_streaming.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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
                # Fixed: Pass the list directly instead of trying to convert to async iterator
                tool_result = await dc_process_streaming_output(output_chunks)
                
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
                # Fixed: Pass the list directly instead of trying to convert to async iterator
                tool_result = await dc_process_streaming_output(output_chunks)
                
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
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 64000,
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
        
    def default_on_error(error, recoverable=True):
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
    
    # Try to load feature toggles
    feature_toggles = {}
    try:
        import json
        toggle_path = Path(__file__).parent / "feature_toggles.json"
        if toggle_path.exists():
            with open(toggle_path, "r") as f:
                feature_toggles = json.load(f)
                logger.info(f"Loaded feature toggles from {toggle_path}")
    except Exception as e:
        logger.warning(f"Could not load feature toggles: {str(e)}")

    # Create API parameters - use XML system prompt to improve function call handling
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": conversation_history,
        "system": XML_SYSTEM_PROMPT,  # Use XML-focused system prompt
        "tools": tools,
        "stream": True
    }
    
    # Disable thinking during streaming to avoid conflicts
    # Thinking mode during streaming can conflict with tool use
    if feature_toggles.get("use_streaming_thinking", False) and thinking_budget is not None:
        api_params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
    
    # Get the model from feature_toggles if available
    api_model = feature_toggles.get("api_model", model)
    if callable(api_model):  # Safety check to ensure model is a string
        api_model = model
    
    # Update the model in api_params
    api_params["model"] = api_model
    
    logger.info(f"Starting unified streaming session with model: {api_model}")
    
    # Initialize streaming session
    session = EnhancedStreamingSession()
    session.start_session()
    
    # Initialize the client
    client = AsyncAnthropic(api_key=api_key)
    
    # Initialize assistant response
    assistant_response = {"role": "assistant", "content": []}
    
    # Initialize tool use buffer for handling partial function calls
    tool_buffer = ToolUseBuffer()
    logger.info("Initialized buffer for handling partial function calls")
    
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
                        
                        # Add the assistant's tool use to the conversation history
                        tool_use_message = {
                            "role": "assistant",
                            "content": [{
                                "type": "tool_use",
                                "id": tool_id,
                                "name": tool_name,
                                "input": tool_input
                            }]
                        }
                        conversation_history.append(tool_use_message)
                        
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
                        
                        # Add delay before resuming to ensure complete processing
                        await asyncio.sleep(0.5)
                        
                        # Resume the stream with updated conversation
                        resume_params = {**api_params, "messages": conversation_history}
                        # Disable thinking on resume to avoid conflicts
                        if "thinking" in resume_params:
                            del resume_params["thinking"]
                            
                        # Resume the stream with the updated conversation
                        resume_stream = await client.messages.create(**resume_params)
                        
                        # Reset the tool buffer for new messages
                        tool_buffer.reset_attempts()
                        
                        # Continue processing the resumed stream
                        async for resume_chunk in resume_stream:
                            # Continue normal processing for resumed stream
                            if hasattr(resume_chunk, "type"):
                                resume_chunk_type = resume_chunk.type
                                
                                # Content block delta for text
                                if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                    if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                        enhanced_callbacks.on_text(resume_chunk.delta.text)
                                
                                # Process partial function calls in resumed stream
                                if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA and hasattr(resume_chunk, "index"):
                                    # Process with tool buffer
                                    content = ""
                                    if hasattr(resume_chunk.delta, "input_json_delta"):
                                        content = resume_chunk.delta.input_json_delta
                                    tool_id = getattr(resume_chunk.delta, "tool_use_id", None)
                                    
                                    # Handle with buffer
                                    if content:
                                        tool_buffer.handle_content_block_delta(
                                            resume_chunk.index, content, tool_id
                                        )
                                
                                # Process complete function calls in resumed stream
                                elif resume_chunk_type == StreamEventType.CONTENT_BLOCK_STOP and hasattr(resume_chunk, "index"):
                                    # Process complete function calls
                                    tool_call = tool_buffer.handle_content_block_stop(resume_chunk.index)
                                    
                                    if tool_call:
                                        # Extract tool details
                                        tool_name = tool_call["tool_name"]
                                        tool_params = tool_call["tool_params"]
                                        tool_id = tool_call["tool_id"] or f"tool_{resume_chunk.index}"
                                        
                                        # Validate parameters
                                        valid, message, fixed_params = tool_buffer.validate_parameters(
                                            tool_name, tool_params
                                        )
                                        
                                        if valid:
                                            # Execute tool
                                            tool_result, tool_result_content = await execute_streaming_tool(
                                                tool_name=tool_name,
                                                tool_input=fixed_params,
                                                tool_id=tool_id,
                                                session=session,
                                                enhanced_callbacks=enhanced_callbacks
                                            )
                                            
                                            # Add the assistant's tool use to the conversation history
                                            tool_use_message = {
                                                "role": "assistant",
                                                "content": [{
                                                    "type": "tool_use",
                                                    "id": tool_id,
                                                    "name": tool_name,
                                                    "input": fixed_params
                                                }]
                                            }
                                            conversation_history.append(tool_use_message)
                                            
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
                                            
                                            # Add delay before resuming to ensure complete processing
                                            await asyncio.sleep(0.5)
                                            
                                            # Resume the stream again with the updated conversation
                                            try:
                                                second_resume_params = {**resume_params, "messages": conversation_history}
                                                # Create a new stream with the updated conversation
                                                second_resume_stream = await client.messages.create(**second_resume_params)
                                                
                                                # Reset the tool buffer for new messages
                                                tool_buffer.reset_attempts()
                                                
                                                # Process the second resumed stream
                                                async for second_resume_chunk in second_resume_stream:
                                                    # Continue normal processing for the second resumed stream
                                                    if hasattr(second_resume_chunk, "type"):
                                                        second_resume_chunk_type = second_resume_chunk.type
                                                        
                                                        # Content block delta for text
                                                        if second_resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                                            if hasattr(second_resume_chunk.delta, "text") and second_resume_chunk.delta.text:
                                                                enhanced_callbacks.on_text(second_resume_chunk.delta.text)
                                            except Exception as second_resume_error:
                                                logger.error(f"Error resuming stream a second time: {str(second_resume_error)}")
                                                logger.error(traceback.format_exc())
                                                await enhanced_callbacks.on_error(f"Error resuming stream: {str(second_resume_error)}", True)
                                        else:
                                            # Report parameter validation error
                                            logger.warning(f"Parameter validation failed: {message}")
                                            error_message = f"\n[Tool parameter error: {message}]"
                                            enhanced_callbacks.on_text(error_message)
                                
                                # Handle thinking in resumed stream
                                elif resume_chunk_type == StreamEventType.THINKING:
                                    thinking_text = getattr(resume_chunk, "thinking", "")
                                    await enhanced_callbacks.on_thinking(thinking_text)
                                    session.add_thinking(thinking_text)
                
                # Content block delta
                elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                    # Process partial function calls
                    if hasattr(chunk, "index") and hasattr(chunk.delta, "input_json_delta"):
                        content = chunk.delta.input_json_delta
                        tool_id = getattr(chunk.delta, "tool_use_id", None)
                        
                        # Handle with buffer
                        tool_buffer.handle_content_block_delta(chunk.index, content, tool_id)
                        continue
                        
                    # If not a tool call or after processing, handle as text
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        enhanced_callbacks.on_text(chunk.delta.text)
                
                # Content block stop - process complete function calls
                elif chunk_type == StreamEventType.CONTENT_BLOCK_STOP:
                    if hasattr(chunk, "index"):
                        # Process with buffer - add small delay to ensure function call is complete
                        await asyncio.sleep(0.5)
                        
                        # Process complete function calls
                        tool_call = tool_buffer.handle_content_block_stop(chunk.index)
                        
                        if tool_call:
                            # Extract tool details
                            tool_name = tool_call["tool_name"]
                            tool_params = tool_call["tool_params"]
                            tool_id = tool_call["tool_id"] or f"tool_{chunk.index}"
                            
                            # Validate parameters
                            valid, message, fixed_params = tool_buffer.validate_parameters(
                                tool_name, tool_params
                            )
                            
                            if valid:
                                # Execute tool
                                tool_result, tool_result_content = await execute_streaming_tool(
                                    tool_name=tool_name,
                                    tool_input=fixed_params,
                                    tool_id=tool_id,
                                    session=session,
                                    enhanced_callbacks=enhanced_callbacks
                                )
                                
                                # Add the assistant's tool use to the conversation history
                                tool_use_message = {
                                    "role": "assistant",
                                    "content": [{
                                        "type": "tool_use",
                                        "id": tool_id,
                                        "name": tool_name,
                                        "input": fixed_params
                                    }]
                                }
                                conversation_history.append(tool_use_message)
                                
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
                                
                                # Add delay before resuming to ensure complete processing
                                await asyncio.sleep(0.5)
                                
                                # Resume the stream with the updated conversation
                                try:
                                    # Create a deep copy of API params to avoid modifying the original
                                    resume_params = {**api_params, "messages": conversation_history}
                                    # Disable thinking on resume to avoid conflicts
                                    if "thinking" in resume_params:
                                        del resume_params["thinking"]
                                        
                                    # Create a new stream with the updated conversation
                                    resume_stream = await client.messages.create(**resume_params)
                                    
                                    # Reset the tool buffer for new messages
                                    tool_buffer.reset_attempts()
                                    
                                    # Process the resumed stream
                                    async for resume_chunk in resume_stream:
                                        # Continue normal processing for resumed stream
                                        if hasattr(resume_chunk, "type"):
                                            resume_chunk_type = resume_chunk.type
                                            
                                            # Content block delta for text
                                            if resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                                if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                                    enhanced_callbacks.on_text(resume_chunk.delta.text)
                                except Exception as resume_error:
                                    logger.error(f"Error resuming stream: {str(resume_error)}")
                                    logger.error(traceback.format_exc())
                                    await enhanced_callbacks.on_error(f"Error resuming stream: {str(resume_error)}", True)
                            else:
                                # Report parameter validation error
                                logger.warning(f"Parameter validation failed: {message}")
                                error_message = f"\n[Tool parameter error: {message}]"
                                enhanced_callbacks.on_text(error_message)
                
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