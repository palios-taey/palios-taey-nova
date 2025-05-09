#!/usr/bin/env python3
"""
Buffer pattern patch to apply to the existing Claude DC implementation.

This module provides functions to dynamically patch the existing Claude DC 
implementation with the buffer pattern to fix the race condition.
"""

import inspect
import logging
import sys
import os
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, Callable

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("buffer_patch")

def apply_buffer_patch():
    """
    Apply the buffer patch to the current environment.
    
    This function applies runtime patches to ensure the buffer pattern
    is used for processing function calls during streaming.
    """
    logger.info("Applying buffer pattern patch")
    
    try:
        # Import the buffer implementation
        from tool_use_buffer import ToolUseBuffer
    except ImportError:
        try:
            # Try with relative import
            from .tool_use_buffer import ToolUseBuffer
        except ImportError:
            logger.error("Could not import ToolUseBuffer - buffer patch cannot be applied")
            return False
        
    # Create global buffer instance
    global_buffer = ToolUseBuffer()
    logger.info("Created global ToolUseBuffer instance")
    
    # Patch processing functions if we're in the right module
    try:
        # Try to patch the unified streaming loop
        import unified_streaming_loop
        
        # Store original function for CONTENT_BLOCK_DELTA handling
        original_delta_handler = None
        for name, obj in inspect.getmembers(unified_streaming_loop):
            if inspect.isfunction(obj) and 'CONTENT_BLOCK_DELTA' in inspect.getsource(obj):
                original_delta_handler = obj
                break
        
        if original_delta_handler:
            # Create patched version of the function
            @wraps(original_delta_handler)
            def patched_delta_handler(*args, **kwargs):
                # Get chunk from args or kwargs
                chunk = None
                for arg in args:
                    if hasattr(arg, 'type') and hasattr(arg, 'delta'):
                        chunk = arg
                        break
                
                if chunk is None:
                    chunk = kwargs.get('chunk')
                
                # If it's a tool call delta, buffer it
                if (chunk and hasattr(chunk, 'delta') and 
                    hasattr(chunk.delta, 'type') and 
                    chunk.delta.type == 'input_json_delta'):
                    
                    # Get content and tool_id
                    content = getattr(chunk.delta, 'partial_json', '')
                    tool_id = getattr(chunk.delta, 'tool_use_id', None)
                    index = getattr(chunk, 'index', 0)
                    
                    # Buffer the content
                    global_buffer.handle_content_block_delta(index, content, tool_id)
                    
                    # Skip original handler
                    return None
                
                # Otherwise, call original function
                return original_delta_handler(*args, **kwargs)
            
            # Replace the function
            setattr(unified_streaming_loop, original_delta_handler.__name__, patched_delta_handler)
            logger.info(f"Patched {original_delta_handler.__name__} for CONTENT_BLOCK_DELTA handling")
        
        # Store original function for CONTENT_BLOCK_STOP handling
        original_stop_handler = None
        for name, obj in inspect.getmembers(unified_streaming_loop):
            if inspect.isfunction(obj) and 'CONTENT_BLOCK_STOP' in inspect.getsource(obj):
                original_stop_handler = obj
                break
        
        if original_stop_handler:
            # Create patched version of the function
            @wraps(original_stop_handler)
            def patched_stop_handler(*args, **kwargs):
                # Get chunk from args or kwargs
                chunk = None
                for arg in args:
                    if hasattr(arg, 'type') and arg.type == 'content_block_stop':
                        chunk = arg
                        break
                
                if chunk is None:
                    chunk = kwargs.get('chunk')
                
                # If it's a tool call stop, process it
                if chunk and hasattr(chunk, 'index'):
                    index = getattr(chunk, 'index', 0)
                    
                    # Process complete content
                    result = global_buffer.handle_content_block_stop(index)
                    
                    # If we have a complete tool call, use it
                    if result:
                        # TODO: Execute the tool with the result
                        logger.info(f"Complete tool call detected: {result['tool_name']}")
                        
                        # Skip original handler if we handled it
                        return None
                
                # Otherwise, call original function
                return original_stop_handler(*args, **kwargs)
            
            # Replace the function
            setattr(unified_streaming_loop, original_stop_handler.__name__, patched_stop_handler)
            logger.info(f"Patched {original_stop_handler.__name__} for CONTENT_BLOCK_STOP handling")
        
        logger.info("Buffer pattern patch applied successfully")
        return True
        
    except ImportError:
        logger.error("Could not import unified_streaming_loop - buffer patch cannot be applied")
        return False
    except Exception as e:
        logger.error(f"Error applying buffer patch: {str(e)}")
        return False

def use_xml_system_prompt():
    """
    Set up XML system prompt to guide Claude DC to use XML function calls.
    
    This helps prevent race conditions by using a more structured format.
    """
    logger.info("Setting up XML system prompt")
    
    try:
        # Import the XML system prompt
        try:
            from xml_function_prompt import XML_SYSTEM_PROMPT
        except ImportError:
            try:
                from .xml_function_prompt import XML_SYSTEM_PROMPT
            except ImportError:
                logger.error("Could not import XML_SYSTEM_PROMPT - XML prompt cannot be used")
                return False
        
        # Patch the system prompt used by unified_streaming_loop
        try:
            import unified_streaming_loop
            
            # Check if the module has a DC_SYSTEM_PROMPT attribute
            if hasattr(unified_streaming_loop, 'DC_SYSTEM_PROMPT'):
                # Replace it with XML prompt
                setattr(unified_streaming_loop, 'DC_SYSTEM_PROMPT', XML_SYSTEM_PROMPT)
                logger.info("XML system prompt applied")
                return True
        except ImportError:
            logger.error("Could not import unified_streaming_loop - XML prompt cannot be applied")
            return False
    except Exception as e:
        logger.error(f"Error applying XML system prompt: {str(e)}")
        return False
    
    return False

# Automatically apply patch if environment variable is set
if os.environ.get("CLAUDE_DC_USE_BUFFER") == "1":
    apply_buffer_patch()
    
# Automatically use XML prompt if environment variable is set
if os.environ.get("CLAUDE_DC_USE_XML_PROMPT") == "1":
    use_xml_system_prompt()