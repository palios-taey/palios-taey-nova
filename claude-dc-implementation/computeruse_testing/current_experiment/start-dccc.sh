#!/bin/bash
# DCCC Launcher - Starts Claude Code with proper context and prompt cache

# Set up environment
cd /home/computeruse
mkdir -p /home/computeruse/dccc

# Copy necessary files if they don't exist
if [ ! -f "/home/computeruse/dccc/CLAUDE.md" ]; then
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

# Launch Claude Code with prompt-cache
/home/computeruse/claude-code --prompt-cache-file=/home/computeruse/cache/cache.md "Please review /home/computeruse/dccc/CLAUDE.md for context. You are running in the Claude DC environment and will be collaborating directly with Claude DC (The Conductor)."