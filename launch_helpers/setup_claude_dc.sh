#!/bin/bash
# Claude DC Setup Script
# This script sets up Claude DC with streaming, tool integration, and prompt caching

set -e  # Exit on error

REPO_ROOT="/home/jesse/projects/palios-taey-nova"
CLAUDE_DC_ROOT="$REPO_ROOT/claude-dc-implementation"
COMPUTER_USE_DEMO="$CLAUDE_DC_ROOT/computeruse/computer_use_demo"
LAUNCH_HELPERS="$REPO_ROOT/launch_helpers"

echo "Setting up Claude DC - Phase 2 Enhancements..."

# Make sure python and pip are available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Aborting."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Aborting."
    exit 1
fi

# Create launch helpers directory if it doesn't exist
mkdir -p "$LAUNCH_HELPERS"

# Install required packages
echo "Installing required packages..."
pip3 install -q anthropic==0.49.0 streamlit httpx

# Ensure proper permissions
echo "Setting executable permissions..."
chmod +x "$LAUNCH_HELPERS/launch_claude_dc.py"

# Create a wrapper script to properly launch Claude DC
echo "Creating wrapper script..."
cat > "$REPO_ROOT/claude_dc_launch.sh" << 'EOF'
#!/bin/bash
# Launch Claude DC with proper environment setup

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set environment variables
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"your-api-key-here"}
export CLAUDE_ENV=${CLAUDE_ENV:-"live"}

# Launch Claude DC
python3 "$SCRIPT_DIR/launch_helpers/launch_claude_dc.py" "$@"
EOF

# Make the wrapper script executable
chmod +x "$REPO_ROOT/claude_dc_launch.sh"

# Create a CHANGES.md file to document the updates
echo "Creating CHANGES.md to document updates..."
cat > "$CLAUDE_DC_ROOT/CHANGES.md" << 'EOF'
# Claude DC - Phase 2 Enhancements

## Overview
The Claude DC system has been upgraded to Tier 4 with the following enhancements:

### 1. Streaming Responses
- Claude API calls now use `stream=True` for token-by-token responses
- UI displays incremental output in real-time
- Partial replies are preserved when tools are used mid-response

### 2. Tool Integration in Stream
- Claude can use tools mid-response without losing context
- Text already output is maintained when a tool executes
- Tool execution errors are handled gracefully

### 3. Prompt Caching
- Uses Anthropic's prompt caching beta
- Last few user messages marked with `cache_control: ephemeral`
- Significantly reduces token usage for repeated contexts

### 4. 128K Extended Output
- Enables extended output beta for very long answers
- Adjusted `max_tokens` to ~64k for optimal performance
- Utilizes thinking token budget (~32k) for complex reasoning

### 5. Stability Fixes
- Disabled token-efficient tool use beta by default for reliability
- Ensures full conversation context is available each turn
- Fixed import structure to prevent circular imports
- Centralized constants in __init__.py for easier maintenance

### 6. Real-Time Tool Output
- Tool outputs (like command-line results) stream to the UI in real-time
- Uses callbacks to update the UI during tool execution
- Provides immediate feedback on long-running tool operations

## Implementation Details
- Created unified launcher with proper Python path setup
- Fixed streamlit and delta_generator import issues
- Reorganized module structure to avoid import conflicts
- Added proper streaming support for both text and tool outputs
- Centralized configuration options in the UI

## Usage
Run the claude_dc_launch.sh script to start Claude DC:
```bash
./claude_dc_launch.sh
```

Additional options:
```bash
./claude_dc_launch.sh --mode console  # Run in console mode (no UI)
./claude_dc_launch.sh --env dev       # Run in development mode
```
EOF

echo "Claude DC setup complete!"
echo "To launch Claude DC, run: $REPO_ROOT/claude_dc_launch.sh"