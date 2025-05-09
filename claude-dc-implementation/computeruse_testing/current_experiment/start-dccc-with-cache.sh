#!/bin/bash
# Script to launch Claude Code with prompt cache for DCCC collaboration

# Ensure we're in the home directory
cd /home/computeruse

# Set up DCCC directory if it doesn't exist
mkdir -p /home/computeruse/dccc

# Copy necessary files if needed
if [ ! -f "/home/computeruse/dccc/CLAUDE.md" ] && [ -f "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_CODE_DCCC.md" ]; then
  cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_CODE_DCCC.md /home/computeruse/dccc/CLAUDE.md
fi

# Display header
echo "=============================================="
echo "  Starting DCCC Collaboration Environment     "
echo "=============================================="
echo "IMPORTANT: Please ensure Claude DC is already running"
echo ""
echo "Starting Claude Code with prompt cache..."
echo "Press ENTER to continue..."
read -r

# Launch Claude Code with prompt-cache using the stable run-claude-code-simple.sh
/home/computeruse/run-claude-code-simple.sh --prompt-cache-file=/home/computeruse/cache/cache.md "Please review /home/computeruse/dccc/CLAUDE.md for context. You are running in the Claude DC environment and will be collaborating directly with Claude DC."