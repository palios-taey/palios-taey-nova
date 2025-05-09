# Streaming Integration Guide

This document outlines how to safely integrate the streaming implementation with production code while maintaining stability.

## Integration Strategy

The streaming implementation is designed for seamless integration with existing code through a careful, phased approach:

1. **Feature Flags**: Introduce streaming as an opt-in feature
2. **Independent Deployment**: Deploy streaming components separately from core functionality
3. **Progressive Rollout**: Enable streaming for specific tools first, then expand
4. **Fallback Mechanism**: Maintain non-streaming paths as fallbacks
5. **Comprehensive Monitoring**: Add detailed logging and telemetry

## Integration Steps

### 1. Preparation

Before integrating the streaming implementation, take these steps:

1. **Create Backups**: Backup all production code that will be modified
2. **Set Up Monitoring**: Implement comprehensive logging for streaming components
3. **Create Feature Flag**: Add a `use_streaming` flag in configuration
4. **Test Extensively**: Run all streaming tests in isolation
5. **Document Existing Behavior**: Capture baseline behavior for comparison

### 2. Add Streaming Components

Next, add the streaming components to the production environment:

1. **Copy Files**: Copy the streaming implementation files to the production directory
2. **Update Imports**: Ensure imports work correctly in the production environment
3. **Configure Environment**: Set up any environment variables needed for streaming
4. **Verify Installation**: Run basic tests to ensure components are accessible

### 3. Create Adapter Layer

To safely bridge between existing code and streaming implementation:

1. **Create Adapter Functions**: Build adapter functions that can use either streaming or non-streaming paths
2. **Add Feature Toggle**: Implement logic to choose between streaming and non-streaming based on feature flags
3. **Implement Error Handling**: Add robust error handling with fallback to non-streaming paths
4. **Preserve Compatibility**: Ensure adapters maintain the same interface as existing functions

### 4. Integration Points

These are the key integration points for the streaming implementation:

1. **Agent Loop**: Replace or adapt the existing agent loop with streaming capabilities
2. **UI Callbacks**: Update UI components to handle streaming callbacks
3. **Tool Execution**: Enhance tool execution to support streaming and progress reporting
4. **Error Handling**: Update error handling to support streaming-specific issues
5. **Session Management**: Integrate streaming session management with existing sessions

### 5. Sample Integration Code

Here's a minimal example of how to integrate streaming with existing code:

```python
# Existing imports
from existing_module import execute_agent_loop

# New imports
from dc_streaming_agent_loop import dc_streaming_agent_loop

# Feature flag
USE_STREAMING = config.get("use_streaming", False)

# Adapter function
async def agent_loop(user_input, conversation_history=None, **kwargs):
    """Adapter function that supports both streaming and non-streaming."""
    try:
        if USE_STREAMING:
            # Use streaming implementation
            return await dc_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
        else:
            # Use existing implementation
            return await execute_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
    except Exception as e:
        logger.error(f"Error in agent loop: {str(e)}")
        # Fall back to non-streaming if streaming fails
        if USE_STREAMING:
            logger.warning("Falling back to non-streaming implementation")
            return await execute_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
        # Re-raise if already using non-streaming
        raise
```

### 6. UI Integration

To integrate streaming with the UI:

1. **Define Callbacks**: Implement callbacks for real-time UI updates
2. **Handle Tool Progress**: Update UI to show tool execution progress
3. **Manage Interruptions**: Add interrupt handlers for user cancellation
4. **Error Indication**: Provide clear error state visualization

Sample UI callback implementation:

```python
# Define UI callbacks
callbacks = {
    "on_text": lambda text: update_ui_with_text(text),
    "on_tool_use": lambda name, input: show_tool_use(name, input),
    "on_tool_result": lambda name, input, result: show_tool_result(result),
    "on_tool_progress": lambda name, input, message, progress: update_progress_bar(progress),
    "on_thinking": lambda text: show_thinking_indicator()
}

# Use callbacks with streaming agent loop
result = await agent_loop(
    user_input=user_input,
    callbacks=callbacks,
    use_streaming=True
)
```

### 7. Testing the Integration

After integration, test extensively with these cases:

1. **Basic Streaming**: Verify text appears incrementally
2. **Tool Use**: Test tool invocation during streaming
3. **Error Handling**: Test recovery from API errors
4. **Interruptions**: Verify user can interrupt responses
5. **Progress Reporting**: Check tool progress is reported
6. **Feature Toggle**: Verify switching between streaming and non-streaming works
7. **Fallback Mechanism**: Test falling back to non-streaming when streaming fails

### 8. Rollout Plan

1. **Internal Testing**: Enable streaming for internal users first
2. **Limited Beta**: Roll out to a small percentage of users
3. **Monitoring Period**: Monitor performance and issues
4. **Gradual Expansion**: Increase percentage of users with streaming enabled
5. **Full Deployment**: Enable for all users after stability is confirmed

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Streaming interrupts unexpectedly | Check for API timeout or connection issues |
| Tool results not showing correctly | Verify tool result formatting in callbacks |
| UI not updating incrementally | Ensure UI framework supports incremental updates |
| Increased API errors | Check rate limiting and token management |
| Performance degradation | Monitor memory usage and callback efficiency |

## Monitoring the Integration

Monitor these key metrics:

1. **Stream Completion Rate**: Percentage of streaming responses that complete successfully
2. **Tool Success Rate**: Success rate of tool executions during streaming
3. **Response Latency**: Time to first token and time to completion
4. **Fallback Frequency**: How often streaming falls back to non-streaming
5. **Error Rates**: Types and frequencies of errors

## Additional Resources

- See `dc_streaming_agent_loop.py` for complete implementation details
- The `run_streaming_cli.py` script demonstrates a simple integration
- `test_streaming_agent_loop.py` contains examples of testing streaming functionality