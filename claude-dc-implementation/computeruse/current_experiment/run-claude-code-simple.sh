#!/bin/bash
# Simple wrapper script for running Claude Code with correct encoding settings
# This fixes the UTF-8 encoding issues in the container environment

# Set proper locale to fix encoding issues
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Check where the claude-code executable might be
if [ -f "/home/computeruse/bin/claude-code" ]; then
    CLAUDE_CODE="/home/computeruse/bin/claude-code"
elif [ -f "/usr/local/bin/claude-code" ]; then
    CLAUDE_CODE="/usr/local/bin/claude-code"
elif [ -f "/usr/bin/claude-code" ]; then
    CLAUDE_CODE="/usr/bin/claude-code"
else
    echo "Could not find claude-code executable. Please specify the full path."
    echo "Usage: PATH_TO_CLAUDE_CODE=/path/to/claude-code $0"
    if [ ! -z "$PATH_TO_CLAUDE_CODE" ]; then
        CLAUDE_CODE="$PATH_TO_CLAUDE_CODE"
    else
        exit 1
    fi
fi

echo "Using Claude Code executable: $CLAUDE_CODE"

# Run Claude Code from the root directory
cd /home/computeruse
$CLAUDE_CODE "$@"