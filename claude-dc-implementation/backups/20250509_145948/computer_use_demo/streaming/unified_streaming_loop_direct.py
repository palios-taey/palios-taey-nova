"""
Unified streaming agent loop for Claude DC with direct implementation.

This module provides a comprehensive implementation that combines:
1. Streaming responses - with incremental text output
2. Tool use during streaming - with real-time tool execution
3. Thinking capabilities - with proper integration
4. Direct implementation of tool buffer - with no imports
5. Built-in XML function call prompting - with no imports

The implementation focuses on robustness, error handling, and a seamless user experience
using a direct, no-imports approach for maximum stability during development.
"""

import os
import sys
import asyncio
import logging
import traceback
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, AsyncGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified_streaming")

# Set up log directory
LOG_DIR = Path("/home/computeruse/computer_use_demo/streaming/logs")
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

###############################
# DIRECT IMPLEMENTATION START #
###############################

# XML SYSTEM PROMPT - Directly embedded
XML_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools in a Linux environment.

# Tool Usage Guidelines

When using tools, you MUST ALWAYS use XML format function calls with the following structure:

<function_calls>
<invoke name="TOOL_NAME">
<parameter name="PARAM_NAME">PARAM_VALUE</parameter>
<!-- Additional parameters as needed -->
</invoke>
</function_calls>

## CRITICAL: Tool Usage Process

⚠️ EXTREMELY IMPORTANT: Before executing ANY tool, ALWAYS follow this exact process:

1. PLANNING PHASE: 
   - FIRST, pause and carefully think about what command you need
   - Determine the exact tool needed and all required parameters
   - Plan the complete XML structure in your mind

2. CONSTRUCTION PHASE:
   - Begin by writing these exact words: "I'll now construct a complete function call for [tool name]:"
   - Then construct the ENTIRE XML structure in one go
   - NEVER send partial XML structures

3. STRUCTURE REQUIREMENTS:
   - Opening and closing <function_calls> tags
   - Properly nested <invoke> tags with name attribute
   - ALL required <parameter> tags with proper values
   
4. VERIFICATION:
   - Confirm all XML tags are properly closed
   - Verify all required parameters are included
   - Check parameter values are correct

Attempting to execute partial or incomplete function calls will cause errors.

## Available Tools:

1. dc_bash - For executing shell commands
   EXAMPLE: To list files in a directory
   I'll now construct a complete function call for dc_bash:
   <function_calls>
   <invoke name="dc_bash">
   <parameter name="command">ls -la /home/computeruse</parameter>
   </invoke>
   </function_calls>

2. dc_computer - For interacting with the computer GUI
   EXAMPLE: To click the mouse
   I'll now construct a complete function call for dc_computer:
   <function_calls>
   <invoke name="dc_computer">
   <parameter name="action">click</parameter>
   <parameter name="coordinates">[100, 200]</parameter>
   </invoke>
   </function_calls>

3. dc_str_replace_editor - For viewing, creating, and editing files
   EXAMPLE: To read a file
   I'll now construct a complete function call for dc_str_replace_editor:
   <function_calls>
   <invoke name="dc_str_replace_editor">
   <parameter name="command">read</parameter>
   <parameter name="path">/path/to/file.txt</parameter>
   </invoke>
   </function_calls>

# Parameter Requirements

Always include ALL required parameters for each tool:

1. dc_bash:
   * REQUIRED: `command` - The shell command to execute

2. dc_computer:
   * REQUIRED: `action` - The action to perform (click, type, etc.)
   * Required for click: `coordinates` - The [x, y] coordinates to click
   * Required for type: `text` - The text to input

3. dc_str_replace_editor:
   * REQUIRED: `command` - The action to perform (read, write, etc.)
   * REQUIRED: `path` - The file path to operate on
   * Additional parameters depending on command

# XML Guidelines:

1. Always complete each XML tag before starting the next
2. Include quotes around parameter names and proper closing tags
3. Parameter values should be placed between opening and closing parameter tags
4. Do not use escape characters within parameter values

# Error Handling

If a tool returns an error:
1. Check that your XML was properly formed
2. Verify that all required parameters were included
3. Make corrections and try again with properly formatted XML

When using tools, always wait for their output before continuing with your response.
"""

# DEFAULT FEATURE TOGGLES - Directly embedded
DEFAULT_FEATURE_TOGGLES = {
    "use_streaming_thinking": True,
    "enable_tool_thinking": True,
    "tool_thinking_budget": 2000,
    "api_model": "claude-3-7-sonnet-20250219",
    "use_xml_prompts": True,
    "enable_buffer_delay": True,
    "buffer_delay_ms": 1000,
    "max_tokens": 64000,
    "enable_tool_buffer": True,
    "debug_logging": True,
    "use_response_chunking": True,
    "enforce_construction_prefix": True
}

# Get feature toggles
def get_feature_toggles() -> Dict[str, Any]:
    """
    Get feature toggle configuration from JSON file or defaults.
    
    Returns:
        Dict with feature toggle values.
    """
    try:
        # Try to load from JSON file
        toggle_path = Path(__file__).parent / "feature_toggles.json"
        if toggle_path.exists():
            with open(toggle_path, "r") as f:
                feature_toggles = json.load(f)
                logger.info(f"Loaded feature toggles from {toggle_path}")
                return feature_toggles
    except Exception as e:
        logger.warning(f"Error loading feature toggles: {str(e)}")
    
    # Fall back to defaults
    logger.info("Using default feature toggles")
    return DEFAULT_FEATURE_TOGGLES.copy()

# Stream State Management
class StreamState:
    """Tracks the state of a streaming session."""
    
    def __init__(self):
        self.is_interrupted = False
        self.interrupt_reason = None
        self.thinking_content = []
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def start_session(self):
        self.start_time = time.time()
        self.is_interrupted = False
        self.interrupt_reason = None
        self.thinking_content = []
        self.errors = []
    
    def end_session(self):
        self.end_time = time.time()
        if self.start_time:
            duration = self.end_time - self.start_time
            logger.info(f"Streaming session completed in {duration:.2f} seconds")
    
    def interrupt_stream(self, reason=None):
        self.is_interrupted = True
        self.interrupt_reason = reason
        logger.info(f"Stream interrupted: {reason}")
    
    def resume_stream(self):
        self.is_interrupted = False
        self.interrupt_reason = None
        logger.info("Stream resumed")
    
    def add_thinking(self, thinking):
        if thinking:
            self.thinking_content.append(thinking)
    
    def record_error(self, error, traceback=None):
        self.errors.append({"error": error, "traceback": traceback})
        logger.error(f"Error recorded: {error}")

# Enhanced callback handler
class EnhancedCallbacks:
    """Enhanced callback handler for streaming sessions."""
    
    def __init__(self, callbacks=None):
        self.callbacks = callbacks or {}
    
    def on_text(self, text):
        callback = self.callbacks.get("on_text")
        if callback and text:
            callback(text)
    
    async def on_tool_start(self, tool_name, tool_input):
        callback = self.callbacks.get("on_tool_use")
        if callback:
            callback(tool_name, tool_input)
    
    async def on_tool_progress(self, tool_name, message, progress):
        callback = self.callbacks.get("on_progress")
        if callback:
            callback(message, progress)
    
    async def on_tool_complete(self, tool_name, tool_input, tool_result):
        callback = self.callbacks.get("on_tool_result")
        if callback:
            callback(tool_name, tool_input, tool_result)
    
    async def on_thinking(self, thinking):
        callback = self.callbacks.get("on_thinking")
        if callback and thinking:
            callback(thinking)
    
    async def on_error(self, error, recoverable=True):
        callback = self.callbacks.get("on_error")
        if callback:
            callback(error, recoverable)

# Tool Use Buffer implementation - Direct embedding
class ToolUseBuffer:
    """
    Buffer for handling partial function calls during streaming.
    Accumulates JSON/XML fragments until complete to prevent race conditions.
    """
    
    def __init__(self):
        """Initialize a new tool use buffer."""
        self.json_buffers = {}  # Maps indices to accumulated JSON/XML
        self.tool_ids = {}      # Maps indices to tool use IDs
        self.attempt_count = 0  # For safety against infinite loops
        self.max_attempts = 3   # Maximum number of attempts before breaking
        self.debug_mode = DEFAULT_FEATURE_TOGGLES.get("debug_logging", False)
        
        # Configuration from feature toggles
        self.feature_toggles = get_feature_toggles()
        self.buffer_delay_enabled = self.feature_toggles.get("enable_buffer_delay", True)
        self.buffer_delay_ms = self.feature_toggles.get("buffer_delay_ms", 1000)
        
        if self.debug_mode:
            logger.info(f"ToolUseBuffer initialized with delay={self.buffer_delay_ms}ms enabled={self.buffer_delay_enabled}")
    
    def handle_content_block_delta(self, index: int, content: str, tool_id: Optional[str] = None) -> bool:
        """
        Handle a content block delta event by accumulating partial content.
        
        Args:
            index: The content block index
            content: The partial content (JSON or XML)
            tool_id: Optional tool use ID
            
        Returns:
            True if content was buffered, False otherwise
        """
        # Initialize buffer if needed
        if index not in self.json_buffers:
            self.json_buffers[index] = ""
            
        # Store tool ID if provided
        if tool_id is not None:
            self.tool_ids[index] = tool_id
            
        # Accumulate content
        self.json_buffers[index] += content
        
        # Log buffer update in debug mode
        if self.debug_mode:
            content_preview = self.json_buffers[index][:50] + "..." if len(self.json_buffers[index]) > 50 else self.json_buffers[index]
            logger.debug(f"Buffer {index} updated: {content_preview}")
        
        return True  # Content was buffered
    
    async def handle_content_block_stop(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Handle a content block stop event by processing the complete content.
        
        Args:
            index: The content block index
            
        Returns:
            Dict with tool call details if complete, None otherwise
        """
        # Check if we have content for this index
        if index not in self.json_buffers:
            return None
            
        # Add delay to ensure complete buffer if enabled
        if self.buffer_delay_enabled and self.buffer_delay_ms > 0:
            delay_seconds = self.buffer_delay_ms / 1000.0
            logger.info(f"Adding buffer delay of {delay_seconds:.2f}s to ensure complete function call")
            await asyncio.sleep(delay_seconds)
            
        buffer = self.json_buffers[index]
        tool_id = self.tool_ids.get(index)
        
        # First check for XML function call
        if '<function_calls>' in buffer and '</function_calls>' in buffer:
            result = self._process_xml_call(buffer, index, tool_id)
            if result is not None:
                self.attempt_count += 1  # Increment attempt counter
            return result
        
        # Check for JSON function call
        try:
            # Try to parse as JSON
            data = json.loads(buffer)
            
            # Extract tool name
            tool_name = None
            if "tool" in data:
                tool_name = data["tool"]
            elif "name" in data:
                tool_name = data["name"]
            else:
                # Default to bash if no tool is specified
                tool_name = "dc_bash"
                
            # Extract parameters
            if "parameters" in data:
                params = data["parameters"]
            elif "params" in data:
                params = data["params"]
            else:
                # Use whole object as parameters
                params = data
                
            # Remove from buffer
            self.json_buffers.pop(index, None)
            
            # Increment attempt counter
            self.attempt_count += 1
            
            return {
                "tool_name": tool_name,
                "tool_params": params,
                "tool_id": tool_id,
                "format": "json"
            }
        except json.JSONDecodeError:
            # Incomplete or invalid JSON - keep in buffer
            if self.debug_mode:
                logger.debug(f"Incomplete or invalid JSON for index {index}: {buffer}")
            return None
    
    def _process_xml_call(self, buffer: str, index: int, tool_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Process an XML function call."""
        # Log the buffer content in debug mode
        if self.debug_mode:
            logger.debug(f"Processing XML call: {buffer}")
            
        # Extract function name
        name_match = re.search(r'<invoke name="([^"]+)"', buffer)
        if not name_match:
            logger.warning(f"Invalid XML: missing function name")
            # Clear buffer to avoid getting stuck
            self.json_buffers.pop(index, None)
            return None
        
        function_name = name_match.group(1)
        
        # Extract parameters
        params = {}
        param_matches = re.finditer(r'<parameter name="([^"]+)">([^<]+)</parameter>', buffer)
        for match in param_matches:
            param_name = match.group(1)
            param_value = match.group(2)
            params[param_name] = param_value
        
        # Clear buffer
        self.json_buffers.pop(index, None)
        
        # Ensure dc_ prefix for tool names
        tool_name = function_name
        if not tool_name.startswith("dc_"):
            for prefix in ["dc_"]:
                if any(tool_name == t.replace(prefix, "") for t in ["bash", "computer", "str_replace_editor"]):
                    tool_name = f"{prefix}{tool_name}"
                    break
        
        return {
            "tool_name": tool_name,
            "tool_params": params,
            "tool_id": tool_id,
            "format": "xml"
        }
    
    def should_break(self) -> bool:
        """
        Check if we should break execution to prevent infinite loops.
        
        Returns:
            True if maximum attempts reached, False otherwise
        """
        return self.attempt_count >= self.max_attempts
    
    def reset_attempts(self):
        """Reset attempt counter."""
        self.attempt_count = 0
    
    def validate_parameters(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate and attempt to fix tool parameters.
        
        Args:
            tool_name: Name of the tool
            params: Tool parameters
            
        Returns:
            Tuple of (valid, message, fixed_params)
        """
        fixed = params.copy() if params else {}
        
        if tool_name == "dc_bash":
            # Check for command parameter
            if "command" not in fixed or not fixed["command"]:
                # Try alternative field names
                alt_fields = ["cmd", "bash", "shell", "terminal", "exec"]
                for field in alt_fields:
                    if field in fixed and fixed[field]:
                        fixed["command"] = fixed[field]
                        logger.info(f"Recovered command from {field} parameter")
                        break
                
                # Still missing command?
                if "command" not in fixed or not fixed["command"]:
                    return False, "Missing required 'command' parameter", fixed
        
        elif tool_name == "dc_computer":
            # Check for action parameter
            if "action" not in fixed or not fixed["action"]:
                # Try alternative field names
                alt_fields = ["operation", "type", "function", "command"]
                for field in alt_fields:
                    if field in fixed and fixed[field]:
                        fixed["action"] = fixed[field]
                        logger.info(f"Recovered action from {field} parameter")
                        break
                
                # Still missing action?
                if "action" not in fixed or not fixed["action"]:
                    return False, "Missing required 'action' parameter", fixed
        
        elif tool_name == "dc_str_replace_editor":
            # Check for required parameters
            if "command" not in fixed or not fixed["command"]:
                return False, "Missing required 'command' parameter", fixed
            
            if "path" not in fixed or not fixed["path"]:
                return False, "Missing required 'path' parameter", fixed
        
        return True, "Parameters validated successfully", fixed

#############################
# DIRECT IMPLEMENTATION END #
#############################

async def execute_streaming_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_id: str,
    session: StreamState,
    enhanced_callbacks: EnhancedCallbacks
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
        try:
            # Import within function scope to allow fallback if not available
            from dc_executor import dc_execute_tool
            tool_result = await dc_execute_tool(
                tool_name=tool_name,
                tool_input=tool_input
            )
        except ImportError:
            # Mock implementation for testing
            class ToolResult:
                def __init__(self, output=None, error=None, base64_image=None):
                    self.output = output
                    self.error = error
                    self.base64_image = base64_image
            
            # Simulate tool execution
            if tool_name == "dc_bash":
                if "command" in tool_input:
                    tool_result = ToolResult(output=f"Executed: {tool_input['command']}")
                else:
                    tool_result = ToolResult(error="Missing required 'command' parameter")
            elif tool_name == "dc_str_replace_editor":
                if "command" in tool_input and "path" in tool_input:
                    tool_result = ToolResult(output=f"Executed: {tool_input['command']} on {tool_input['path']}")
                else:
                    tool_result = ToolResult(error="Missing required parameters")
            else:
                tool_result = ToolResult(error=f"Unknown tool: {tool_name}")
        
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
            if hasattr(tool_result, 'base64_image') and tool_result.base64_image:
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
    This is a direct implementation with no imports for maximum stability.
    
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
    # Initialize DC implementation if needed
    try:
        from dc_setup import dc_initialize
        dc_initialize(use_real_adapters=use_real_adapters)
    except ImportError:
        logger.warning("DC initialization unavailable, continuing without it")
    
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
    enhanced_callbacks = EnhancedCallbacks({
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
    
    # Get tool definitions
    try:
        from registry.dc_registry import dc_get_tool_definitions
        tools = dc_get_tool_definitions()
    except ImportError:
        # Mock tool definitions for testing
        tools = [
            {
                "name": "dc_bash",
                "description": "Execute bash commands",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "dc_str_replace_editor",
                "description": "Read, write, or edit files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command (read, write, edit)"
                        },
                        "path": {
                            "type": "string",
                            "description": "The file path"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write (for write command)"
                        }
                    },
                    "required": ["command", "path"]
                }
            }
        ]
    
    # Get feature toggles (direct implementation)
    feature_toggles = get_feature_toggles()
    
    # Create API parameters - use XML system prompt to improve function call handling
    api_params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": conversation_history,
        "system": XML_SYSTEM_PROMPT,  # Directly used from embedded implementation
        "tools": tools,
        "stream": True
    }
    
    # Configure thinking mode based on feature toggles
    # Enable thinking for planning tool calls and other complex reasoning
    if feature_toggles.get("use_streaming_thinking", False) and thinking_budget is not None:
        # Calculate thinking budget - use specified budget or default to 4000
        thinking_tokens = thinking_budget
        api_params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_tokens
        }
        logger.info(f"Enabled thinking with budget of {thinking_tokens} tokens")
    
    # Get the model from feature_toggles if available
    api_model = feature_toggles.get("api_model", model)
    if callable(api_model):  # Safety check to ensure model is a string
        api_model = model
    
    # Update the model in api_params
    api_params["model"] = api_model
    
    logger.info(f"Starting unified streaming session with model: {api_model}")
    
    # Initialize streaming session
    session = StreamState()
    session.start_session()
    
    # Initialize the client
    client = AsyncAnthropic(api_key=api_key)
    
    # Initialize assistant response
    assistant_response = {"role": "assistant", "content": []}
    
    # Initialize tool use buffer for handling partial function calls
    tool_buffer = ToolUseBuffer()
    logger.info("Initialized buffer for handling partial function calls")
    
    # Track if we detected construction prefix
    found_construction_prefix = False
    
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
                            # Check for construction prefix if enabled
                            if feature_toggles.get("enforce_construction_prefix", False):
                                if "I'll now construct a complete function call for" in block.text:
                                    found_construction_prefix = True
                                    logger.info("Detected function call construction prefix")
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
                        
                        # Configure thinking for resuming the stream
                        # Still enable thinking but with smaller budget for tool planning
                        if feature_toggles.get("enable_tool_thinking", False):
                            # Use a smaller budget for tool planning
                            tool_thinking_budget = feature_toggles.get("tool_thinking_budget", 2000)
                            resume_params["thinking"] = {
                                "type": "enabled",
                                "budget_tokens": tool_thinking_budget
                            }
                            logger.info(f"Enabled tool thinking with budget of {tool_thinking_budget} tokens")
                        elif "thinking" in resume_params:
                            # If tool thinking not enabled, remove thinking to avoid conflicts
                            del resume_params["thinking"]
                            
                        # Reset construction prefix detection for the next response
                        found_construction_prefix = False
                            
                        # Resume the stream with the updated conversation
                        resume_stream = await client.messages.create(**resume_params)
                        
                        # Reset the tool buffer for new messages
                        tool_buffer.reset_attempts()
                        
                        # Continue processing the resumed stream
                        async for resume_chunk in resume_stream:
                            # Continue normal processing for resumed stream
                            if hasattr(resume_chunk, "type"):
                                resume_chunk_type = resume_chunk.type
                                
                                # Handle text content
                                if resume_chunk_type == StreamEventType.CONTENT_BLOCK_START:
                                    if hasattr(resume_chunk, "content_block"):
                                        block = resume_chunk.content_block
                                        if block.type == "text" and block.text:
                                            # Check for construction prefix
                                            if feature_toggles.get("enforce_construction_prefix", False):
                                                if "I'll now construct a complete function call for" in block.text:
                                                    found_construction_prefix = True
                                                    logger.info("Detected function call construction prefix")
                                            enhanced_callbacks.on_text(block.text)
                                
                                # Content block delta for text
                                elif resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                    if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                        # Check for construction prefix
                                        if feature_toggles.get("enforce_construction_prefix", False):
                                            if "I'll now construct a complete function call for" in resume_chunk.delta.text:
                                                found_construction_prefix = True
                                                logger.info("Detected function call construction prefix")
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
                                    tool_call = await tool_buffer.handle_content_block_stop(resume_chunk.index)
                                    
                                    # Skip if no construction prefix and it's required
                                    if feature_toggles.get("enforce_construction_prefix", False) and not found_construction_prefix:
                                        logger.warning("Skipping tool execution - no construction prefix detected")
                                        continue
                                    
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
                                            
                                            # Reset construction prefix detection for the next response
                                            found_construction_prefix = False
                                            
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
                                                        
                                                        # Handle text content
                                                        if second_resume_chunk_type == StreamEventType.CONTENT_BLOCK_START:
                                                            if hasattr(second_resume_chunk, "content_block"):
                                                                block = second_resume_chunk.content_block
                                                                if block.type == "text" and block.text:
                                                                    # Check for construction prefix
                                                                    if feature_toggles.get("enforce_construction_prefix", False):
                                                                        if "I'll now construct a complete function call for" in block.text:
                                                                            found_construction_prefix = True
                                                                            logger.info("Detected function call construction prefix")
                                                                    enhanced_callbacks.on_text(block.text)
                                                        
                                                        # Content block delta for text
                                                        elif second_resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                                            if hasattr(second_resume_chunk.delta, "text") and second_resume_chunk.delta.text:
                                                                # Check for construction prefix
                                                                if feature_toggles.get("enforce_construction_prefix", False):
                                                                    if "I'll now construct a complete function call for" in second_resume_chunk.delta.text:
                                                                        found_construction_prefix = True
                                                                        logger.info("Detected function call construction prefix")
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
                
                # Content block delta - process text and check for function calls
                elif chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                    # Check for construction prefix
                    if hasattr(chunk.delta, "text") and chunk.delta.text:
                        text = chunk.delta.text
                        if feature_toggles.get("enforce_construction_prefix", False):
                            if "I'll now construct a complete function call for" in text:
                                found_construction_prefix = True
                                logger.info("Detected function call construction prefix")
                    
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
                        # Skip if no construction prefix and it's required
                        if feature_toggles.get("enforce_construction_prefix", False) and not found_construction_prefix:
                            logger.warning("Skipping tool execution - no construction prefix detected")
                            continue
                            
                        # Process with buffer - add small delay to ensure function call is complete
                        await asyncio.sleep(0.5)
                        
                        # Process complete function calls
                        tool_call = await tool_buffer.handle_content_block_stop(chunk.index)
                        
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
                                
                                # Reset construction prefix detection for the next response
                                found_construction_prefix = False
                                
                                # Resume the stream with the updated conversation
                                try:
                                    # Create a deep copy of API params to avoid modifying the original
                                    resume_params = {**api_params, "messages": conversation_history}
                                    
                                    # Configure thinking for resuming the stream
                                    # Still enable thinking but with smaller budget for tool planning
                                    if feature_toggles.get("enable_tool_thinking", False):
                                        # Use a smaller budget for tool planning
                                        tool_thinking_budget = feature_toggles.get("tool_thinking_budget", 2000)
                                        resume_params["thinking"] = {
                                            "type": "enabled",
                                            "budget_tokens": tool_thinking_budget
                                        }
                                        logger.info(f"Enabled tool thinking with budget of {tool_thinking_budget} tokens")
                                    elif "thinking" in resume_params:
                                        # If tool thinking not enabled, remove thinking to avoid conflicts
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
                                            
                                            # Handle text content
                                            if resume_chunk_type == StreamEventType.CONTENT_BLOCK_START:
                                                if hasattr(resume_chunk, "content_block"):
                                                    block = resume_chunk.content_block
                                                    if block.type == "text" and block.text:
                                                        # Check for construction prefix
                                                        if feature_toggles.get("enforce_construction_prefix", False):
                                                            if "I'll now construct a complete function call for" in block.text:
                                                                found_construction_prefix = True
                                                                logger.info("Detected function call construction prefix")
                                                        enhanced_callbacks.on_text(block.text)
                                            
                                            # Content block delta for text
                                            elif resume_chunk_type == StreamEventType.CONTENT_BLOCK_DELTA:
                                                if hasattr(resume_chunk.delta, "text") and resume_chunk.delta.text:
                                                    # Check for construction prefix
                                                    if feature_toggles.get("enforce_construction_prefix", False):
                                                        if "I'll now construct a complete function call for" in resume_chunk.delta.text:
                                                            found_construction_prefix = True
                                                            logger.info("Detected function call construction prefix")
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
    print("\nUnified Streaming Demo with Direct Implementation\n")
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