#!/bin/bash
# Direct DCCC launcher using the WORKING xterm command
# No additional wrappers or complexity

# Create DCCC directory if it doesn't exist
mkdir -p /home/computeruse/dccc

# Copy CLAUDE.md if it doesn't exist locally yet
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

# Launch Claude Code with the WORKING xterm command and prompt cache
xterm -fa 'Monospace' -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude --prompt-cache-file=/home/computeruse/cache/cache.md \"Please review /home/computeruse/dccc/CLAUDE.md for context and collaboration with Claude DC\""