"""
Buffer Pattern Implementation for Claude DC Function Calls.

This module implements a buffer pattern to solve the race condition where
partial function calls are processed before they are complete during streaming.
This prevents errors caused by processing incomplete function calls.
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any, Tuple, List, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("buffer_pattern")

class ToolCallBuffer:
    """
    Buffer for accumulating partial JSON/XML for tool calls during streaming.
    
    This implements the buffer pattern to prevent the race condition where
    partial function calls are processed prematurely during streaming.
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
            delta: The delta object containing partial JSON
            
        Returns:
            Dict with information about the partial content or None if not a tool call
        """
        # Check if this is a tool call delta
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
        
        # Log buffer status for debugging
        logger.debug(f"Buffer for index {index} now: {buffer[:100]}...")
        
        # Return information about the partial tool call
        return {
            "type": "partial_tool_call",
            "buffer": buffer,
            "tool_name": self.tool_names.get(index),
            "tool_use_id": self.tool_use_ids.get(index),
            "is_complete": False,
            "index": index
        }
        
    def extract_xml_function_call(self, xml_str: str) -> Dict[str, Any]:
        """
        Extract function call information from XML string.
        
        Args:
            xml_str: The XML string to parse
            
        Returns:
            Dict with tool name and parameters if valid, or error information
        """
        # Detailed result with success/failure information
        result = {
            'success': False,
            'error': None,
            'function_name': None,
            'parameters': {}
        }
        
        # First, check for basic XML format
        if not ('<function_calls>' in xml_str and '</function_calls>' in xml_str):
            result['error'] = "XML must have both opening <function_calls> and closing </function_calls> tags"
            result['format'] = "xml_incomplete"
            return result
            
        try:
            # Parse XML
            root = ET.fromstring(xml_str)
            
            # Check structure
            if root.tag != 'function_calls':
                result['error'] = "Root tag must be <function_calls>"
                result['format'] = "xml_invalid"
                return result
                
            # Find invoke tag
            invoke = root.find('./invoke')
            if invoke is None:
                result['error'] = "Missing <invoke> tag inside <function_calls>"
                result['format'] = "xml_invalid"
                return result
                
            # Get function name
            function_name = invoke.get('name')
            if not function_name:
                result['error'] = "Missing 'name' attribute in <invoke> tag"
                result['format'] = "xml_invalid"
                return result
            
            result['function_name'] = function_name
                
            # Get parameters
            parameters = {}
            param_elements = invoke.findall('./parameter')
            
            if not param_elements:
                # This might be valid if the function takes no parameters
                logger.info(f"No <parameter> tags found for {function_name}, but this might be valid")
                
            for param in param_elements:
                name = param.get('name')
                if not name:
                    result['error'] = "Missing 'name' attribute in <parameter> tag"
                    result['format'] = "xml_invalid"
                    return result
                    
                parameters[name] = param.text or ""
            
            # Set success result
            result['success'] = True
            result['parameters'] = parameters
            return result
            
        except ET.ParseError as e:
            # Get line and column information if available
            match = re.search(r'line (\d+), column (\d+)', str(e))
            if match:
                line, column = match.groups()
                lines = xml_str.split('\n')
                problem_line = lines[int(line)-1] if int(line)-1 < len(lines) else ""
                pointer = ' ' * (int(column)-1) + '^'
                detail = f"\nError at line {line}, column {column}:\n{problem_line}\n{pointer}"
                result['error'] = f"XML parse error: {str(e)}{detail}"
            else:
                result['error'] = f"XML parse error: {str(e)}"
            
            result['format'] = "xml_malformed"
            return result
        except Exception as e:
            logger.warning(f"XML parsing error: {str(e)}")
            result['error'] = f"XML processing error: {str(e)}"
            result['format'] = "xml_error"
            return result
    
    def process_content_block_stop(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Process a content_block_stop event during streaming.
        
        Args:
            index: The index of the content block
            
        Returns:
            Dict with information about the complete content or None if no buffer
        """
        # Check if we have a buffer for this index
        if index not in self.json_buffers:
            return None
            
        buffer = self.json_buffers[index]
        
        # First check for XML-style function calls
        if '<function_calls>' in buffer and '</function_calls>' in buffer:
            # We have something that looks like complete XML
            xml_result = self.extract_xml_function_call(buffer)
            
            if xml_result['success']:
                # We have a valid XML function call
                function_name = xml_result['function_name']
                parameters = xml_result['parameters']
                
                # Strip dc_ prefix if present for compatibility
                if function_name.startswith("dc_"):
                    tool_name = function_name
                else:
                    # For other functions, check if we need to add prefix
                    tool_name = function_name
                    for prefix in ["dc_"]:
                        if any(tool_name == t.replace(prefix, "") for t in ["dc_bash", "dc_computer", "dc_str_replace_editor"]):
                            tool_name = f"{prefix}{tool_name}"
                            break
                
                # Clear buffers
                self.json_buffers.pop(index, None)
                
                # Increment attempt count
                self.attempt_count += 1
                
                # Log success
                logger.info(f"Successfully parsed XML function call: {tool_name}")
                
                # Return the XML function call
                return {
                    "type": "complete_tool_call",
                    "format": "xml",
                    "index": index,
                    "tool_name": tool_name,
                    "tool_params": parameters,
                    "tool_use_id": self.tool_use_ids.get(index),
                    "is_complete": True
                }
            else:
                # XML parsing failed with specific error
                logger.warning(f"XML parsing failed: {xml_result['error']}")
                
                # Clear buffers for complete but invalid XML
                self.json_buffers.pop(index, None)
                
                # Return detailed error
                return {
                    "type": "tool_call_error",
                    "error": xml_result['error'],
                    "buffer": buffer,
                    "format": xml_result.get('format', 'xml_invalid'),
                    "tool_use_id": self.tool_use_ids.get(index),
                    "is_complete": False,
                    "index": index
                }
        
        # Try to parse as JSON (as fallback for non-XML tool calls)
        try:
            tool_params = json.loads(buffer)
            
            # Identify tool name from JSON structure
            if "tool" in tool_params:
                tool_name = tool_params["tool"]
            elif "name" in tool_params:
                tool_name = tool_params["name"]
            else:
                # Default to dc_bash if no tool name found
                tool_name = "dc_bash"
                
            # Extract parameters to clean structure
            if "parameters" in tool_params:
                parameters = tool_params["parameters"]
            elif "params" in tool_params:
                parameters = tool_params["params"]
            else:
                # Use the whole object as parameters
                parameters = tool_params
            
            # Clear buffers
            self.json_buffers.pop(index, None)
                
            # Increment attempt count
            self.attempt_count += 1
            
            # Log success
            logger.info(f"Successfully parsed JSON function call: {tool_name}")
            
            # Return the parsed content
            return {
                "type": "complete_tool_call",
                "format": "json",
                "index": index,
                "tool_name": tool_name,
                "tool_params": parameters,
                "tool_use_id": self.tool_use_ids.get(index),
                "is_complete": True
            }
        except json.JSONDecodeError as e:
            # Log error details
            logger.warning(f"JSON parsing error: {str(e)}")
            
            # Return error information
            return {
                "type": "tool_call_error",
                "error": f"Invalid JSON: {str(e)}",
                "buffer": buffer,
                "format": "json_invalid",
                "tool_use_id": self.tool_use_ids.get(index),
                "is_complete": False,
                "index": index
            }
    
    def should_break_execution(self) -> bool:
        """Check if we should break execution to prevent infinite loops."""
        return self.attempt_count >= self.max_attempts
        
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
                    
        elif tool_name == "dc_str_replace_editor":
            # Validate command and path parameters
            if "command" not in fixed_params or not fixed_params["command"]:
                return False, "Missing required 'command' parameter", fixed_params
                
            if "path" not in fixed_params or not fixed_params["path"]:
                return False, "Missing required 'path' parameter", fixed_params
        
        # Add more tool validation as needed
        
        return True, "Parameters validated successfully", fixed_params