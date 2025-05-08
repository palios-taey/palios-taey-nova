"""
Simple, standalone buffer implementation for Claude DC's streaming function calls.

This module provides a minimal implementation of the buffer pattern to solve
the race condition where partial function calls are processed before they're complete.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_buffer")

class FunctionCallBuffer:
    """
    Minimal buffer for accumulating partial JSON/XML during streaming.
    
    This is a standalone implementation that doesn't rely on any external modules.
    """
    
    def __init__(self):
        """Initialize the buffer."""
        self.buffers = {}  # Dict mapping index to content
        self.tool_ids = {}  # Dict mapping index to tool_use_id
        self.count = 0  # Safety count to prevent infinite loops
    
    def accumulate(self, index: int, content: str, tool_id: Optional[str] = None) -> bool:
        """
        Accumulate partial content for a function call.
        
        Args:
            index: Content block index
            content: Partial content (JSON or XML)
            tool_id: Optional tool_use_id
            
        Returns:
            True if content was accumulated (is partial), False otherwise
        """
        # Initialize buffer if needed
        if index not in self.buffers:
            self.buffers[index] = ""
        
        # Track tool_id if provided
        if tool_id:
            self.tool_ids[index] = tool_id
        
        # Accumulate content
        self.buffers[index] += content
        
        # Log buffer update
        logger.debug(f"Buffer {index} updated: {self.buffers[index][:50]}...")
        
        return True
    
    def is_complete(self, index: int) -> bool:
        """
        Check if the content in the buffer is complete.
        
        Args:
            index: Content block index
            
        Returns:
            True if the content is complete, False otherwise
        """
        if index not in self.buffers:
            return False
        
        buffer = self.buffers[index]
        
        # Check for complete XML
        if '<function_calls>' in buffer and '</function_calls>' in buffer:
            return True
        
        # Check for valid JSON
        try:
            json.loads(buffer)
            return True
        except json.JSONDecodeError:
            return False
    
    def get_complete_content(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get the complete content from the buffer if it's complete.
        
        Args:
            index: Content block index
            
        Returns:
            Dict with tool_name, tool_params, and tool_id if complete, None otherwise
        """
        if not self.is_complete(index):
            return None
        
        buffer = self.buffers[index]
        tool_id = self.tool_ids.get(index)
        
        # Check for XML function call
        if '<function_calls>' in buffer and '</function_calls>' in buffer:
            # Extract function name
            name_match = re.search(r'<invoke name="([^"]+)"', buffer)
            if not name_match:
                logger.warning(f"Invalid XML: Missing function name")
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
            self.buffers.pop(index, None)
            if index in self.tool_ids:
                self.tool_ids.pop(index)
            
            # Normalize tool name (add dc_ prefix if needed)
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
        
        # Process JSON
        try:
            data = json.loads(buffer)
            
            # Extract tool name
            tool_name = None
            if "tool" in data:
                tool_name = data["tool"]
            elif "name" in data:
                tool_name = data["name"]
            else:
                # Default to dc_bash if no name found
                tool_name = "dc_bash"
            
            # Extract parameters
            if "parameters" in data:
                params = data["parameters"]
            elif "params" in data:
                params = data["params"]
            else:
                params = data
            
            # Clear buffer
            self.buffers.pop(index, None)
            if index in self.tool_ids:
                self.tool_ids.pop(index)
            
            return {
                "tool_name": tool_name,
                "tool_params": params,
                "tool_id": tool_id,
                "format": "json"
            }
        except json.JSONDecodeError:
            return None
    
    def validate_parameters(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate tool parameters and attempt to recover from common issues.
        
        Args:
            tool_name: The name of the tool
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
                    
        elif tool_name == "dc_str_replace_editor":
            # Validate command and path parameters
            if "command" not in fixed_params or not fixed_params["command"]:
                return False, "Missing required 'command' parameter", fixed_params
                
            if "path" not in fixed_params or not fixed_params["path"]:
                return False, "Missing required 'path' parameter", fixed_params
        
        # Parameter validation passed
        return True, "Parameters validated successfully", fixed_params