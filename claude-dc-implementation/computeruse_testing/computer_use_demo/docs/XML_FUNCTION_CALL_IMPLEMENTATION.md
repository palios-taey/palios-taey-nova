# XML Function Call Implementation for Claude DC

This document summarizes the implementation of XML-style function calls for Claude DC, addressing the feedback that Claude DC struggled with correctly generating function calls during streaming despite the buffer pattern implementation.

## Problem Overview

After implementing the buffer pattern, Claude DC was still experiencing issues:

1. Claude DC understood the required format but struggled to generate it correctly during streaming
2. Even with buffering to prevent partial execution, Claude DC was not maintaining the correct structure
3. The issue was a disconnect between Claude DC's understanding of the format and its implementation during generation

## Solution: XML-Style Function Calls

We implemented a comprehensive solution that:

1. Enhances the system prompt with explicit XML syntax patterns and examples
2. Adds XML structure validation with detailed feedback
3. Provides clear syntax guidance in error messages
4. Supports both JSON and XML formats for backwards compatibility

### Components Implemented:

1. **Enhanced System Prompt**: 
   - Clear XML syntax with proper tag structure
   - Multiple examples for each tool type
   - Syntax error avoidance guidance
   - Detailed parameter requirements

2. **XML Tool Validator**:
   - Parses and validates XML structure
   - Extracts tool name and parameters
   - Provides detailed error messages with suggestions
   - Identifies common syntax mistakes

3. **Enhanced Tool Call Buffer**: 
   - Support for both JSON and XML formats
   - Detection of XML-style function calls in progress
   - Enhanced error handling with feedback
   - Format-specific processing

4. **Streamlined Error Messages**:
   - Specific details about syntax errors
   - Suggestions for correction
   - Examples of correct syntax
   - Clear context for the problem

## Implementation Details

### 1. Enhanced System Prompt

The system prompt now includes explicit XML syntax guidance:

```
# REQUIRED FUNCTION CALL SYNTAX

When using tools, you MUST follow this EXACT format with proper XML tags:

```xml
<function_calls>
<invoke name="TOOL_NAME">
<parameter name="PARAM_NAME">PARAM_VALUE</parameter>
</invoke>
</function_calls>
```

For example, to run a bash command:

```xml
<function_calls>
<invoke name="dc_bash">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>
```
```

### 2. XML Tool Validator

A dedicated validator ensures proper XML structure:

```python
def validate_xml_structure(xml_str: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Validate the XML structure of a tool call."""
    try:
        # Check for complete tags
        if not xml_str.strip().startswith('<function_calls>'):
            return False, "Missing opening <function_calls> tag", None
            
        if not xml_str.strip().endswith('</function_calls>'):
            return False, "Missing closing </function_calls> tag", None
        
        # Parse XML
        root = ET.fromstring(xml_str)
        
        # Extract tool information
        invoke_elements = root.findall('./invoke')
        if not invoke_elements:
            return False, "Missing <invoke> tag", None
        
        invoke = invoke_elements[0]
        tool_name = invoke.get('name')
        
        # Extract parameters
        parameters = {}
        param_elements = invoke.findall('./parameter')
        for param in param_elements:
            param_name = param.get('name')
            param_value = param.text
            parameters[param_name] = param_value
            
        # Return extracted data
        extracted_data = {
            'tool_name': tool_name,
            'parameters': parameters
        }
        
        return True, "XML structure is valid", extracted_data
    
    except ET.ParseError as e:
        # Provide detailed error location
        line_col = re.search(r'line (\d+), column (\d+)', str(e))
        if line_col:
            line, col = line_col.groups()
            lines = xml_str.split('\n')
            problem_line = lines[int(line)-1] if int(line) <= len(lines) else ""
            pointer = ' ' * (int(col)-1) + '^'
            
            error_details = f"XML parsing error at line {line}, column {col}:\n{problem_line}\n{pointer}"
            return False, error_details, None
        else:
            return False, f"XML parsing error: {str(e)}", None
```

### 3. Enhanced Buffer Processing

The buffer now detects and processes XML-style function calls:

```python
def process_content_block_stop(self, index: int) -> Optional[Dict[str, Any]]:
    """Process a content_block_stop event during streaming."""
    buffer = self.json_buffers[index]
    
    # First check for XML-style tool call (preferred format)
    if XML_VALIDATOR_AVAILABLE and '<function_calls>' in buffer:
        # Try to extract tool call data from XML
        is_valid, message, extracted_data = extract_tool_call_data(buffer)
        
        if is_valid and extracted_data:
            # Extract tool information
            xml_tool_name = extracted_data.get('tool_name')
            xml_parameters = extracted_data.get('parameters', {})
            
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
                suggestion = generate_correction_suggestion(buffer)
                
                return {
                    'type': 'tool_call_error',
                    'error': f"XML validation error: {message}",
                    'suggestion': suggestion,
                    'buffer': buffer,
                    'format': 'xml_invalid'
                }
    
    # Fallback to JSON parsing (original behavior)
    try:
        tool_params = json.loads(buffer)
        # ... JSON processing logic
    except json.JSONDecodeError as e:
        # Check if it's an incomplete XML tool call
        if '<function_calls>' in buffer and '</function_calls>' not in buffer:
            return {
                'type': 'tool_call_error',
                'error': "Incomplete XML tool call (missing closing tags)",
                'format': 'xml_incomplete'
            }
        else:
            # ... JSON error handling
```

### 4. Error Feedback for Claude DC

When XML validation fails, Claude DC receives feedback to improve:

```python
# Handle XML validation errors specifically
if result and result.get('type') == 'tool_call_error' and 'xml' in result.get('format', ''):
    error_msg = result.get('error', 'Unknown XML validation error')
    suggestion = result.get('suggestion', '')
    
    # Provide feedback to help Claude DC improve its XML structure
    formatted_error = f"\n\n[Tool Call Syntax Error: {error_msg}]"
    if suggestion:
        formatted_error += f"\n{suggestion}"
    
    logger.warning(f"XML validation error: {error_msg}")
    enhanced_callbacks.on_text(formatted_error)
    continue
```

## Benefits

This XML function call implementation solves Claude DC's issues by:

1. Providing a clear, structured format that's easier to generate correctly
2. Using XML's inherent structure to prevent malformation
3. Offering detailed feedback when errors occur
4. Maintaining backwards compatibility with JSON
5. Supporting both immediate and progressive validation

## Testing

A dedicated test script (`test_xml_streaming.py`) verifies the XML function call implementation with various prompts designed to test:

1. Basic XML function calls
2. Complex commands
3. Parameter extraction
4. XML buffer pattern with partial generation
5. Error handling and feedback

## Conclusion

The XML function call implementation addresses Claude DC's feedback by providing a more structured, clear format with detailed guidance and feedback. By using XML tags instead of JSON, we leverage a format that's more resilient to partial generation and provides clearer syntax boundaries. This should significantly improve Claude DC's ability to correctly generate function calls during streaming.