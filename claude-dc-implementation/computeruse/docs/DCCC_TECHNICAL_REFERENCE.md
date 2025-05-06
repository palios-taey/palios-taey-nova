# DCCC Technical Reference

This document provides quick reference information for the DCCC integration project.

## Key Paths

### Anthropic Implementation
- Main directory: `/home/computeruse/computer_use_demo/`
- Loop code: `/home/computeruse/computer_use_demo/loop.py`
- Streamlit UI: `/home/computeruse/computer_use_demo/streamlit.py`
- Tools: `/home/computeruse/computer_use_demo/tools/`

### Custom Implementation
- Main directory: `/home/computeruse/computer_use_demo_custom/`
- Streaming loop: `/home/computeruse/computer_use_demo_custom/unified_streaming_loop.py`
- Streaming enhancements: `/home/computeruse/computer_use_demo_custom/streaming_enhancements.py`
- Custom tools: `/home/computeruse/computer_use_demo_custom/tools/`

### Integration Files
- Framework: `/home/computeruse/integration_framework.py`
- Integrated UI: `/home/computeruse/integrated_streamlit.py`
- ROSETTA STONE: `/home/computeruse/rosetta_stone.py`
- Continuity: `/home/computeruse/continuity.py`

## Key Commands

### Docker Operations
```bash
# Launch Anthropic container
./current-execution-status/claude-integration/launch_computer_use.sh

# Get container ID
docker ps

# Execute command in container
docker exec -it <container_id> <command>

# Copy files to container
docker cp /path/to/file <container_id>:/destination/path

# Run integration script
./claude-dc-implementation/computeruse/run_integrated_dccc.sh <container_id>
```

### Python Environment
```bash
# Run streamlit app
streamlit run /path/to/app.py

# Test script
python -m /path/to/script.py

# Install package
pip install package_name
```

### File Operations
```bash
# Create backup
cp /path/to/file /path/to/file.bak

# Edit file
nano /path/to/file

# View file
cat /path/to/file

# Change permissions
chmod +x /path/to/script.sh
```

## API Reference

### Anthropic SDK v0.50.0
```python
# Check SDK parameters
import anthropic
import inspect
print(inspect.signature(anthropic.Anthropic().messages.create))
print(inspect.signature(anthropic.Anthropic().messages.stream))

# Non-streaming API (original)
client.beta.messages.with_raw_response.create(
    max_tokens=max_tokens,
    messages=messages,
    model=model,
    system=[system],
    tools=tool_collection.to_params(),
    # Use individual parameters instead of 'betas'
    extra_body=extra_body,
)

# Streaming API (SDK v0.50.0)
# For SDK 0.50.0, use client.messages.stream
stream = await client.messages.create(
    model=model,
    max_tokens=max_tokens,
    messages=messages,
    tools=tools,
    stream=True,  # This enables streaming
    # Use individual parameters instead of betas or anthropic_beta
    # For thinking, the correct format is:
    thinking={
        "enabled": {
            "budget_tokens": thinking_budget
        }
    },
)

# Process streaming events
async for chunk in stream:
    if hasattr(chunk, "type"):
        chunk_type = chunk.type
        
        # Content block delta (text chunks)
        if chunk_type == "content_block_delta":
            if hasattr(chunk.delta, "text") and chunk.delta.text:
                # Process text content
                print(chunk.delta.text, end="", flush=True)
                
        # Thinking tokens
        elif chunk_type == "thinking":
            thinking_text = getattr(chunk, "thinking", "")
            # Process thinking content
            print(f"Thinking: {thinking_text}")
            
        # Tool use blocks
        elif chunk_type == "content_block_start" and getattr(block, "type", None) == "tool_use":
            tool_name = block.name
            tool_input = block.input
            tool_id = getattr(block, "id", "tool_1")
            # Execute tool
```

### Integration Bridge
```python
# Create bridge with default features
bridge = create_bridge()

# Create bridge with custom features
bridge = create_bridge({
    FeatureToggle.USE_STREAMING: True,
    FeatureToggle.USE_THINKING: True,
    FeatureToggle.USE_STREAMLIT_CONTINUITY: True
})

# Call sampling loop via bridge
await bridge.sampling_loop(
    messages=messages,
    model=model,
    output_callback=output_callback,
    tool_output_callback=tool_output_callback,
    api_response_callback=api_response_callback,
    api_key=api_key,
    thinking_budget=thinking_budget
)
```

## Event Types

| Event Type | Description | Usage |
|------------|-------------|-------|
| `content_block_start` | Start of a content block | Initialize content blocks |
| `content_block_delta` | Incremental content update | Add text to current block |
| `content_block_stop` | End of a content block | Finalize content block |
| `message_start` | Start of a message | Initialize message |
| `message_delta` | Incremental message update | Not commonly used |
| `message_stop` | End of a message | Finalize message |
| `thinking` | Thinking token content | Process thinking content |
| `error` | Error event | Handle errors |

## Feature Toggle Reference

| Toggle | Environment Variable | Default | Description |
|--------|----------------------|---------|-------------|
| `USE_STREAMING` | `ENABLE_STREAMING` | True | Enable streaming responses |
| `USE_THINKING` | `ENABLE_THINKING` | True | Enable thinking token management |
| `USE_ROSETTA_STONE` | `ENABLE_ROSETTA` | False | Enable AI-to-AI communication protocol |
| `USE_STREAMLIT_CONTINUITY` | `ENABLE_CONTINUITY` | True | Enable state persistence |

## Common Issues and Solutions

### Streaming Not Working
- Check `stream=True` is set in API call
- Verify proper event handling for streaming events
- Check Anthropic SDK version (should be ≥0.50.0)
- For SDK 0.50.0, don't use the `betas` parameter (use individual parameters instead)
- Verify the thinking parameter format is correct for your SDK version

### Handling Streaming Events
- Different event types require specific handling
- Content blocks should be processed incrementally
- Tool use during streaming requires special attention
- Thinking tokens may appear between content blocks
- Ensure event handlers account for all possible event types

### Tool Use Errors
- Ensure tool definitions match expected format
- Check required parameters are provided
- Verify tools are registered correctly

### Streamlit Continuity Issues
- Check state file permissions
- Verify state file isn't corrupted
- Ensure serializable state format

### Docker Issues
- Verify ports are properly mapped
- Check container is running
- Ensure API key is properly set

### SDK Version Compatibility
- SDK 0.50.0+ uses different parameter formats
- `betas` parameter is no longer used (replaced with individual parameters)
- Thinking parameter format changed to `thinking={"enabled": {"budget_tokens": 4000}}`
- Check API parameters using `inspect.signature()` on SDK functions