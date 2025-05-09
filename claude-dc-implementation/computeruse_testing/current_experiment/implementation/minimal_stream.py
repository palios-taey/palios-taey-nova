"""
Minimal implementation of streaming with tool use.
Focuses on the core functionality without UI components.
"""

import os
import sys
import asyncio
import inspect
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
import json

# Determine the correct paths for the container environment
if os.path.exists("/home/computeruse"):
    # We're in the container
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"

# Add all possible paths to Python path
paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Set the current directory to the computer_use_demo directory
# This can help with relative imports
os.chdir(str(computer_use_demo_dir))

# Import our utility modules
from .stream_config import (
    logger, ENABLE_STREAMING, ENABLE_THINKING, ENABLE_PROMPT_CACHING,
    ENABLE_EXTENDED_OUTPUT, ENABLE_TOKEN_EFFICIENT, DEFAULT_MODEL,
    COMPUTER_USE_BETA, TOOL_VERSION, MAX_TOKENS, THINKING_BUDGET,
    API_PROVIDER
)
from .stream_utils import log_event, log_api_call, log_response, log_tool_result, log_function_entry_exit

# Import the anthropic library first, which is likely to be available
try:
    from anthropic import Anthropic, APIError
    logger.info("Successfully imported Anthropic client")
except ImportError as e:
    logger.error(f"Failed to import Anthropic: {e}")
    raise

# Use a more explicit import approach for the tools
try:
    # Try importing through relative import first (looking in computer_use_demo_dir)
    sys.path.insert(0, str(computer_use_demo_dir))
    
    # Log all the paths to aid debugging
    logger.info(f"Python path: {json.dumps(sys.path, indent=2)}")
    
    # Check if the tools directory exists
    tools_dir = computer_use_demo_dir / "tools"
    if os.path.exists(tools_dir):
        logger.info(f"Tools directory exists at: {tools_dir}")
        logger.info(f"Contents: {os.listdir(tools_dir)}")
    else:
        logger.warning(f"Tools directory not found at: {tools_dir}")
    
    # Import via a direct path approach
    from computer_use_demo.tools import ToolResult, TOOL_GROUPS_BY_VERSION, ToolCollection
    logger.info("Successfully imported tools")
except ImportError as e:
    # Try an alternative import approach
    logger.warning(f"First import approach failed: {e}")
    try:
        # Try direct import from the full path
        sys.path.insert(0, str(computer_use_demo_dir))
        # Import from the tools module directly
        from tools import ToolResult, TOOL_GROUPS_BY_VERSION, ToolCollection
        logger.info("Successfully imported tools via alternative method")
    except ImportError as e2:
        logger.error(f"All import approaches failed: {e2}")
        raise

@log_function_entry_exit
async def run_streaming_test(
    messages: List[Dict[str, Any]],
    api_key: str,
    output_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    tool_callback: Optional[Callable[[Any, str], None]] = None
) -> None:
    """
    Run a minimal streaming test with tool use.
    
    Args:
        messages: The list of messages to send to the API
        api_key: The Anthropic API key
        output_callback: Optional callback for content output
        tool_callback: Optional callback for tool execution results
    """
    logger.info("Starting streaming test")
    
    # Default callbacks if none provided
    if output_callback is None:
        output_callback = lambda content: log_response(content, 
                                                    is_delta=content.get("is_delta", False) 
                                                    if isinstance(content, dict) else False)
    
    if tool_callback is None:
        tool_callback = log_tool_result
    
    # Get the tools for the specified version
    tool_group = TOOL_GROUPS_BY_VERSION.get(TOOL_VERSION)
    if not tool_group:
        logger.error(f"Invalid tool version: {TOOL_VERSION}")
        return
    
    # Create tool collection
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    logger.info(f"Created tool collection with {len(tool_collection.tools)} tools")
    
    # Create Anthropic client
    client = Anthropic(api_key=api_key, max_retries=2)
    logger.info("Created Anthropic client")
    
    # Set up beta flags
    betas = []
    
    # Add required beta flag for computer use
    if TOOL_VERSION == "computer_use_20250124":
        betas.append(COMPUTER_USE_BETA)
        logger.info(f"Added required beta flag: {COMPUTER_USE_BETA}")
    
    # Prepare API call parameters
    api_params = {
        "max_tokens": MAX_TOKENS,
        "messages": messages,
        "model": DEFAULT_MODEL,
        "system": [{
            "type": "text",
            "text": "You are Claude, an AI assistant. You are running in a controlled environment with access to tools."
        }],
        "tools": tool_collection.to_params(),
        "stream": ENABLE_STREAMING  # Always enable streaming
    }
    
    # Check if the client has beta namespace or supports beta flags directly
    has_beta_namespace = hasattr(client, "beta") and hasattr(client.beta, "messages")
    
    # Detect the API version and available methods
    messages_obj = client.beta.messages if has_beta_namespace else client.messages
    
    # For thinking budget - check if thinking is supported
    # Different versions of the SDK handle this differently
    if THINKING_BUDGET:
        try:
            # Try adding the thinking parameter - newer versions
            api_params["thinking"] = {"type": "enabled", "budget_tokens": THINKING_BUDGET}
            logger.info(f"Added thinking budget: {THINKING_BUDGET}")
        except Exception as e:
            logger.warning(f"Could not add thinking budget parameter: {e}")
    
    # The beta flags need to be handled differently based on SDK version
    if betas:
        try:
            # Check if this client version supports the beta parameter directly
            if "beta" in inspect.signature(messages_obj.create).parameters:
                api_params["beta"] = betas
                logger.info(f"Added beta flags via parameter: {betas}")
            else:
                # For newer SDK versions, beta flags might be set differently
                logger.info(f"Client doesn't support direct beta parameter, using alternative approach")
                for beta in betas:
                    logger.info(f"Attempting to add beta flag: {beta}")
                    # For newer SDK versions, this might be handled differently
        except Exception as e:
            logger.warning(f"Failed to add beta flags: {e}, continuing without them")
    
    log_api_call(api_params)
    
    try:
        logger.info("Making API call with streaming enabled")
        
        # Use the correct client structure based on what we detected
        if has_beta_namespace:
            logger.info("Using client.beta.messages.create()")
            # In this case, beta flags should be passed as parameter
            stream = client.beta.messages.create(**api_params)
        else:
            logger.info("Using client.messages.create()")
            # In this case, we need to modify beta flags approach
            
            # Remove beta parameter if it exists since it's not supported
            if "beta" in api_params:
                logger.info("Removing unsupported 'beta' parameter")
                del api_params["beta"]
                
            # Also remove thinking parameter if it exists and isn't supported
            if "thinking" in api_params:
                try:
                    # Check if thinking is supported in this version
                    if "thinking" not in inspect.signature(client.messages.create).parameters:
                        logger.info("Removing unsupported 'thinking' parameter")
                        del api_params["thinking"]
                except Exception:
                    # If check fails, remove it to be safe
                    logger.info("Removing potentially unsupported 'thinking' parameter")
                    api_params.pop("thinking", None)
            
            # Make the API call with the adjusted parameters
            stream = client.messages.create(**api_params)
            
        logger.info("Stream object created successfully")
        
        # To track all content blocks from the stream
        content_blocks = []
        
        # Process the stream
        for event in stream:
            # Log the raw event structure for debugging
            event_dict = event.model_dump() if hasattr(event, "model_dump") else str(event)
            log_event("stream_event", event_dict)
            
            if hasattr(event, "type"):
                if event.type == "content_block_start":
                    # New content block started
                    logger.info(f"New content block started: {event.content_block.type if hasattr(event.content_block, 'type') else 'unknown'}")
                    current_block = event.content_block
                    content_blocks.append(current_block)
                    
                    # Convert block to dict for callback
                    if hasattr(current_block, "model_dump"):
                        block_dict = current_block.model_dump()
                    else:
                        # Fallback if model_dump not available
                        block_dict = {"type": getattr(current_block, "type", "unknown")}
                        if hasattr(current_block, "text"):
                            block_dict["text"] = current_block.text
                        elif hasattr(current_block, "thinking"):
                            block_dict["thinking"] = current_block.thinking
                    
                    output_callback(block_dict)
                
                elif event.type == "content_block_delta":
                    # Content block delta received
                    if hasattr(event, "index") and event.index < len(content_blocks):
                        logger.info(f"Content block delta for index {event.index}")
                        
                        # Handle text delta
                        if hasattr(event.delta, "text") and event.delta.text:
                            logger.info(f"Text delta: {event.delta.text}")
                            if hasattr(content_blocks[event.index], "text"):
                                content_blocks[event.index].text += event.delta.text
                            else:
                                content_blocks[event.index].text = event.delta.text
                            
                            delta_block = {
                                "type": "text",
                                "text": event.delta.text,
                                "is_delta": True,
                            }
                            output_callback(delta_block)
                        
                        # Handle thinking delta
                        elif hasattr(event.delta, "thinking") and event.delta.thinking:
                            logger.info(f"Thinking delta: {event.delta.thinking}")
                            if hasattr(content_blocks[event.index], "thinking"):
                                content_blocks[event.index].thinking += event.delta.thinking
                            else:
                                content_blocks[event.index].thinking = event.delta.thinking
                            
                            delta_block = {
                                "type": "thinking",
                                "thinking": event.delta.thinking,
                                "is_delta": True,
                            }
                            output_callback(delta_block)
                
                elif event.type == "message_stop":
                    logger.info("Message generation complete")
                    break
        
        # Process tool usage from content blocks
        logger.info("Processing tool usage from content blocks")
        tool_blocks = [block for block in content_blocks if getattr(block, "type", None) == "tool_use"]
        
        if tool_blocks:
            logger.info(f"Found {len(tool_blocks)} tool use blocks")
            
            for tool_block in tool_blocks:
                # Extract tool information
                tool_name = getattr(tool_block, "name", "unknown")
                tool_id = getattr(tool_block, "id", "unknown")
                tool_input = getattr(tool_block, "input", {})
                
                logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                
                try:
                    # Set up streaming for tool outputs if available
                    for tool in tool_collection.tools:
                        if hasattr(tool, 'set_stream_callback'):
                            tool.set_stream_callback(
                                lambda chunk, tid=tool_id: tool_callback(
                                    ToolResult(output=chunk, error=None), 
                                    tid
                                )
                            )
                    
                    # Run the tool
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=tool_input,
                        streaming=True,  # Enable streaming for the tool
                    )
                    
                    # Log and process the result
                    tool_callback(result, tool_id)
                    
                except Exception as e:
                    logger.error(f"Error running tool {tool_name}: {e}")
                    # Create error result
                    error_result = ToolResult(
                        output=None,
                        error=f"Error executing tool: {str(e)}",
                        base64_image=None
                    )
                    tool_callback(error_result, tool_id)
        else:
            logger.info("No tool use blocks found in response")
        
        logger.info("Streaming test completed successfully")
    
    except APIError as e:
        logger.error(f"Anthropic API Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in streaming test: {e}")
        raise

@log_function_entry_exit
def get_api_key() -> str:
    """Get the Anthropic API key from environment or file."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        # Try to read from the standard location
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            api_key = api_key_path.read_text().strip()
            logger.info("Found API key in ~/.anthropic/api_key")
        else:
            logger.error("No API key found in environment or ~/.anthropic/api_key")
            raise ValueError("API key not found")
    
    return api_key