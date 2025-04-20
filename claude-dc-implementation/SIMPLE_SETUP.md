# Claude DC - Simple Setup Guide

This guide describes a simplified approach for getting Claude DC running with streaming, thinking, and tool use capabilities.

## Overview

Instead of trying to enhance the host-side launcher scripts, we're taking a more direct approach:

1. Launch the standard container using the proven launch script
2. Run a simple setup script inside the container
3. Configure features incrementally, starting with the most stable options

This approach avoids Python path issues and complex launcher scripts that have been causing problems.

## Quick Start

### Step 1: Launch the Container

```bash
./current-execution-status/claude-integration/launch_computer_use.sh
```

This will start a fresh container and drop you into a bash shell inside it.

### Step 2: Run the Setup Script

From inside the container:

```bash
cd github/palios-taey-nova
./claude_dc_setup.sh
```

The script will:
1. Set up proper environment variables for screen dimensions
2. Ask which beta features you want to enable
3. Ask if you want streaming responses enabled
4. Launch Streamlit with the proper configuration

### Step 3: Access the Interface

Once the setup is complete, you can access Claude DC through:

- **VNC Desktop:** http://localhost:6080
- **Streamlit UI:** http://localhost:8501
- **Combined UI:** http://localhost:8080

## Feature Configuration

### Core Features

- **Streaming Responses:** Enables Claude's responses to appear token-by-token in real-time
- **Tool Use:** Always enabled - allows Claude to use tools during its response
- **Thinking:** Always enabled - gives Claude a thinking token budget for complex reasoning

### Beta Features

The setup script allows you to select which beta features to enable:

1. **No beta features** (most stable) - All beta flags disabled
2. **Only prompt caching** - Enables prompt caching for better token efficiency
3. **Prompt caching + extended output** - Also enables 128K token output
4. **All beta features** - Enables all available beta features

Start with option 1 or 2 for maximum stability. Only add more features if the basic functionality is working properly.

## Recommended Configurations

For most reliable streaming with tool use:
```
- Streaming: Enabled
- Beta features: None or only prompt caching
```

For maximum output length:
```
- Streaming: Enabled 
- Beta features: Prompt caching + extended output
```

## Testing Streaming and Tool Use

A dedicated test script is included that specifically tests streaming with tool use:

```bash
# Inside the container
cd github/palios-taey-nova
./test_streaming_tool_use.sh
```

This script:
1. Sets up a minimal configuration (streaming enabled, all beta features disabled)
2. Runs a simple test that asks Claude to use a tool
3. Shows the incremental output from streaming
4. Verifies that tool use works correctly with streaming

If this test passes, you can be confident that the core streaming with tool use functionality is working properly.

## Verifying Streaming Works

When streaming is working correctly:

1. You'll see Claude's responses appear incrementally, word by word
2. When Claude uses a tool, the tool invocation will appear in the UI
3. The tool output will be shown, and Claude will continue generating its response
4. The entire interaction will be continuous, without interruptions

## Troubleshooting

If you encounter issues:

1. Exit the container (Ctrl+D)
2. Run the launch script again to start with a fresh container
3. Run the setup script with fewer features enabled:
   - Disable all beta features
   - Try with or without streaming

For persistent issues, try accessing Claude DC directly through the VNC interface at http://localhost:6080 rather than using Streamlit.

## Advanced Usage

To modify environment variables or features after initial setup, you can set them directly and restart Streamlit:

```bash
# Inside the container
export ENABLE_STREAMING=true
export ENABLE_THINKING=true
export ENABLE_PROMPT_CACHING=false
export ENABLE_EXTENDED_OUTPUT=false
export ENABLE_TOKEN_EFFICIENT=false

cd /home/computeruse
python3 run_claude_dc.py
```