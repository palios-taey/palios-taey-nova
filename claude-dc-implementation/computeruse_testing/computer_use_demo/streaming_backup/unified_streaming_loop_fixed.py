"""
Unified streaming agent loop for Claude DC (FIXED VERSION).

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
import copy

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
    # Import buffer pattern implementation
    from buffer_pattern import ToolCallBuffer
    logger.info("Using buffer pattern for function calls")
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
    # Import buffer pattern implementation
    from .buffer_pattern import ToolCallBuffer
    logger.info("Using buffer pattern for function calls")

# Set up log directory
LOG_DIR = Path("/home/computeruse/computer_use_demo_custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Add file handler for streaming agent logs
file_handler = logging.FileHandler(LOG_DIR / "unified_streaming.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Enhanced system prompt with clear tool usage instructions
DC_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools in a Linux environment.

# Tool Usage Guidelines

Answer the user's request using the relevant tool(s), if they are available. Before calling a tool, think about what you're looking for and check that ALL required parameters are provided or can be reasonably inferred from context.

1. dc_computer - For interacting with the computer GUI
   * REQUIRED: The 'action' parameter MUST be included
   * For mouse actions that need coordinates, the 'coordinates' parameter is REQUIRED
   * For text input actions, the 'text' parameter is REQUIRED

2. dc_bash - For executing shell commands
   * ⚠️ CRITICAL: The 'command' parameter is ABSOLUTELY REQUIRED
   * REQUIRED FORMAT: {"command": "your shell command"}
   * INCORRECT FORMATS (NEVER DO THESE):
     - {} (empty object)
     - {"prompt": "command"} (wrong parameter name)
     - Omitting the command parameter entirely
   * CORRECT EXAMPLES:
     - {"command": "ls -la"}
     - {"command": "cat /etc/hosts"}
     - {"command": "grep -r 'search term' /path"}

3. dc_str_replace_editor - For viewing, creating, and editing files
   * REQUIRED: The 'command' and 'path' parameters MUST be included
   * Different commands need different additional parameters

# Parameter Validation Process

For each tool call, follow this process:
1. Check that all REQUIRED parameters for the tool are provided or can be inferred
2. IF any required parameters are missing, ASK the user to provide these values
3. If the user provides a specific value for a parameter (especially in quotes), use that value EXACTLY
4. DO NOT make up values for or ask about optional parameters
5. VERIFY that parameter values match the expected format before executing the tool

# Tool Selection Guidelines

When selecting a tool:
1. Carefully analyze which of the provided tools is relevant to the user's request
2. For file operations, prefer dc_str_replace_editor over dc_bash when appropriate
3. For system information or running commands, use dc_bash with properly formatted parameters
4. For GUI interactions, use dc_computer with all required parameters

# Error Handling

If a tool returns an error:
1. Check if the error is due to invalid parameters - if so, correct and try again
2. If the error is due to permission issues, explain the limitation to the user
3. If the error persists after one retry, explain the issue clearly to the user
4. Provide alternative approaches when appropriate

When using tools, always wait for their output before continuing with your response.
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

def set_default_tool_parameters(
    tool_name: str, 
    tool_input: Dict[str, Any],
    conversation_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract and validate parameters for tools when they are missing or incomplete.
    
    Args:
        tool_name: The name of the tool
        tool_input: The input parameters provided
        conversation_history: The conversation history to use for extracting information
        
    Returns:
        Updated tool input with extracted parameters
    """
    # Create a copy to avoid modifying the original
    tool_input = tool_input.copy() if tool_input else {}
    
    # Log parameter extraction attempt
    logger.info(f"Parameter extraction for {tool_name} with input: {tool_input}")
    
    # Set default parameters for each tool type
    if tool_name == "dc_bash":
        # Make sure command parameter exists
        if "command" not in tool_input or not tool_input["command"]:
            import re
            
            # Log the parameter extraction attempt
            logger.info(f"Command parameter missing or empty for {tool_name}, attempting extraction")
            
            # Get the last user message
            last_user_message = None
            if conversation_history:
                # First search for the most recent user message with explicit command mentions
                for msg in reversed(conversation_history):
                    if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                        content = msg.get("content")
                        # Prioritize messages with likely command references
                        if any(keyword in content.lower() for keyword in 
                               ["command", "run", "execute", "bash", "terminal", "shell", "type"]):
                            last_user_message = content
                            logger.info(f"Found priority user message with command references: {last_user_message[:100]}...")
                            break
                
                # If no message with explicit command mentions found, use the most recent message
                if not last_user_message:
                    for msg in reversed(conversation_history):
                        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                            last_user_message = msg.get("content")
                            logger.info(f"Using most recent user message: {last_user_message[:100]}...")
                            break
            
            if last_user_message:
                # Try different patterns to extract a command in order of reliability
                
                # Pattern 1: Commands in quotes (highest reliability)
                command_match = re.search(r"['\"`]([^'\"]+)['\"`]", last_user_message)
                if command_match:
                    tool_input["command"] = command_match.group(1)
                    logger.info(f"HIGH CONFIDENCE - Extracted command from quotes: {tool_input['command']}")
                    return tool_input
                
                # Pattern 2: Commands after specific action phrases (medium-high reliability)
                cmd_phrases = [
                    # Most explicit patterns first
                    r"(?:run|execute)(?:\s+the)?(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"(?:use|type|enter|try)(?:\s+the)?(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"(?:issue|with|do|perform)(?:\s+the)?(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"bash(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"terminal(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"shell(?:\s+command)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"command(?:\s+is)?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)",
                    r"(?:please|can you)(?:\s+(?:run|execute|use|try|check))?\s+['`\"]?([\w\s\-\.\/\*\?\[\]\(\)\>\<\|\&\;]+?)['`\"]?(?:\.|\band\b|$|;)"
                ]
                
                for phrase in cmd_phrases:
                    cmd_match = re.search(phrase, last_user_message, re.IGNORECASE)
                    if cmd_match:
                        extracted_cmd = cmd_match.group(1).strip()
                        if extracted_cmd and len(extracted_cmd) > 3:  # Avoid too-short matches
                            tool_input["command"] = extracted_cmd
                            logger.info(f"MEDIUM CONFIDENCE - Extracted command from phrase: {tool_input['command']}")
                            return tool_input
                
                # Pattern 3: Common command patterns (like ls, cd, grep) (medium reliability)
                common_cmd_patterns = [
                    # Format: command with arguments
                    r"\b(ls|cd|grep|find|cat|mkdir|rm|cp|mv|pwd|ps|echo|touch|git|chmod|chown)[ \t]+([^\n;|&]+)",
                    # Format: command with flags
                    r"\b(ls|cd|grep|find|cat)[ \t]+(\-[a-zA-Z]+[ \t]+[^\n;|&]+)",
                    # Format: more complex commands with pipes
                    r"\b(grep|cat|ls|find)[ \t]+([^\n;|&\>]+[\|\>][^\n;|&]+)"
                ]
                
                for pattern in common_cmd_patterns:
                    common_cmd_match = re.search(pattern, last_user_message)
                    if common_cmd_match:
                        cmd = common_cmd_match.group(1) + " " + common_cmd_match.group(2).strip()
                        tool_input["command"] = cmd
                        logger.info(f"MEDIUM CONFIDENCE - Extracted common command pattern: {tool_input['command']}")
                        return tool_input
            
            # Check for potential commands in alternative fields (low reliability)
            possible_command_fields = ["prompt", "text", "input", "query", "code", "script", "command_text"]
            for field in possible_command_fields:
                if field in tool_input and tool_input[field] and isinstance(tool_input[field], str):
                    potential_cmd = tool_input[field].strip()
                    if potential_cmd:
                        # Try to extract command from quotes first
                        command_match = re.search(r"['\"`]([^'\"]+)['\"`]", potential_cmd)
                        if command_match:
                            tool_input["command"] = command_match.group(1)
                        else:
                            # Just use the field value directly
                            tool_input["command"] = potential_cmd
                        
                        logger.info(f"LOW CONFIDENCE - Extracted command from {field} parameter: {tool_input['command']}")
                        return tool_input
            
            # No reliable command found - log the issue
            logger.warning("No command could be extracted from context")
            
            # If we're still here, set a safe default with clear error message
            tool_input["command"] = "echo 'Error: Could not determine the command to execute. Please provide a specific command explicitly.'"
    
    return tool_input

async def execute_streaming_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_id: str,
    session: EnhancedStreamingSession,
    enhanced_callbacks: EnhancedStreamingCallbacks,
    conversation_history: List[Dict[str, Any]] = None
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
        # Apply default parameters if needed
        # Pass the conversation_history from the function scope rather than importing
        tool_input = set_default_tool_parameters(tool_name, tool_input, conversation_history)
        
        # Check for streaming bash implementation
        if tool_name == "dc_bash":
            try:
                # Try to import the streaming bash tool
                from tools.dc_bash_fixed import dc_execute_bash_tool_streaming, dc_process_streaming_output
                logger.info("Using fixed streaming bash implementation")
                logger.info(f"Tool input after default parameters: {tool_input}")
                
                # Collect streaming output chunks
                output_chunks = []
                async for chunk in dc_execute_bash_tool_streaming(tool_input, progress_callback):
                    # Add chunk to output collection
                    output_chunks.append(chunk)
                    # Display chunk to user in real-time
                    enhanced_callbacks.on_text(chunk)
                
                # Process the collected output directly with the list rather than trying to convert to an async iterator
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
                logger.warning("Fixed streaming bash implementation not available, falling back to standard")
                
        # Check for streaming file operations implementation
        elif tool_name == "dc_str_replace_editor":
            # NOTE: This would be implemented similarly to bash but we're focusing on bash first
            pass
        
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
    else:
        # Make a deep copy to avoid modifying the original
        conversation_history = copy.deepcopy(conversation_history)
    
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

    # Create API parameters
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": conversation_history,
        "system": DC_SYSTEM_PROMPT,
        "tools": tools,
        "stream": True
    }
    
    # IMPORTANT: Disable thinking completely for tool use to avoid API errors
    # (API requires special handling of thinking blocks with tool use)
    # See error: "Expected `thinking` or `redacted_thinking`, but found `tool_use`"
    thinking_budget = None
    
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
    
    # Initialize assistant response accumulator
    response_text_chunks = []
    current_tool_uses = {}  # Track tool uses by ID
    
    # Initialize tool call buffer for handling partial function calls
    tool_buffer = ToolCallBuffer()
    logger.info("Initialized ToolCallBuffer for handling partial function calls")
    
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
                            text = block.text
                            response_text_chunks.append(text)
                            enhanced_callbacks.on_text(text)
                    
                    # Handle tool use blocks
                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = getattr(block, "id", "tool_1")
                        
                        # Store the tool use for proper tracking
                        current_tool_uses[tool_id] = {
                            "name": tool_name,
                            "input": tool_input
                        }
                        
                        # Add tool use to conversation history BEFORE executing - CRITICAL for tool_use_id tracking
                        # This ensures the API knows about the tool use when we send the tool result
                        conversation_history.append({
                            "role": "assistant",
                            "content": [{
                                "type": "tool_use",
                                "id": tool_id,
                                "name": tool_name,
                                "input": tool_input
                            }]
                        })
                        
                        # Log the tool use for debugging
                        logger.info(f"Added tool use to conversation history: tool_id={tool_id}, tool_name={tool_name}")
                        
                        # Execute tool after adding to conversation history
                        tool_result, tool_result_content = await execute_streaming_tool(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_id=tool_id,
                            session=session,
                            enhanced_callbacks=enhanced_callbacks,
                            conversation_history=conversation_history
                        )
                        
                        # Add tool result to conversation with MATCHING ID - CRITICAL for tool_use_id tracking
                        tool_result_message = {
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_id,  # Must match the tool_id in the tool_use message
                                "content": tool_result_content
                            }]
                        }
                        
                        # Update conversation history with tool result
                        conversation_history.append(tool_result_message)
                        
                        # Log conversation state for debugging
                        logger.info(f"Added tool result to conversation history: tool_use_id={tool_id}")
                        
                        # Resume the stream with updated conversation
                        try:
                            # Create a deep copy of API params to avoid modifying the original
                            resume_params = copy.deepcopy(api_params)
                            resume_params["messages"] = conversation_history
                            
                            # Log the conversation structure for debugging
                            logger.info(f"Resuming stream with {len(conversation_history)} messages")
                            logger.info(f"Last message role: {conversation_history[-1]['role']}")
                            logger.info(f"Conversation sequence: {[msg['role'] for msg in conversation_history]}")
                            
                            # Create a new stream with the updated conversation history
                            resume_stream = await client.messages.create(**resume_params)
                            
                            # Continue processing the resumed stream
                            async for resume_chunk in resume_stream:
                                # Continue normal processing for resumed stream
                                if hasattr(resume_chunk, "type"):
                                    resume_chunk_type = resume_chunk.type
                                    
                                    # Content block start in resumed stream
                                    if resume_chunk_type == StreamEventType.CONTENT_BLOCK_START:
                                        if hasattr(resume_chunk, "content_block"):
                                            block = resume_chunk.content_block
                                            if block.type == "text" and block.text:
                                                response_text_chunks.append(block.text)
                                                enhanced_callbacks.on_text(block.text)
                                    
                                    # Content block delta for text
                                    elif resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                        if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                            response_text_chunks.append(resume_chunk.delta.text)
                                            enhanced_callbacks.on_text(resume_chunk.delta.text)
                                    
                                    # Handle thinking in resumed stream
                                    elif resume_chunk_type == StreamEventType.THINKING:
                                        thinking_text = getattr(resume_chunk, "thinking", "")
                                        await enhanced_callbacks.on_thinking(thinking_text)
                                        session.add_thinking(thinking_text)
                        except Exception as resume_error:
                            logger.error(f"Error resuming stream: {str(resume_error)}")
                            logger.error(traceback.format_exc())
                            await enhanced_callbacks.on_error(f"Error resuming stream: {str(resume_error)}", True)
                
                # Content block delta
                elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                    # First process with the buffer to handle partial function calls
                    if hasattr(chunk, "index"):
                        buffer_result = tool_buffer.process_content_block_delta(chunk.index, chunk.delta)
                        if buffer_result:
                            # This is a partial tool call, being buffered
                            logger.info(f"Buffering partial tool call: {buffer_result['buffer'][:50]}...")
                            continue
                    
                    # Handle regular text deltas
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        response_text_chunks.append(chunk.delta.text)
                        enhanced_callbacks.on_text(chunk.delta.text)
                
                # Content block stop - process complete function calls from buffer
                elif chunk_type == StreamEventType.CONTENT_BLOCK_STOP:
                    # Process with buffer - check for complete tool calls
                    if hasattr(chunk, "index"):
                        buffer_result = tool_buffer.process_content_block_stop(chunk.index)
                        
                        # If we have a result from the buffer
                        if buffer_result:
                            logger.info(f"Buffer processing result: {buffer_result['type']} for index {chunk.index}")
                            
                            # If we have a complete tool call from the buffer
                            if buffer_result["type"] == "complete_tool_call":
                                # Extract tool details
                                tool_name = buffer_result["tool_name"]
                                tool_params = buffer_result["tool_params"]
                                tool_id = buffer_result["tool_use_id"] or f"tool_{chunk.index}"
                                
                                logger.info(f"Complete tool call detected: {tool_name} with params: {tool_params}")
                                
                                # Store the tool use for proper tracking
                                current_tool_uses[tool_id] = {
                                    "name": tool_name,
                                    "input": tool_params
                                }
                                
                                # Add tool use to conversation history
                                conversation_history.append({
                                    "role": "assistant",
                                    "content": [{
                                        "type": "tool_use",
                                        "id": tool_id,
                                        "name": tool_name,
                                        "input": tool_params
                                    }]
                                })
                                
                                # Log tool addition to history
                                logger.info(f"Added tool use to conversation history: tool_id={tool_id}, tool_name={tool_name}")
                                
                                # Execute the tool
                                tool_result, tool_result_content = await execute_streaming_tool(
                                    tool_name=tool_name,
                                    tool_input=tool_params,
                                    tool_id=tool_id,
                                    session=session,
                                    enhanced_callbacks=enhanced_callbacks,
                                    conversation_history=conversation_history
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
                                
                                # Update conversation history
                                conversation_history.append(tool_result_message)
                                logger.info(f"Added tool result to conversation history: tool_use_id={tool_id}")
                                
                                # Resume the stream with updated conversation
                                try:
                                    # Copy API params and update conversation
                                    resume_params = copy.deepcopy(api_params)
                                    resume_params["messages"] = conversation_history
                                    
                                    # Log the conversation structure
                                    logger.info(f"Resuming stream with {len(conversation_history)} messages")
                                    logger.info(f"Last message role: {conversation_history[-1]['role']}")
                                    
                                    # Create a new stream with updated conversation history
                                    resume_stream = await client.messages.create(**resume_params)
                                    
                                    # Process the resumed stream
                                    async for resume_chunk in resume_stream:
                                        # Handle resume chunks (similar to main stream handling)
                                        if hasattr(resume_chunk, "type"):
                                            resume_chunk_type = resume_chunk.type
                                            
                                            # Handle the various event types for resumed stream
                                            if resume_chunk_type == StreamEventType.CONTENT_BLOCK_START:
                                                if hasattr(resume_chunk, "content_block"):
                                                    block = resume_chunk.content_block
                                                    if block.type == "text" and block.text:
                                                        response_text_chunks.append(block.text)
                                                        enhanced_callbacks.on_text(block.text)
                                            
                                            elif resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                                if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                                    response_text_chunks.append(resume_chunk.delta.text)
                                                    enhanced_callbacks.on_text(resume_chunk.delta.text)
                                except Exception as resume_error:
                                    logger.error(f"Error resuming stream: {str(resume_error)}")
                                    logger.error(traceback.format_exc())
                                    await enhanced_callbacks.on_error(f"Error resuming stream: {str(resume_error)}", True)
                            
                            # Handle error cases from buffer
                            elif buffer_result["type"] == "tool_call_error":
                                logger.warning(f"Tool call error from buffer: {buffer_result['error']}")
                                # Provide feedback to help Claude DC fix the function call
                                error_feedback = f"\n\n[Tool Call Error: {buffer_result['error']}]\n"
                                enhanced_callbacks.on_text(error_feedback)
                                response_text_chunks.append(error_feedback)
                
                # Thinking
                elif chunk_type == StreamEventType.THINKING:
                    thinking_text = getattr(chunk, "thinking", "")
                    await enhanced_callbacks.on_thinking(thinking_text)
                    session.add_thinking(thinking_text)
        
        # End streaming session
        session.end_session()
        
        # Build the complete response text
        full_response_text = "".join(response_text_chunks)
        
        # Add the assistant response to conversation history
        assistant_response = {
            "role": "assistant",
            "content": full_response_text
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