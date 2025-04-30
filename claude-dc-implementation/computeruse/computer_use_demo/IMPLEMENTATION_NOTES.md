# Claude DC Implementation Notes

## Recent Fixes (2025-04-30)

### 0. Tool Use ID Fix
Fixed a critical API error related to tool use message format. The API requires a specific format for tool use and tool result messages:

```python
# Tool use message must include an ID in this exact format:
{
    "role": "assistant",
    "content": [{
        "type": "tool_use",
        "id": "toolu_unique_id",  # ID must be at the top level, not nested!
        "name": "tool_name",      # Name and input at the top level too
        "input": {...}            # Input contains the parameters
    }]
}

# Tool result message must reference the same ID but using id instead of tool_use_id:
{
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": "toolu_unique_id",  # Must match the tool use ID above
                                          # IMPORTANT: Field must be named "tool_use_id" not "id"
        "content": "Result content",
        "is_error": false
    }]
}
```

Key findings:
1. The `"id"` field in the `tool_use` structure is required by the API
2. The `tool_use_id` in the `tool_result` must match this ID to link them
3. Using `None` as a tool_use_id will cause API errors

Fixed by:
1. Generating unique IDs for each tool use
2. Adding a validation step to ensure all tool_use messages have an ID
3. Ensuring tool result messages reference the correct tool_use ID
4. Properly formatting the content and is_error fields in tool results

### 1. KeyError Fix in Streamlit UI
Fixed a critical KeyError: 'name' issue in the `_render_message` function in streamlit.py. The function was trying to directly access message["name"] and message["input"] when rendering tool use messages, but the tool_use message structure can vary depending on the API response format.

**Fix Solution:**
```python
# Before:
elif message["type"] == "tool_use":
    st.code(f'Tool Use: {message["name"]}\nInput: {message["input"]}')

# After:
elif message["type"] == "tool_use":
    # Safely access name and input fields with fallbacks
    name = message.get("name", message.get("tool_use", {}).get("name", message.get("type", "unknown")))
    input_data = message.get("input", message.get("tool_use", {}).get("input", {}))
    st.code(f'Tool Use: {name}\nInput: {json.dumps(input_data, indent=2)}')
```

This fix handles multiple possible structures of tool_use messages:
- Direct access format: `{"type": "tool_use", "name": "bash", "input": {...}}`
- Nested format: `{"type": "tool_use", "tool_use": {"name": "bash", "input": {...}}}`
- Hybrid format: `{"type": "tool_use", "name": "bash", "tool_use": {"input": {...}}}`
- Missing fields: Falls back to reasonable defaults if fields are missing

Added a test script `test_streamlit_fix.py` to verify the fix works for different message formats.

### 2. Tool Format Update
The API has extremely specific requirements for how tools must be defined. We've updated the tool formats from:

```python
# Old format
{
    "type": "function",
    "function": { ... }
}
```

To:

```python
# Simplified format for bash tool - NO parameters field, just name and type!
{
    "type": "bash_20250124",
    "name": "bash"
}

# For computer actions, must use custom type with input_schema:
{
    "type": "custom",               
    "name": "computer",             
    "description": "...",           # Description is allowed for custom tools
    "input_schema": { ... }         # Custom tools require input_schema, not parameters
}

# Editor tool requires EXACT name "str_replace_editor"
{
    "type": "text_editor_20250124",
    "name": "str_replace_editor"    # MUST be exactly "str_replace_editor"!
}
```

**Critical Requirements:**
1. The API only accepts specific tool types: 'bash_20250124', 'custom', and 'text_editor_20250124'. It does NOT accept 'computer_use_20250124' as a valid type.
2. ALL tool types require a 'name' field, regardless of whether they're standard or custom tools.
3. For text_editor_20250124, the name MUST be exactly "str_replace_editor" - no other name will work.
4. The standard tools (bash_20250124, text_editor_20250124) do NOT accept a 'description' field or 'parameters' field in the top level - it will cause an error.
5. Custom tools DO allow a 'description' field.
6. For custom tools, the API requires an 'input_schema' field instead of 'parameters'. This is different from the standard tools.
7. When the model uses a custom tool, the parameters are sent in the 'input' field, not in a 'parameters' field.

### 2. Thinking Parameter Requirements
When using the thinking parameter, there are strict requirements:
- Temperature MUST be set to 1.0 (no other value works)
- Thinking budget must be at least 1024 tokens
- max_tokens must be greater than thinking.budget_tokens

```python
# Correct way to set thinking parameter
if thinking:
    params["thinking"] = thinking
    # Temperature must be 1.0 when thinking is enabled
    params["temperature"] = 1.0
    # Ensure max_tokens is greater than thinking.budget_tokens
    if "budget_tokens" in thinking and params["max_tokens"] <= thinking["budget_tokens"]:
        params["max_tokens"] = thinking["budget_tokens"] * 2
else:
    # Use the specified temperature if thinking is not enabled
    params["temperature"] = temperature
```

### 3. Beta Flags Setup
Beta flags must be passed in the client headers, not as request parameters:

```python
client = AsyncAnthropic(
    api_key=api_key,
    default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
)
```

### 4. SDK Version Requirement
The implementation requires Anthropic SDK v0.50.0.
- Added clearer warnings about version mismatch
- Added `update_anthropic_sdk.sh` script to easily update to the required version
- Run `./update_anthropic_sdk.sh` if you see SDK version warnings

### 5. Tool Implementation Enhancements
- Updated all tool implementations to handle different input formats
- Added parameter normalization to accommodate various input structures
- Improved error handling and logging in all tool implementations
- Modified execute_tool function to support the new tool naming requirements

## Testing Strategy

1. **Incremental Testing**: Test each tool individually before using all together
   ```bash
   # Test bash tool only
   python test_tool_format.py --bash
   
   # Test computer tool only
   python test_tool_format.py --computer
   
   # Test edit tool only
   python test_tool_format.py --edit
   
   # Test all tools together
   python test_tool_format.py --all
   ```

2. **Tool Variant Testing**: Test different tool variants
   ```bash
   # Test with specific tool definitions
   python test_tool_variants.py --tools tool_definitions/bash_tool.json
   ```

## Common Errors and Solutions

1. `tools.0.bash_20250124.parameters: Extra inputs are not permitted`
   - **Solution**: Remove parameters field entirely from bash tool definition

2. `tools.0.text_editor_20250124.name: Input should be 'str_replace_editor'`
   - **Solution**: Name must be exactly "str_replace_editor" for text_editor_20250124

3. `thinking.enabled.budget_tokens: Input should be greater than or equal to 1024`
   - **Solution**: Set thinking.budget_tokens to at least 1024

4. `` max_tokens` must be greater than `thinking.budget_tokens` ``
   - **Solution**: Ensure max_tokens > thinking.budget_tokens

5. `` temperature` may only be set to 1 when thinking is enabled ``
   - **Solution**: Set temperature to 1.0 when thinking is enabled

## How to Run

1. Ensure you have the correct SDK version:
   ```bash
   ./update_anthropic_sdk.sh
   ```

2. Start the Streamlit interface:
   ```bash
   ./run_streamlit.sh
   ```

## Beta Features

The implementation uses several beta features:
- Tools support via "tools-2024-05-16" beta flag
- Extended output support via "output-128k-2025-02-19" beta flag
- Thinking parameter for extended reasoning capability