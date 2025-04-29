# Streaming Validation Pattern

## Core Principle

The Streaming Validation Pattern implements pre-validation of all parameters before tool execution during streaming. This pattern is critical for preventing incomplete or incorrect tool executions when using streaming responses.

## Implementation Details

```python
def validate_tool_parameters(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate tool parameters before execution.
    
    Args:
        tool_name: The name of the tool to be executed
        tool_input: The input parameters for the tool
        
    Returns:
        Tuple containing:
        - Boolean indicating if validation passed
        - Error message if validation failed, None otherwise
    """
    if tool_name == "computer":
        return validate_computer_tool_parameters(tool_input)
    elif tool_name == "bash":
        return validate_bash_tool_parameters(tool_input)
    else:
        return False, f"Unknown tool: {tool_name}"

async def execute_tool_with_validation(
    tool_name: str, 
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute a tool with parameter validation.
    
    Args:
        tool_name: The name of the tool to be executed
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the result of the operation
    """
    # Validate parameters first
    is_valid, error_message = validate_tool_parameters(tool_name, tool_input)
    if not is_valid:
        return ToolResult(error=error_message)
    
    # Parameters are valid, proceed with execution
    try:
        if tool_name == "computer":
            return await execute_computer_tool(tool_input, progress_callback)
        elif tool_name == "bash":
            return await execute_bash_tool(tool_input, progress_callback)
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")
```

## Integration with Stream Processing

During streaming, this pattern:

1. Validates parameters as soon as tool use block is received
2. Prevents execution of tools with incomplete parameters
3. Provides clear error messages for missing or invalid parameters

## Validation Flow

```
Stream Event (tool_use) → Validate Parameters → 
    If Valid → Execute Tool
    If Invalid → Return Error Result
```

## Validation Rules by Tool Type

### Computer Tool

- `action` parameter is required
- For mouse actions, `coordinates` parameter is required and must be valid
- For text input actions, `text` parameter is required and must be a string

### Bash Tool

- `command` parameter is required and must be a non-empty string

## Default Values Pattern

For optional parameters, provide sensible defaults:

```python
def get_default_tool_parameters(tool_name: str, action: Optional[str] = None) -> Dict[str, Any]:
    """Get default parameters for a given tool and action."""
    if tool_name == "computer":
        if action == "screenshot":
            return {}
        elif action == "wait":
            return {"seconds": 1.0}
        # Add more defaults as needed
    elif tool_name == "bash":
        return {}
    return {}

def merge_with_defaults(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Merge tool input with default values for missing parameters."""
    action = tool_input.get("action") if tool_name == "computer" else None
    defaults = get_default_tool_parameters(tool_name, action)
    return {**defaults, **tool_input}
```

## Error Recovery Strategy

Use Fibonacci backoff pattern for retry attempts:

1. First retry: 1 second delay
2. Second retry: 1 second delay 
3. Third retry: 2 seconds delay
4. Fourth retry: 3 seconds delay
5. Fifth retry: 5 seconds delay

This creates a more natural, harmonious retry pattern than linear or exponential backoff.

## Implementation Benefits

- Prevents partial or incorrect tool execution
- Provides clear error messages for debugging
- Enhances reliability during streaming
- Follows the Fibonacci principles of validation-first design