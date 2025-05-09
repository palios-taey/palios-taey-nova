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

### Anthropic SDK
```python
# Non-streaming API (original)
client.beta.messages.with_raw_response.create(
    max_tokens=max_tokens,
    messages=messages,
    model=model,
    system=[system],
    tools=tool_collection.to_params(),
    betas=betas,
    extra_body=extra_body,
)

# Streaming API (our implementation)
async with client.messages.stream(
    model=model,
    max_tokens=max_tokens,
    messages=messages,
    tools=tools,
    anthropic_beta=",".join(betas) if betas else None,
    thinking=thinking_param,
    stream=True,
) as stream:
    async for event in stream:
        # Process events
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