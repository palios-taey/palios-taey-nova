#!/bin/bash
# Simple wrapper script for running Claude Code with correct encoding
# This fixes the UTF-8 encoding issues in the container environment

# Set proper locale to fix encoding issues
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Use the exact path to claude-code discovered by Claude Chat
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude"

# Create xterm window with proper encoding
xterm -fa "Monospace" -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 $CLAUDE_PATH $*"