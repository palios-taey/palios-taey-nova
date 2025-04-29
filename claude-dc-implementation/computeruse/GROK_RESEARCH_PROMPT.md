# Anthropic API Tool Format Research Request

## Context
We're implementing Claude DC with tool use capability using the Anthropic API (v0.50.0 SDK). We've encountered specific errors related to tool format definitions that need resolution. Since you (Grok) created the initial implementation, your insights will be valuable.

## Current Issues
1. We've updated from function-style tools to the new format but keep hitting specific format requirements:
   - First error: "tools.0: Input tag 'function' found using 'type' does not match any of the expected tags: 'bash_20250124', 'custom', 'text_editor_20250124'"
   - After fixing: "tools.0.custom.input_schema: Field required" (for custom tools)

## Specific Research Needed

### 1. Exact Tool Format Specifications
- Find the most current, detailed documentation on the exact format required for tools in the Anthropic API
- Focus on the differences between:
  - Standard tools (bash_20250124, text_editor_20250124)
  - Custom tools (type: "custom")

### 2. Schema Requirements By Tool Type
- What is the exact format required for bash_20250124?
- What is the exact format required for text_editor_20250124?
- What is the exact format required for custom tools?
- Do standard tools use "parameters" while custom tools require "input_schema"?

### 3. Working Examples
- Find complete, working examples of each tool type
- Examples should be specifically for the Claude API, not Claude.ai or other implementations
- Include examples of how parameters are passed when calling each tool type

### 4. Tool Execution Format
- How does Claude pass parameters to each tool type during execution?
- For custom tools, are parameters passed in an "input" field?
- For standard tools, how are parameters structured when received?

### 5. Beta Flags Requirements
- Confirm the exact beta flags needed for tool use
- Confirm whether these should be in headers or request parameters

## Current Implementation
Currently, we're defining tools like this:

```python
# Bash tool
{
    "type": "bash_20250124",
    "description": "Execute a bash command",
    "parameters": {
        "type": "object",
        "properties": {...}
    }
}

# Computer tool (custom)
{
    "type": "custom",
    "name": "computer",
    "description": "Control the computer",
    "input_schema": {
        "type": "object",
        "properties": {...}
    }
}

# Edit tool
{
    "type": "text_editor_20250124",
    "description": "Edit files on the system",
    "parameters": {
        "type": "object",
        "properties": {...}
    }
}
```

## Urgency
This is blocking our Claude DC implementation, so detailed and precise information is crucial. Please provide exact specifications and working examples that we can directly implement.

## Additional Notes
- We're using Python with the Anthropic SDK v0.50.0
- The tool format seems extremely specific and unforgiving
- Other Claude interfaces (like Claude.ai web) have working tool implementations that we can learn from
