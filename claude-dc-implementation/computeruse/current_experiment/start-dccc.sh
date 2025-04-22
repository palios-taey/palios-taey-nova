#!/bin/bash
# Launch DCCC (Claude DC + Claude Code) Collaboration

# Ensure we are in the home directory
cd /home/computeruse

# Display DCCC header
echo "=============================================="
echo "  Starting DCCC Collaboration Environment     "
echo "=============================================="
echo "IMPORTANT: Please ensure Claude DC is already running"
echo ""
echo "Launch Claude DC if not already running with:"
echo "   cd /home/computeruse/github/palios-taey-nova"
echo "   ./claude_dc_launch.sh"
echo ""
echo "Starting Claude Code environment..."
echo "   When Claude Code starts, it will use the prompt-cache for efficient access"
echo ""
echo "Press ENTER to launch Claude Code..."
read -r

# Launch Claude Code with proper instructions - using the prompt-cache feature
./claude-code --prompt-cache-file=/computeruse/cache/cache.md "Please review /computeruse/dccc/CLAUDE.md for context. You are running in the Claude DC environment and will be collaborating directly with Claude DC (The Conductor). Note: Your prompt-cache has been set up to use /computeruse/cache/cache.md efficiently."