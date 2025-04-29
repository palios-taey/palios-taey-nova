# Claude DC Implementation Guide

**Project:** PALIOS AI OS – Claude DC ("The Conductor") Implementation  
**Role:** *Claude DC* – The Conductor Agent with Computer Use capabilities  
**Context:** This is a complete streaming implementation with tool use

## Overview

This directory contains a production-ready implementation of Claude with streaming capabilities, tool use, thinking parameters, and other advanced features. It addresses the issues found in previous implementations and provides a stable foundation for your operation.

## Key Features

1. **Streaming with Tool Use**: Real-time, token-by-token streaming with seamless tool integration
2. **Proper Parameter Handling**: Correct implementation of thinking as a parameter (not a beta flag)
3. **Beta Flags Configuration**: Proper header-based beta flag configuration
4. **Event-Based Processing**: Comprehensive handling of all streaming event types
5. **Tool Validation**: Parameter validation for all tools before execution
6. **Error Handling**: Robust error recovery with proper exception handling
7. **Streamlit UI**: Real-time UI updates with state persistence

## Directory Structure

- `loop.py` - Core implementation with streaming and tool use
- `streamlit_app.py` - Streamlit UI for interacting with Claude
- `tools/` - Tool implementations:
  - `bash.py` - Execute shell commands
  - `computer.py` - Control the computer (mouse/keyboard)
  - `edit.py` - File operations (read/write/append)
- `run_streamlit.sh` - Script to launch the Streamlit UI
- `verify.py` - Script to verify the implementation
- `requirements.txt` - Required dependencies

## Implementation Details

### Beta Flags

Previous implementations incorrectly passed beta flags as parameters, causing errors like:
```
AsyncMessages.create() got an unexpected keyword argument 'anthropic_beta'
```

This implementation correctly sets beta flags in the client headers:
```python
client = AsyncAnthropic(
    api_key=api_key,
    default_headers={"anthropic-beta": "output-128k-2025-02-19,tools-2024-05-16"}
)
```

### Thinking Parameter

Previous implementations incorrectly treated thinking as a beta flag. This implementation correctly passes it as a parameter in the request body:

```python
if thinking_budget:
    params["thinking"] = {
        "type": "enabled",
        "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
    }
```

### Streaming Event Handling

This implementation properly handles all streaming event types:

1. `content_block_start` - For detecting new content blocks (text or tool use)
2. `content_block_delta` - For processing streaming content updates and tool inputs
3. `content_block_stop` - For finalizing tool inputs and executing tools
4. `message_stop` - For detecting message completion

### Tool Execution During Streaming

Tool execution happens when a complete tool input is received:
```python
if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
    tool_input_acc += event.delta.partial_json
    
elif event.type == "content_block_stop":
    # We have a complete tool input
    tool_input = json.loads(tool_input_acc)
    # Execute the tool...
```

## Getting Started

1. **Verify the Implementation**:
   ```bash
   python verify.py --all
   ```

2. **Run the Streamlit App**:
   ```bash
   ./run_streamlit.sh
   ```

## Configuration Options

The Streamlit UI provides several configuration options:

- **Model Selection**: Choose between Claude models
- **Thinking**: Enable/disable thinking and adjust budget
- **Prompt Caching**: Enable/disable prompt caching
- **Extended Output**: Enable/disable 128k output
- **Debug Mode**: View detailed event information

## Deployment to Production

To deploy this implementation to your production environment:

1. **Create a backup of your current environment**:
   ```bash
   cp -r /home/computeruse/computer_use_demo /home/computeruse/computer_use_demo_backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Copy the new implementation files**:
   ```bash
   cp -r /home/computeruse/computer_use_demo_grok/* /home/computeruse/computer_use_demo/
   ```

3. **Verify the installation**:
   ```bash
   cd /home/computeruse/computer_use_demo
   python verify.py --all
   ```

4. **Start using the new environment**:
   ```bash
   cd /home/computeruse/computer_use_demo
   ./run_streamlit.sh
   ```

## Troubleshooting

If you encounter issues:

1. **SDK Version**: Ensure you're using Anthropic SDK v0.50.0
   ```bash
   python -c "import anthropic; print(anthropic.__version__)"
   ```

2. **API Key**: Verify your API key is correctly set in the environment
   ```bash
   echo $ANTHROPIC_API_KEY | wc -c
   ```

3. **Debug Mode**: Enable debug mode to see detailed events
   ```bash
   ./run_streamlit.sh --debug
   ```

4. **Logs**: Check the log files for errors
   ```bash
   cat streamlit_app.log
   cat claude_dc.log
   ```

## Collaboration with Claude Code

Remember that Claude Code (DCCC) is available to help with any implementation issues or enhancements. The collaboration protocol is documented in:
```
/home/computeruse/dccc/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md
```

To communicate efficiently with Claude Code, use the ROSETTA STONE protocol:
```
[SENDER][TOPIC][MESSAGE]
```

Example:
```
[DC][ERROR][Getting error on API call: Request entity too large]
```

## Future Enhancements

After you've successfully deployed and tested this implementation, consider these enhancements:

1. **Additional Tools**: Add more specialized tools for your specific needs
2. **Prompt Caching Optimization**: Fine-tune cache control for better performance
3. **Extended Output Testing**: Test with longer outputs up to 128k tokens
4. **Thinking Parameter Tuning**: Experiment with different thinking budgets
5. **UI Enhancements**: Add more features to the Streamlit UI

Remember: You are Claude DC, the Conductor of the PALIOS AI OS. This implementation provides you with the stable foundation you need to fulfill your role effectively.