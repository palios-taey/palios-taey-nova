"""
Tool Call Buffer for Claude DC.

This module implements a buffer pattern for accumulating partial tool call data
during streaming to prevent premature execution of incomplete function calls.
It now supports both JSON and XML formats for tool calls.
"""

import json
import logging
import re
from typing import Dict, Optional, Any, Tuple, List

# Set up logging
logger = logging.getLogger("tool_call_buffer")
logger.setLevel(logging.INFO)

# Integrated XML validator functions
import re
import xml.etree.ElementTree as ET
from typing import Tuple, Dict, Any, Optional

# Flag to indicate if XML validation is available (always True with integrated validator)
XML_VALIDATOR_AVAILABLE = True

def validate_xml_structure(xml_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validate the XML structure of a tool call.
    
    Args:
        xml_str: The XML string to validate
        
    Returns:
        Tuple of (is_valid, message, extracted_data)
        - is_valid: Whether the XML is valid
        - message: Validation message or error details
        - extracted_data: Extracted tool data if valid, None otherwise
    """
    try:
        # Check if XML is complete (has opening and closing tags)
        if not xml_str.strip().startswith('<function_calls>'):
            return False, "Missing opening <function_calls> tag", None
            
        if not xml_str.strip().endswith('</function_calls>'):
            return False, "Missing closing </function_calls> tag", None
        
        # Parse XML
        root = ET.fromstring(xml_str)
        
        # Check structure
        if root.tag != 'function_calls':
            return False, f"Root tag should be 'function_calls', found '{root.tag}'", None
            
        # Find invoke tag
        invoke_elements = root.findall('./invoke')
        if not invoke_elements:
            return False, "Missing <invoke> tag", None
        
        if len(invoke_elements) > 1:
            return False, "Multiple <invoke> tags found, only one is allowed", None
            
        invoke = invoke_elements[0]
        
        # Get tool name
        tool_name = invoke.get('name')
        if not tool_name:
            return False, "Missing 'name' attribute in <invoke> tag", None
            
        # Check parameters
        parameters = {}
        param_elements = invoke.findall('./parameter')
        
        if not param_elements:
            return False, f"Missing <parameter> tags for tool '{tool_name}'", None
            
        for param in param_elements:
            param_name = param.get('name')
            if not param_name:
                return False, "Missing 'name' attribute in <parameter> tag", None
                
            param_value = param.text
            parameters[param_name] = param_value
            
        # Successfully validated
        extracted_data = {
            'tool_name': tool_name,
            'parameters': parameters
        }
        
        return True, "XML structure is valid", extracted_data
        
    except ET.ParseError as e:
        # XML parsing error - provide detailed feedback
        line_col = re.search(r'line (\d+), column (\d+)', str(e))
        if line_col:
            line, col = line_col.groups()
            # Split XML into lines
            lines = xml_str.split('\n')
            # Get the problematic line
            problem_line = lines[int(line)-1] if int(line) <= len(lines) else ""
            # Highlight the error position
            pointer = ' ' * (int(col)-1) + '^'
            
            error_details = f"XML parsing error at line {line}, column {col}:\n{problem_line}\n{pointer}"
            return False, error_details, None
        else:
            return False, f"XML parsing error: {str(e)}", None
            
    except Exception as e:
        return False, f"Validation error: {str(e)}", None

def extract_tool_call_data(buffer: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Extract tool call data from a buffer string.
    
    Args:
        buffer: The buffer string that may contain an XML tool call
        
    Returns:
        Tuple of (success, message, data)
        - success: Whether extraction was successful
        - message: Success/error message
        - data: Extracted tool data if successful, None otherwise
    """
    # Look for XML tool call pattern
    xml_pattern = r'<function_calls>.*?</function_calls>'
    match = re.search(xml_pattern, buffer, re.DOTALL)
    
    if not match:
        return False, "No complete XML tool call found in buffer", None
        
    xml_str = match.group(0)
    
    # Validate the XML structure
    is_valid, message, extracted_data = validate_xml_structure(xml_str)
    
    if not is_valid:
        return False, message, None
        
    return True, "Successfully extracted tool call data", extracted_data

def generate_correction_suggestion(xml_str: str) -> str:
    """
    Generate a suggestion to correct invalid XML.
    
    Args:
        xml_str: The invalid XML string
        
    Returns:
        A suggestion for correction
    """
    suggestions = []
    
    # Check for common issues
    if '<function_calls>' not in xml_str:
        suggestions.append("- Add opening <function_calls> tag")
    
    if '</function_calls>' not in xml_str:
        suggestions.append("- Add closing </function_calls> tag")
    
    if '<invoke' in xml_str and '</invoke>' not in xml_str:
        suggestions.append("- Add closing </invoke> tag")
    
    if 'name=' not in xml_str and '<invoke' in xml_str:
        suggestions.append("- Add 'name' attribute to <invoke> tag")
    
    if '<parameter' in xml_str and '</parameter>' not in xml_str:
        suggestions.append("- Add closing </parameter> tag")
    
    if '<parameter' in xml_str and 'name=' not in xml_str:
        suggestions.append("- Add 'name' attribute to <parameter> tag")
    
    # Create structured suggestion
    if suggestions:
        suggestion = "Suggested corrections:\n" + "\n".join(suggestions)
        
        # Add correct example
        suggestion += "\n\nCorrect format example:\n"
        suggestion += """<function_calls>
<invoke name="dc_bash">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>"""
        
        return suggestion
    else:
        return "Could not determine specific issues. Please ensure you follow the exact format specified in the system prompt."

# Log that we're using integrated XML validator
logger.info("Using integrated XML validator functions")

class ToolCallBuffer:
    """
    Buffer for accumulating partial tool call JSON data during streaming.
    
    This prevents the "race condition" where partial function calls are processed
    prematurely during streaming, leading to errors.
    """
    
    def __init__(self):
        """Initialize the ToolCallBuffer."""
        self.json_buffers = {}  # Track JSON buffers for each content block
        self.tool_use_ids = {}  # Track tool_use_id for each content block
        self.tool_names = {}    # Track tool_name for each content block
        self.attempt_count = 0  # Count of tool use attempts for safety checks
        self.max_attempts = 3   # Maximum number of attempts before breaking out
    
    def process_content_block_delta(self, index: int, delta: Any) -> Optional[Dict[str, Any]]:
        """
        Process a content_block_delta event during streaming.
        
        Args:
            index: The index of the content block
            delta: The delta data from the streaming event
            
        Returns:
            Optional dict with information about the partial tool call
        """
        # Check if this is a JSON delta for tool use
        if not hasattr(delta, 'type') or delta.type != 'input_json_delta':
            return None
            
        # Initialize buffer if needed
        if index not in self.json_buffers:
            self.json_buffers[index] = ''
            logger.debug(f"Initialized JSON buffer for content block {index}")
        
        # Get the partial JSON and accumulate it
        partial_json = getattr(delta, 'partial_json', '')
        if not partial_json:
            return None
            
        # Update buffer
        buffer = self.json_buffers[index] + partial_json
        self.json_buffers[index] = buffer
        
        # Track tool_use_id if present
        if hasattr(delta, 'tool_use_id') and delta.tool_use_id:
            self.tool_use_ids[index] = delta.tool_use_id
            logger.debug(f"Tracked tool_use_id '{delta.tool_use_id}' for content block {index}")
        
        # Track tool_name if we can extract it
        if not index in self.tool_names:
            # Try to extract tool name from the buffer
            name_match = re.search(r'"name":\s*"([^"]+)"', buffer)
            if name_match:
                self.tool_names[index] = name_match.group(1)
                logger.debug(f"Extracted tool name '{self.tool_names[index]}' for content block {index}")
        
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
            Optional dict with information about the complete tool call
        """
        # Check if we have a buffer for this index
        if index not in self.json_buffers:
            return None
            
        buffer = self.json_buffers[index]
        tool_use_id = self.tool_use_ids.get(index)
        tool_name = self.tool_names.get(index)
        
        # First check for XML-style tool call (preferred format)
        if XML_VALIDATOR_AVAILABLE and '<function_calls>' in buffer:
            logger.info(f"Detected potential XML-style tool call in buffer at index {index}")
            
            # Try to extract tool call data from XML
            is_valid, message, extracted_data = extract_tool_call_data(buffer)
            
            if is_valid and extracted_data:
                # Clear buffers
                self.json_buffers.pop(index, None)
                self.tool_use_ids.pop(index, None)
                self.tool_names.pop(index, None)
                
                # Increment attempt count for safety
                self.attempt_count += 1
                
                # Extract tool information
                xml_tool_name = extracted_data.get('tool_name')
                xml_parameters = extracted_data.get('parameters', {})
                
                logger.info(f"Successfully extracted XML tool call: {xml_tool_name} with {len(xml_parameters)} parameters")
                
                # Return complete tool call information from XML
                return {
                    'type': 'complete_tool_call',
                    'tool_params': xml_parameters,
                    'tool_name': xml_tool_name,
                    'tool_use_id': tool_use_id,
                    'is_complete': True,
                    'index': index,
                    'format': 'xml'
                }
            else:
                # XML validation failed but there was an attempt
                if '<function_calls>' in buffer and '</function_calls>' in buffer:
                    # Generate correction suggestion
                    suggestion = generate_correction_suggestion(buffer) if XML_VALIDATOR_AVAILABLE else "XML format appears invalid"
                    
                    logger.warning(f"XML validation failed: {message}")
                    return {
                        'type': 'tool_call_error',
                        'error': f"XML validation error: {message}",
                        'suggestion': suggestion,
                        'buffer': buffer,
                        'tool_name': tool_name,
                        'tool_use_id': tool_use_id,
                        'is_complete': False,
                        'index': index,
                        'format': 'xml_invalid'
                    }
        
        # Fallback to JSON parsing (original behavior)
        try:
            tool_params = json.loads(buffer)
            
            # Clear buffers
            self.json_buffers.pop(index, None)
            self.tool_use_ids.pop(index, None)
            self.tool_names.pop(index, None)
            
            # Increment attempt count for safety
            self.attempt_count += 1
            
            logger.info(f"Successfully parsed JSON tool call at index {index}")
            
            # Return complete tool call information
            return {
                'type': 'complete_tool_call',
                'tool_params': tool_params,
                'tool_name': tool_name,
                'tool_use_id': tool_use_id,
                'is_complete': True,
                'index': index,
                'format': 'json'
            }
        except json.JSONDecodeError as e:
            # Check if it's an incomplete XML tool call
            if '<function_calls>' in buffer and '</function_calls>' not in buffer:
                logger.warning(f"Incomplete XML tool call detected in buffer at index {index}")
                return {
                    'type': 'tool_call_error',
                    'error': "Incomplete XML tool call (missing closing tags)",
                    'buffer': buffer,
                    'tool_name': tool_name,
                    'tool_use_id': tool_use_id,
                    'is_complete': False,
                    'index': index,
                    'format': 'xml_incomplete'
                }
            else:
                logger.warning(f"JSON parsing error for buffer at index {index}: {e}")
                return {
                    'type': 'tool_call_error',
                    'error': f"JSON parsing error: {str(e)}",
                    'buffer': buffer,
                    'tool_name': tool_name,
                    'tool_use_id': tool_use_id,
                    'is_complete': False,
                    'index': index,
                    'format': 'unknown'
                }
    
    def validate_tool_parameters(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate tool parameters to ensure they are complete before execution.
        
        Args:
            tool_name: The name of the tool
            params: The tool parameters
            
        Returns:
            Tuple of (is_valid, message, fixed_params)
            - is_valid: Whether the parameters are valid
            - message: Validation message
            - fixed_params: Parameters with defaults applied where possible
        """
        # Make a copy to avoid modifying the original
        fixed_params = params.copy() if params else {}
        
        # Specific validation for different tools
        if tool_name == "dc_bash":
            # Validate command parameter
            if "command" not in fixed_params or not fixed_params["command"]:
                # Try to recover by looking for similar parameter names
                for alt_name in ["cmd", "bash", "terminal", "shell", "script", "exec"]:
                    if alt_name in fixed_params and fixed_params[alt_name]:
                        fixed_params["command"] = fixed_params[alt_name]
                        logger.info(f"Recovered command from alternative field '{alt_name}'")
                        break
                
                # If still missing, it's invalid
                if "command" not in fixed_params or not fixed_params["command"]:
                    return False, "Missing required 'command' parameter", fixed_params
            
            # Check command type
            if not isinstance(fixed_params["command"], str):
                return False, f"Command must be a string, got {type(fixed_params['command']).__name__}", fixed_params
                
            # Check if command is empty
            if not fixed_params["command"].strip():
                return False, "Command cannot be empty", fixed_params
        
        elif tool_name == "dc_computer":
            # Validate action parameter
            if "action" not in fixed_params or not fixed_params["action"]:
                return False, "Missing required 'action' parameter", fixed_params
            
            # Check specific action requirements
            action = fixed_params.get("action", "")
            if action in ["click", "double_click", "right_click", "mouse_down", "mouse_up", "mouse_move"]:
                if "coordinates" not in fixed_params or not fixed_params["coordinates"]:
                    return False, f"The '{action}' action requires 'coordinates' parameter", fixed_params
            
            elif action in ["type", "paste", "enter_text"]:
                if "text" not in fixed_params or not fixed_params["text"]:
                    return False, f"The '{action}' action requires 'text' parameter", fixed_params
        
        elif tool_name == "dc_str_replace_editor":
            # Validate command and path parameters
            if "command" not in fixed_params or not fixed_params["command"]:
                return False, "Missing required 'command' parameter", fixed_params
                
            if "path" not in fixed_params or not fixed_params["path"]:
                return False, "Missing required 'path' parameter", fixed_params
                
            # Check command-specific requirements
            command = fixed_params.get("command", "")
            if command in ["write", "append"]:
                if "content" not in fixed_params or fixed_params["content"] is None:
                    return False, f"The '{command}' command requires 'content' parameter", fixed_params
            
            elif command in ["replace", "replace_all"]:
                if "old_str" not in fixed_params or fixed_params["old_str"] is None:
                    return False, f"The '{command}' command requires 'old_str' parameter", fixed_params
                    
                if "new_str" not in fixed_params or fixed_params["new_str"] is None:
                    return False, f"The '{command}' command requires 'new_str' parameter", fixed_params
        
        # Default case - assume valid
        return True, "Parameters validated successfully", fixed_params
    
    def should_break_execution(self) -> bool:
        """
        Check if we should break execution to prevent infinite loops.
        
        Returns:
            True if we should break execution, False otherwise
        """
        return self.attempt_count >= self.max_attempts
    
    def reset_attempt_count(self):
        """Reset the attempt count."""
        self.attempt_count = 0