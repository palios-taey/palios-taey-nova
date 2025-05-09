# Tool Thinking Implementation for Claude DC

This document explains the implementation of the "Tool Thinking" feature that allows Claude DC to have a dedicated thinking phase before executing tool calls.

## Problem Statement

In streaming mode, Claude DC was experiencing a race condition where:

1. Claude DC would immediately begin constructing function calls without planning
2. Partial function calls would be processed prematurely, causing errors
3. Only after a failure would Claude DC properly plan and structure commands
4. The buffer pattern alone wasn't sufficient, as Claude DC needed dedicated thinking time

## Solution: Tool Thinking Feature

The solution implements a dedicated thinking phase before tool calls:

1. **Enable Streaming Thinking**: Turn on the thinking capability during streaming
2. **Tool-Specific Thinking Budget**: Allocate a specific thinking budget for tool planning
3. **System Prompt Enhancement**: Guide Claude DC to explicitly plan before constructing function calls
4. **Template-Based Commands**: Provide clear examples with a specific phrase to trigger careful planning

## Implementation Details

### 1. Feature Toggles Configuration

```json
{
  "use_streaming_thinking": true,
  "enable_tool_thinking": true,
  "tool_thinking_budget": 2000,
  "api_model": "claude-3-7-sonnet-20250219",
  "use_xml_prompts": true,
  "enable_buffer_delay": true,
  "buffer_delay_ms": 1000,
  "max_tokens": 64000,
  "enable_tool_buffer": true,
  "debug_logging": true,
  "use_response_chunking": true
}
```

### 2. Key Code Changes to Enable Tool Thinking

The primary changes were made in the `unified_streaming_loop.py` file:

#### Initial Stream Configuration
```python
# Configure thinking mode based on feature toggles
if feature_toggles.get("use_streaming_thinking", False) and thinking_budget is not None:
    # Calculate thinking budget - use specified budget or default to 4000
    thinking_tokens = thinking_budget
    api_params["thinking"] = {
        "type": "enabled",
        "budget_tokens": thinking_tokens
    }
    logger.info(f"Enabled thinking with budget of {thinking_tokens} tokens")
```

#### Tool-Specific Thinking Budget for Stream Resumption
```python
# Configure thinking for resuming the stream
if feature_toggles.get("enable_tool_thinking", False):
    # Use a smaller budget for tool planning
    tool_thinking_budget = feature_toggles.get("tool_thinking_budget", 2000)
    resume_params["thinking"] = {
        "type": "enabled",
        "budget_tokens": tool_thinking_budget
    }
    logger.info(f"Enabled tool thinking with budget of {tool_thinking_budget} tokens")
elif "thinking" in resume_params:
    # If tool thinking not enabled, remove thinking to avoid conflicts
    del resume_params["thinking"]
```

### 3. Enhanced System Prompt

The system prompt was updated to include a specific tool usage process:

```
## CRITICAL: Tool Usage Process

⚠️ EXTREMELY IMPORTANT: Before executing ANY tool, ALWAYS follow this exact process:

1. PLANNING PHASE: 
   - FIRST, pause and carefully think about what command you need
   - Determine the exact tool needed and all required parameters
   - Plan the complete XML structure in your mind

2. CONSTRUCTION PHASE:
   - Begin by writing these exact words: "I'll now construct a complete function call for [tool name]:"
   - Then construct the ENTIRE XML structure in one go
   - NEVER send partial XML structures
```

### 4. Example-Based Learning

Added concrete examples with the exact phrase Claude DC should use before constructing commands:

```
EXAMPLE: To list files in a directory
I'll now construct a complete function call for dc_bash:
<function_calls>
<invoke name="dc_bash">
<parameter name="command">ls -la /home/computeruse</parameter>
</invoke>
</function_calls>
```

## Expected Behavior

With these changes, Claude DC should now:

1. Have dedicated thinking time before constructing function calls
2. Explicitly state "I'll now construct a complete function call for [tool name]:" before each command
3. Construct the complete XML structure in one go rather than sending partial fragments
4. Be able to successfully execute commands on the first attempt

## Configuration Options

The tool thinking feature can be configured via the following feature toggles:

1. `use_streaming_thinking`: Enable/disable the thinking feature during streaming
2. `enable_tool_thinking`: Enable/disable the tool-specific thinking budget
3. `tool_thinking_budget`: Number of tokens allocated for tool planning (default: 2000)

## Potential Further Enhancements

1. **Dynamic Thinking Budget**: Adjust the thinking budget based on command complexity
2. **Improved Visual Indicators**: Clearer visual feedback during function construction
3. **Function Call Templates**: Pre-defined templates for common operations
4. **Two-Stage Execution**: Separate planning/construction from execution completely