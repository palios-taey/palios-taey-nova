"""
Mock Streamlit implementation for testing.
This provides a way to test Streamlit callbacks without actually running the Streamlit UI.
"""

import logging
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mock_streamlit')

class MockStreamlit:
    """
    Mock Streamlit implementation that records what would be displayed
    and validates callback parameters.
    """
    
    def __init__(self, validate_callbacks=True):
        """Initialize the mock Streamlit with optional validation."""
        self.validate_callbacks = validate_callbacks
        self.messages = []
        self.current_message = ""
        self.tool_results = []
        self.api_responses = []
        self.errors = []
        
    def reset(self):
        """Reset the mock state."""
        self.messages = []
        self.current_message = ""
        self.tool_results = []
        self.api_responses = []
        self.errors = []
    
    def output_callback(self, content_block: Dict[str, Any]) -> None:
        """
        Process content blocks from Claude's responses.
        This mimics the Streamlit callback for displaying Claude's output.
        """
        if self.validate_callbacks:
            # Validate required fields based on block type
            if not isinstance(content_block, dict):
                self.errors.append(f"Content block is not a dict: {type(content_block)}")
                return
                
            if "type" not in content_block:
                self.errors.append(f"Content block missing 'type': {content_block}")
                return
        
        # Process different block types
        block_type = content_block.get("type")
        
        if block_type == "text":
            # Process text blocks
            text = content_block.get("text", "")
            is_delta = content_block.get("is_delta", False)
            
            if is_delta:
                # Append to current message for deltas
                self.current_message += text
            else:
                # Start new message for full blocks
                self.current_message = text
                
            # Record the message
            if not is_delta or not self.messages:
                self.messages.append(self.current_message)
            else:
                # Update the last message for deltas
                self.messages[-1] = self.current_message
                
            logger.debug(f"Text {'delta' if is_delta else 'block'}: {text[:50]}...")
            
        elif block_type == "thinking":
            # Process thinking blocks
            thinking = content_block.get("thinking", "")
            is_delta = content_block.get("is_delta", False)
            
            # Record thinking output but don't display it
            logger.debug(f"Thinking {'delta' if is_delta else 'block'}: {thinking[:50]}...")
            
        elif block_type == "tool_use":
            # Process tool use blocks
            tool_name = content_block.get("name")
            tool_id = content_block.get("id")
            tool_input = content_block.get("input", {})
            
            if self.validate_callbacks:
                if not tool_name:
                    self.errors.append(f"Tool use block missing 'name': {content_block}")
                if not tool_id:
                    self.errors.append(f"Tool use block missing 'id': {content_block}")
                if not isinstance(tool_input, dict):
                    self.errors.append(f"Tool input is not a dict: {type(tool_input)}")
            
            # Record tool use
            self.current_message += f"\n\nUsing tool: {tool_name}"
            if self.messages:
                self.messages[-1] = self.current_message
            else:
                self.messages.append(self.current_message)
                
            logger.info(f"Tool use: {tool_name} (ID: {tool_id})")
    
    def tool_output_callback(self, result, tool_use_id) -> None:
        """
        Process tool results.
        This mimics the Streamlit callback for displaying tool outputs.
        """
        if self.validate_callbacks:
            if not hasattr(result, 'output') and not hasattr(result, 'error'):
                self.errors.append(f"Tool result missing output/error fields: {result}")
            if not tool_use_id:
                self.errors.append(f"Tool output missing tool_use_id: {tool_use_id}")
        
        # Record tool output
        output = getattr(result, 'output', None) or getattr(result, 'error', "No output")
        self.tool_results.append({
            'tool_use_id': tool_use_id,
            'output': output,
            'error': getattr(result, 'error', None),
            'base64_image': getattr(result, 'base64_image', None)
        })
        
        # Update current message
        self.current_message += f"\n\nTool result: {output[:100]}..."
        if self.messages:
            self.messages[-1] = self.current_message
            
        logger.info(f"Tool output for ID {tool_use_id}: {output[:50]}...")
    
    def api_response_callback(self, request, response, error) -> None:
        """
        Process API responses and validate parameters.
        This mimics the Streamlit callback for tracking API responses.
        """
        if self.validate_callbacks:
            # This is the key validation that was causing the error
            # We don't require request to be non-None now
            if error is not None and not isinstance(error, Exception):
                self.errors.append(f"Error is not an Exception: {type(error)}")
        
        # Record the API response
        self.api_responses.append({
            'request': request,
            'response': response,
            'error': error
        })
        
        if error:
            logger.error(f"API error: {error}")
        else:
            logger.info("API response received successfully")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of what would be displayed in Streamlit."""
        return {
            'messages': self.messages,
            'tool_results': self.tool_results,
            'api_responses': self.api_responses,
            'errors': self.errors
        }