#!/bin/bash
# Ultra-minimal approach to running Claude Code with correct encoding and Node options
# Place this file directly in /home/computeruse/ and make it executable with:
# chmod +x claude-code-with-options.sh

# Set essential encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Add Node options for adequate memory (optional, but helpful)
export NODE_OPTIONS="--max-old-space-size=4096"

# Claude Code direct path - verified location
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude"

# Run Claude Code executable directly
exec "$CLAUDE_PATH" "$@"