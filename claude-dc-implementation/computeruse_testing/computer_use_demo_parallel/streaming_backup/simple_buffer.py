"""
Simple buffer implementation for handling tool calls during streaming.

This module provides a minimal implementation of the buffer pattern
to prevent partial tool calls from being executed prematurely.
"""

import json
import logging
import re
from typing import Dict, Optional, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_buffer")

class SimpleToolBuffer:
    """
    Simple buffer for accumulating partial JSON for tool calls during streaming.
    
    This class implements the buffer pattern described in BUFFER_PATTERN_IMPLEMENTATION.md,
    ensuring that tool calls are only executed when they are complete.
    """
    
    def __init__(self):
        """Initialize the buffer."""
        self.json_buffers = {}  # Dict mapping index to buffer content
        self.tool_use_ids = {}  # Dict mapping index to tool_use_id
        self.tool_names = {}    # Dict mapping index to tool_name
        self.attempt_count = 0  # Count of tool use attempts
        self.max_attempts = 3   # Maximum number of attempts before breaking out
    
    def process_content_block_delta(self, index: int, delta_content: str, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a content_block_delta event during streaming.
        
        Args:
            index: The index of the content block
            delta_content: The partial JSON content
            tool_id: Optional tool_use_id from the delta
            
        Returns:
            Dict with information about the partial content
        """
        # Initialize buffer if needed
        if index not in self.json_buffers:
            self.json_buffers[index] = ''
        
        # Accumulate the partial JSON
        buffer = self.json_buffers[index] + delta_content
        self.json_buffers[index] = buffer
        
        # Track tool_use_id if present
        if tool_id:
            self.tool_use_ids[index] = tool_id
        
        # Return information about the partial tool call
        return {
            'type': 'partial_tool_call',
            'buffer': buffer,
            'tool_name': self.tool_names.get(index),
            'tool_use_id': self.tool_use_ids.get(index),
            'is_complete': False,
            'index': index
        }

    def process_delta(self, index: int, delta_content: str, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Alias for process_content_block_delta to maintain compatibility.
        
        Args:
            index: The index of the content block
            delta_content: The partial JSON content
            tool_id: Optional tool_use_id from the delta
            
        Returns:
            Dict with information about the partial content
        """
        return self.process_content_block_delta(index, delta_content, tool_id)
        
    def process_content_block_stop(self, index: int) -> Dict[str, Any]:
        """
        Process a content_block_stop event during streaming.
        
        Args:
            index: The index of the content block
            
        Returns:
            Dict with information about the complete content
        """
        if index not in self.json_buffers:
            return None
            
        buffer = self.json_buffers[index]
        
        # Try to parse the complete JSON
        try:
            tool_params = json.loads(buffer)
            
            # Clear buffers
            self.json_buffers.pop(index, None)
            
            # Increment attempt count
            self.attempt_count += 1
            
            # Detect XML function calls (based on string content analysis)
            if isinstance(buffer, str) and '<function_calls>' in buffer and '</function_calls>' in buffer:
                return {
                    'type': 'complete_xml',  # Use complete_xml for XML calls
                    'tool_name': self.tool_names.get(index),
                    'tool_params': tool_params,
                    'tool_use_id': self.tool_use_ids.get(index),
                    'is_complete': True,
                    'index': index
                }
            else:
                # Return JSON tool call
                return {
                    'type': 'complete_json',  # Use complete_json for JSON calls
                    'tool_name': tool_params.get("tool") or tool_params.get("name"),
                    'tool_params': tool_params.get("parameters") or tool_params.get("params") or tool_params,
                    'tool_use_id': self.tool_use_ids.get(index),
                    'is_complete': True,
                    'index': index
                }
        except json.JSONDecodeError as e:
            # Check if this might be XML instead of JSON
            if isinstance(buffer, str) and ('<' in buffer and '>' in buffer):
                # This looks like it might be XML
                if '<function_calls>' in buffer and '</function_calls>' in buffer:
                    # This is complete XML but failed to parse as JSON
                    # Try to extract tool name and params via regex
                    tool_name_match = re.search(r'<invoke name="([^"]+)"', buffer)
                    
                    if tool_name_match:
                        tool_name = tool_name_match.group(1)
                        
                        # Extract parameters using simple regex
                        params = {}
                        param_matches = re.finditer(r'<parameter name="([^"]+)">([^<]+)</parameter>', buffer)
                        
                        for match in param_matches:
                            param_name = match.group(1)
                            param_value = match.group(2)
                            params[param_name] = param_value
                        
                        # Clear buffers
                        self.json_buffers.pop(index, None)
                        
                        # Increment attempt count
                        self.attempt_count += 1
                        
                        return {
                            'type': 'complete_xml',
                            'tool_name': tool_name,
                            'tool_params': params,
                            'tool_use_id': self.tool_use_ids.get(index),
                            'is_complete': True,
                            'index': index
                        }
                else:
                    # Incomplete XML - keep buffer for now
                    return {
                        'type': 'partial_tool_call',
                        'buffer': buffer,
                        'error': 'Incomplete XML',
                        'is_complete': False,
                        'index': index
                    }
            
            # Return error for invalid JSON
            return {
                'type': 'tool_call_error',
                'error': str(e),
                'buffer': buffer,
                'is_complete': False,
                'index': index
            }
    
    def process_stop(self, index: int) -> Dict[str, Any]:
        """
        Alias for process_content_block_stop to maintain compatibility.
        
        Args:
            index: The index of the content block
            
        Returns:
            Dict with information about the complete content
        """
        return self.process_content_block_stop(index)
            
    def should_break_execution(self) -> bool:
        """Check if we should break execution to prevent infinite loops."""
        return self.attempt_count >= self.max_attempts
        
    def should_break(self) -> bool:
        """Alias for should_break_execution to maintain compatibility."""
        return self.should_break_execution()
        
    def reset_attempts(self):
        """Reset the attempt counter."""
        self.attempt_count = 0
        
    def validate_tool_parameters(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate tool parameters to ensure they are complete before execution.
        
        Args:
            tool_name: The name of the tool to validate
            params: The parameters to validate
            
        Returns:
            Tuple of (is_valid, message, fixed_params)
        """
        fixed_params = params.copy() if params else {}
        
        if tool_name == "dc_bash":
            # Validate command parameter
            if "command" not in fixed_params or not fixed_params["command"]:
                # Try to recover from alternative fields
                for alt_name in ["cmd", "bash", "terminal", "shell"]:
                    if alt_name in fixed_params and fixed_params[alt_name]:
                        fixed_params["command"] = fixed_params[alt_name]
                        logger.info(f"Recovered command from {alt_name} parameter")
                        break
                
                # If still missing, it's invalid
                if "command" not in fixed_params or not fixed_params["command"]:
                    return False, "Missing required 'command' parameter", fixed_params
        
        elif tool_name == "dc_computer":
            # Validate action parameter
            if "action" not in fixed_params or not fixed_params["action"]:
                # Try to recover from alternative fields
                for alt_name in ["operation", "command", "type"]:
                    if alt_name in fixed_params and fixed_params[alt_name]:
                        fixed_params["action"] = fixed_params[alt_name]
                        logger.info(f"Recovered action from {alt_name} parameter")
                        break
                
                # If still missing, it's invalid
                if "action" not in fixed_params or not fixed_params["action"]:
                    return False, "Missing required 'action' parameter", fixed_params
        
        # Add more tool validation as needed
        
        return True, "Parameters validated successfully", fixed_params