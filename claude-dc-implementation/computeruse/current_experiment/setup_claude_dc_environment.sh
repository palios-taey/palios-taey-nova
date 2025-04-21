#!/bin/bash
# Setup script for Claude DC environment
# This prepares the environment for Claude DC and Claude Code collaboration

set -e  # Exit on error

echo "==================================================="
echo "    Claude DC Environment Setup"
echo "==================================================="

# 1. Ensure proper directories exist
mkdir -p /home/computeruse/logs
mkdir -p /home/computeruse/temp
mkdir -p /home/computeruse/current_experiment

# 2. Copy key files
echo "Copying configuration files..."
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/run-claude-code-simple.sh /home/computeruse/
chmod +x /home/computeruse/run-claude-code-simple.sh

# 3. Set up locale for proper encoding
echo "Setting up locale for proper encoding..."
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Add to .bashrc to persist across sessions
if ! grep -q "LANG=C.UTF-8" /home/computeruse/.bashrc; then
    echo '# Fix encoding issues' >> /home/computeruse/.bashrc
    echo 'export LANG=C.UTF-8' >> /home/computeruse/.bashrc
    echo 'export LC_ALL=C.UTF-8' >> /home/computeruse/.bashrc
    echo 'export TERM=xterm-256color' >> /home/computeruse/.bashrc
fi

# 4. Create aliases for convenience
echo "Creating helpful aliases..."
if ! grep -q "alias cc=" /home/computeruse/.bashrc; then
    echo '# Claude Code wrapper alias' >> /home/computeruse/.bashrc
    echo 'alias cc="/home/computeruse/run-claude-code-simple.sh"' >> /home/computeruse/.bashrc
    echo 'alias claude-code="/home/computeruse/run-claude-code-simple.sh"' >> /home/computeruse/.bashrc
fi

# 5. Display information
echo
echo "Environment setup complete!"
echo
echo "Next steps:"
echo "1. Review the onboarding guide: /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_DC_ONBOARDING.md"
echo "2. Launch Claude Code with: /home/computeruse/run-claude-code-simple.sh"
echo "3. Test the streaming implementation: cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment && python3 minimal_test.py"
echo
echo "For details on Claude DC and Claude Code collaboration, see:"
echo "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md"
echo "=================================================="