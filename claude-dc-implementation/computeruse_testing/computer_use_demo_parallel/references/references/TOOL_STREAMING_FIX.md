# Tool Streaming Implementation Fix

## Current Issues

Based on the errors in the logs, we have two major issues with the tool streaming implementation:

1. **Corrupted conversation history**: The API is returning a 400 error with the message: `unexpected tool_use_id found in tool_result blocks`. This suggests our conversation history has an invalid structure with mismatched tool_use_id references.

2. **Async iterator implementation issue**: The attempt to convert a generator to an async iterator with `(chunk for chunk in output_chunks).__aiter__()` is failing because Python generators don't directly support the `__aiter__` method.

## Proposed Solutions

### 1. Fix Conversation History Corruption

The immediate issue appears to be that there's a lingering tool result in the conversation history without a matching tool use. We need to:

1. Reset the conversation history to clear any corrupt entries
2. Implement proper tracking for tool_use and tool_result pairs in the history

### 2. Create a Clean Implementation for Async Streaming

The current approach is trying to mix regular generators with async generators in a way that's not correct. We should:

1. Reimplement the tools with proper async generators
2. Use a correct pattern for async stream processing

## Implementation Plan

### Step 1: Add Conversation History Reset

Add a "Reset Conversation" button in the UI that completely clears all history and state to resolve the immediate API errors.

### Step 2: Fix Async Generator Implementation

Replace the problematic code with a proper async implementation:

```python
# Instead of:
tool_result = await dc_process_streaming_output(
    (chunk for chunk in output_chunks).__aiter__()
)

# Use:
tool_result = await dc_process_streaming_output(output_chunks)

# And modify dc_process_streaming_output to handle a list directly:
async def dc_process_streaming_output(output_chunks):
    # Process chunks from the list
    # ...
```

### Step 3: Fix Tool Use ID Tracking

Modify the tool resumption logic to properly track tool use IDs:

```python
# Store the full tool_use message in history:
tool_use_message = {
    "role": "assistant",
    "content": [{
        "type": "tool_use",
        "id": tool_id,
        "name": tool_name,
        "input": tool_input
    }]
}
conversation_history.append(tool_use_message)

# Then add the tool result with matching ID:
tool_result_message = {
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": tool_result_content
    }]
}
conversation_history.append(tool_result_message)
```

This ensures that each tool_result has a matching tool_use in the conversation history.

## Testing Approach

1. Start with a completely fresh conversation state
2. Implement basic logging in the message creation code
3. Validate message structure before sending to API
4. Test with simple tool use cases first (e.g., basic bash commands)

## Implementation Recommendations

1. Consider implementing a fallback non-streaming mode for tool execution
2. Add more comprehensive error handling with specific recovery paths
3. Improve parameter validation before tool execution
4. Implement a conversation history sanitizer to prevent corruption