# Claude DC Streaming Implementation: Quick Start Guide

This document provides instructions for starting and using the Claude DC streaming implementation.

## Container Environment

This implementation is designed to work with the specific container environment where:
- Port 8501 is exposed for Streamlit
- Port 6080 is used for VNC
- Port 8080 is used for the combined demo UI

## Starting Claude DC

### Option 1: With Streaming (Default)

```bash
cd /home/computeruse/computer_use_demo
./run_claude_dc.sh --streaming
```

This starts Claude DC with the streaming implementation enabled. You can access the UI at http://localhost:8501.

### Option 2: Without Streaming

```bash
cd /home/computeruse/computer_use_demo
./run_claude_dc.sh --no-streaming
```

This starts Claude DC with the original non-streaming implementation. You can access the UI at http://localhost:8501.

## Troubleshooting

If you have issues accessing the Streamlit UI, you can:

1. Check if ports are accessible:
   ```bash
   ./check_ports.sh
   ```

2. Run a simple Streamlit test:
   ```bash
   ./run_streamlit_8501.sh
   ```

3. Check for errors in the logs:
   ```bash
   # For streaming mode
   cat streamlit_streaming.log
   
   # For non-streaming mode
   cat claude_dc_ui.log
   ```

## Implementation Details

### Core Files

- **Streaming Agent Loop**: `/home/computeruse/computer_use_demo/streaming/unified_streaming_loop.py`
- **Streaming Enhancements**: `/home/computeruse/computer_use_demo/streaming/streaming_enhancements.py`
- **Tool Adapter**: `/home/computeruse/computer_use_demo/streaming/tool_adapter.py`
- **Streaming Tools**:
  - `/home/computeruse/computer_use_demo/streaming/tools/dc_bash.py`
  - `/home/computeruse/computer_use_demo/streaming/tools/dc_file.py`
- **Feature Toggles**: `/home/computeruse/computer_use_demo/streaming/feature_toggles.json`

### Configuration

You can configure various streaming features by editing the `feature_toggles.json` file:

```json
{
  "use_streaming_bash": true,
  "use_streaming_file": true,
  "use_streaming_screenshot": false,
  "use_unified_streaming": true,
  "use_streaming_thinking": true,
  "max_thinking_tokens": 4000,
  "log_level": "INFO",
  "api_model": "claude-3-7-sonnet-20250219"
}
```

## Testing

You can run various tests to verify the implementation:

1. Test the API connection:
   ```bash
   python -m streaming.api_test
   ```

2. Run non-interactive streaming test:
   ```bash
   python -m streaming.non_interactive_test
   ```

3. Test tool streaming:
   ```bash
   python -m streaming.tool_streaming_test
   ```

## Next Steps for Development

1. **Refine UI**: Enhance the Streamlit UI for better streaming visualization
2. **Add More Tools**: Extend streaming capabilities to additional tools
3. **Performance Optimization**: Improve streaming efficiency and responsiveness
4. **Enhanced Thinking Tokens**: Improve the display and utilization of thinking tokens