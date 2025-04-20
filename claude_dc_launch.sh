#!/bin/bash
# Launch Claude DC with proper environment setup

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set environment variables
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"your-api-key-here"}
export CLAUDE_ENV=${CLAUDE_ENV:-"live"}

# Launch Claude DC
python3 "$SCRIPT_DIR/launch_helpers/launch_claude_dc.py" "$@"
