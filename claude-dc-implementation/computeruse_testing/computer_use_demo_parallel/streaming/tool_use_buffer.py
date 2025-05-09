"""
Minimal tool use buffer for handling Claude DC function calls during streaming.

This is a focused, standalone implementation designed to solve the race condition 
where partial function calls are processed prematurely during streaming.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("tool_use_buffer")

class ToolUseBuffer:
    """
    Minimal buffer for handling partial function calls during streaming.
    """
    
    def __init__(self):
        """Initialize a new tool use buffer."""
        self.json_buffers = {}  # Maps indices to accumulated JSON/XML
        self.tool_ids = {}      # Maps indices to tool use IDs
        self.attempt_count = 0  # For safety against infinite loops
        self.max_attempts = 3   # Maximum number of attempts before breaking
    
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
        
        # Log buffer update
        logger.debug(f"Buffer {index} updated: {self.json_buffers[index][:50]}...")
        
        return True  # Content was buffered
    
    def handle_content_block_stop(self, index: int) -> Optional[Dict[str, Any]]:
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
            return None
    
    def _process_xml_call(self, buffer: str, index: int, tool_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Process an XML function call."""
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