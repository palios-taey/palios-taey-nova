"""
XML Tool Call Validator for Claude DC.

This module provides functions to validate the XML structure of tool calls
and provide detailed feedback for invalid calls.
"""

import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Tuple, List, Any, Optional

# Configure logging
logger = logging.getLogger("xml_tool_validator")
logger.setLevel(logging.INFO)

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