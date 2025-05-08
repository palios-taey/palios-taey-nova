"""
Tool call buffer for handling streaming function calls.

This module implements the buffer pattern described in BUFFER_PATTERN_IMPLEMENTATION.md,
which prevents the race condition where partial function calls are processed prematurely during streaming.
"""

import json
import logging
import re
from typing import Dict, Optional, Any, List, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tool_buffer")

class ToolCallBuffer:
    """
    Buffer for accumulating partial JSON for tool calls during streaming.
    
    This implementation follows the exact pattern described in BUFFER_PATTERN_IMPLEMENTATION.md.
    """
    
    def __init__(self):
        """Initialize the buffer."""
        self.json_buffers = {}  # Dict mapping index to buffer content
        self.tool_use_ids = {}  # Dict mapping index to tool_use_id
        self.tool_names = {}    # Dict mapping index to tool_name
        self.attempt_count = 0  # Count of tool use attempts
        self.max_attempts = 3   # Maximum number of attempts before breaking out
    
    def process_content_block_delta(self, index: int, delta: Any) -> Optional[Dict[str, Any]]:
        """
        Process a content_block_delta event during streaming.
        
        Args:
            index: The index of the content block
            delta: The delta object from the event
            
        Returns:
            Dict with information about the partial content, or None if not a tool call
        """
        if not hasattr(delta, 'type') or delta.type != 'input_json_delta':
            return None
            
        # Initialize buffer if needed
        if index not in self.json_buffers:
            self.json_buffers[index] = ''
        
        # Accumulate the partial JSON
        partial_json = getattr(delta, 'partial_json', '')
        buffer = self.json_buffers[index] + partial_json
        self.json_buffers[index] = buffer
        
        # Track tool_use_id if present
        if hasattr(delta, 'tool_use_id') and delta.tool_use_id:
            self.tool_use_ids[index] = delta.tool_use_id
        
        # Return information about the partial tool call
        return {
            'type': 'partial_tool_call',
            'buffer': buffer,
            'tool_name': self.tool_names.get(index),
            'tool_use_id': self.tool_use_ids.get(index),
            'is_complete': False,
            'index': index
        }
    
    def process_content_block_stop(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Process a content_block_stop event during streaming.
        
        Args:
            index: The index of the content block
            
        Returns:
            Dict with information about the complete content, or None if not a tool call
        """
        if index not in self.json_buffers:
            return None
            
        buffer = self.json_buffers[index]
        
        # Try to parse the complete JSON
        try:
            tool_params = json.loads(buffer)
            
            # Detect XML-style function calls
            if isinstance(buffer, str) and '<function_calls>' in buffer and '</function_calls>' in buffer:
                # XML handling for function calls
                tool_name = self._extract_xml_tool_name(buffer)
                parameters = self._extract_xml_parameters(buffer)
                
                # Clear buffers
                self.json_buffers.pop(index, None)
                
                # Increment attempt count
                self.attempt_count += 1
                
                # Return with specific type for XML
                return {
                    'type': 'complete_xml',
                    'tool_params': parameters,
                    'tool_name': tool_name,
                    'tool_use_id': self.tool_use_ids.get(index),
                    'is_complete': True,
                    'index': index
                }
            
            # Clear buffers
            self.json_buffers.pop(index, None)
            
            # Increment attempt count
            self.attempt_count += 1
            
            # Return complete tool call information with specific type for JSON
            return {
                'type': 'complete_json',
                'tool_params': tool_params,
                'tool_name': self._extract_tool_name(tool_params),
                'tool_use_id': self.tool_use_ids.get(index),
                'is_complete': True,
                'index': index
            }
            
        except json.JSONDecodeError as e:
            # Check if it's actually XML
            if '<function_calls>' in buffer:
                if '</function_calls>' in buffer:
                    # It's complete XML but JSON parsing failed
                    try:
                        tool_name = self._extract_xml_tool_name(buffer)
                        parameters = self._extract_xml_parameters(buffer)
                        
                        # Clear buffers
                        self.json_buffers.pop(index, None)
                        
                        # Increment attempt count
                        self.attempt_count += 1
                        
                        # Return XML data
                        return {
                            'type': 'complete_xml',
                            'tool_params': parameters,
                            'tool_name': tool_name,
                            'tool_use_id': self.tool_use_ids.get(index),
                            'is_complete': True,
                            'index': index
                        }
                    except Exception as xml_error:
                        # XML parsing failed
                        return {
                            'type': 'tool_call_error',
                            'error': f"XML parsing error: {str(xml_error)}",
                            'buffer': buffer,
                            'is_complete': False,
                            'index': index
                        }
                else:
                    # Incomplete XML
                    return {
                        'type': 'partial_xml',
                        'buffer': buffer,
                        'tool_name': None,
                        'tool_use_id': self.tool_use_ids.get(index),
                        'is_complete': False,
                        'index': index
                    }
            
            # JSON parsing error
            return {
                'type': 'tool_call_error',
                'error': str(e),
                'buffer': buffer,
                'is_complete': False,
                'index': index
            }
    
    def should_break_execution(self) -> bool:
        """Check if we should break execution to prevent infinite loops."""
        return self.attempt_count >= self.max_attempts
    
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
        
        # Handle nested parameters structure (common in JSON)
        if "parameters" in fixed_params and isinstance(fixed_params["parameters"], dict):
            # Merge parameters into top level for easier processing
            for key, value in fixed_params["parameters"].items():
                if key not in fixed_params:
                    fixed_params[key] = value
        
        if tool_name == "dc_bash":
            # Validate command parameter
            if "command" not in fixed_params or not fixed_params["command"]:
                # Try to recover from alternative fields
                for alt_name in ["cmd", "bash", "terminal", "shell"]:
                    if alt_name in fixed_params and fixed_params[alt_name]:
                        fixed_params["command"] = fixed_params[alt_name]
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
                        break
                
                # If still missing, it's invalid
                if "action" not in fixed_params or not fixed_params["action"]:
                    return False, "Missing required 'action' parameter", fixed_params
        
        # Add more tool validation as needed
        
        return True, "Parameters validated successfully", fixed_params
    
    def _extract_tool_name(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Extract tool name from parameters dict.
        
        Args:
            params: The parameters dict
            
        Returns:
            Tool name if found, None otherwise
        """
        # Check standard fields
        if "tool" in params:
            return params["tool"]
        if "name" in params:
            return params["name"]
        
        # Try to infer from content
        content_str = str(params)
        for tool in ["dc_bash", "dc_computer", "dc_str_replace_editor"]:
            if tool in content_str:
                return tool
        
        # Default
        return None
    
    def _extract_xml_tool_name(self, xml_str: str) -> Optional[str]:
        """
        Extract tool name from XML string.
        
        Args:
            xml_str: The XML string
            
        Returns:
            Tool name if found, None otherwise
        """
        match = re.search(r'<invoke name="([^"]+)"', xml_str)
        if match:
            return match.group(1)
        return None
    
    def _extract_xml_parameters(self, xml_str: str) -> Dict[str, str]:
        """
        Extract parameters from XML string.
        
        Args:
            xml_str: The XML string
            
        Returns:
            Dict of parameter name to value
        """
        params = {}
        param_matches = re.finditer(r'<parameter name="([^"]+)">([^<]+)</parameter>', xml_str)
        for match in param_matches:
            param_name = match.group(1)
            param_value = match.group(2)
            params[param_name] = param_value
        return params