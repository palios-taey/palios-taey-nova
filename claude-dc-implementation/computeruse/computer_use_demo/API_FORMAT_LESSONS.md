# API Format Lessons for Claude Tool Use

## Tool Format Requirements

The Anthropic API has extremely specific requirements for how tools, tool use messages, and tool result messages must be structured.

### 1. Tool Definitions

Tools must be defined with these exact formats:

```python
# Standard tool (like bash)
{
    "type": "bash_20250124",  # Type must be exact versioned name
    "name": "bash"            # Name is required
}

# NO parameters, description, or other fields allowed for standard tools!

# Custom tool
{
    "type": "custom",            # Must be "custom" for non-standard tools
    "name": "computer",          # Name is required
    "description": "...",        # Description is allowed for custom tools
    "input_schema": {            # Must use input_schema, not parameters
        "type": "object",
        "properties": { ... },
        "required": [...]
    }
}

# Text editor tool
{
    "type": "text_editor_20250124",
    "name": "str_replace_editor"  # MUST be exactly "str_replace_editor"
}
```

### 2. Tool Use Messages

Tool use messages must have this exact structure:

```python
# In assistant messages:
{
    "role": "assistant",
    "content": [{
        "type": "tool_use",
        "id": "toolu_unique_id",  # ID at the top level, not nested!
        "name": "tool_name",      # Name at the top level
        "input": {                # Input contains parameters
            "param1": "value1",
            "param2": "value2"
        }
    }]
}
```

Key requirements:
- The `id` field must be at the top level of the tool_use object
- Do NOT nest details inside a "tool_use" field
- The API expects a flat structure with type, id, name, and input all at the same level

### 3. Tool Result Messages

Tool result messages must have this exact structure:

```python
# In user messages:
{
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": "toolu_unique_id",  # Must match the tool use ID
        "content": "Result content",
        "is_error": false
    }]
}
```

Key requirements:
- In tool result messages, the field must be named `tool_use_id` (not `id`)
- Do NOT nest details inside a "tool_result" field
- The API expects a flat structure with type, tool_use_id, content, and is_error at the same level

## Why These Details Matter

The API performs strict validation on these message formats:
- Wrong field names will cause 400 Bad Request errors
- Missing required fields will cause validation errors
- Nested structures where flat ones are expected will be rejected
- Extra fields that aren't allowed will be rejected

## Common Errors and Their Meanings

1. `messages.X.content.0.tool_use.id: Field required`:
   - You're using a nested structure for tool_use messages
   - Fix: Move the "id" to the top level of the tool_use object

2. `messages.X.content.0.tool_result.tool_use_id: Field required`:
   - You're using a nested structure for tool_result messages
   - Fix: Use a flat structure with tool_use_id at the top level

3. `tools.0.bash_20250124.parameters: Extra inputs are not permitted`:
   - You've included a parameters field in a standard tool
   - Fix: Remove the parameters field entirely

4. `tools.0.text_editor_20250124.name: Input should be 'str_replace_editor'`:
   - The text editor tool name must be exactly "str_replace_editor"
   - Fix: Use the exact name required

## Best Practices for Tool Implementation

1. **Test individual tools first** before combining them
2. **Log all API requests and responses** to debug format issues
3. **Follow the exact structures** shown in this document
4. **Validate message formats** before sending to the API
5. **Generate proper IDs** for tool use that follow the API's format

## Testing Tool Format

Use the `verify_tool_format.py` script to verify that your tool format is correct.
This script makes a complete API request with tool use and tool result messages to ensure 
the format is compatible with the API requirements.