#!/bin/bash
# Simple setup script for Claude DC inside the container
# This script configures the necessary environment variables and launches
# Claude DC with the desired features enabled.

set -e  # Exit on error

echo "==================================================="
echo "  Claude DC Setup - with Claude Code Integration"
echo "==================================================="

# Check if we're inside the container
if [ ! -d "/home/computeruse" ]; then
  echo "❌ This script must be run inside the Computer Use container."
  echo "First, launch the container with:"
  echo "  ./current-execution-status/claude-integration/launch_computer_use.sh"
  echo "Then, inside the container:"
  echo "  cd github/palios-taey-nova && ./claude_dc_setup.sh"
  exit 1
fi

# Check for the Claude DC implementation
if [ ! -d "/home/computeruse/github/palios-taey-nova/claude-dc-implementation" ]; then
  echo "❌ Claude DC implementation directory not found."
  echo "Please make sure the repository is properly mounted in the container."
  exit 1
fi

# Install NVM (Node Version Manager) if not already installed
echo "Installing/verifying NVM and Node.js..."
if [ ! -d "/home/computeruse/.nvm" ]; then
  echo "Installing NVM..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  
  # Load NVM
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
else
  echo "NVM already installed, loading it..."
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Install Node.js v18.20.8
echo "Installing Node.js v18.20.8..."
nvm install 18.20.8
nvm use 18.20.8

# Verify Node.js installation
NODE_VERSION=$(node -v)
echo "Node.js version: $NODE_VERSION"

# Install Claude-Code
echo "Installing Claude-Code..."
npm install -g @anthropic/claude-code

# Verify Claude-Code installation
CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "Not installed")
echo "Claude-Code version: $CLAUDE_VERSION"

# Set up environment variables for ComputerTool
export WIDTH=1024
export HEIGHT=768
export DISPLAY_NUM=1
export DISPLAY=:1

echo "✅ Screen dimensions set to ${WIDTH}x${HEIGHT} on display:${DISPLAY_NUM}"

# Check if streaming is enabled
# Note: Streaming is now a core feature, not a beta flag
export ENABLE_STREAMING=true

# Prompt for which features to enable
echo
echo "Select which beta features to enable:"
echo "  1) No beta features (most stable)"
echo "  2) Only prompt caching"
echo "  3) Prompt caching + extended output"
echo "  4) All beta features"
read -p "Enter your choice (1-4) [default: 1]: " beta_choice
beta_choice=${beta_choice:-1}

# Configure beta features
case $beta_choice in
  1)
    echo "✅ Running with NO beta features"
    export ENABLE_PROMPT_CACHING=false
    export ENABLE_EXTENDED_OUTPUT=false
    export ENABLE_TOKEN_EFFICIENT=false
    ;;
  2)
    echo "✅ Running with prompt caching ONLY"
    export ENABLE_PROMPT_CACHING=true
    export ENABLE_EXTENDED_OUTPUT=false
    export ENABLE_TOKEN_EFFICIENT=false
    ;;
  3)
    echo "✅ Running with prompt caching + extended output"
    export ENABLE_PROMPT_CACHING=true
    export ENABLE_EXTENDED_OUTPUT=true
    export ENABLE_TOKEN_EFFICIENT=false
    ;;
  4)
    echo "✅ Running with ALL beta features"
    export ENABLE_PROMPT_CACHING=true
    export ENABLE_EXTENDED_OUTPUT=true
    export ENABLE_TOKEN_EFFICIENT=true
    ;;
  *)
    echo "❌ Invalid choice. Defaulting to NO beta features."
    export ENABLE_PROMPT_CACHING=false
    export ENABLE_EXTENDED_OUTPUT=false
    export ENABLE_TOKEN_EFFICIENT=false
    ;;
esac

# Configure streaming (this is separate from beta features)
read -p "Enable response streaming? (y/n) [default: y]: " enable_streaming
enable_streaming=${enable_streaming:-y}

if [[ "$enable_streaming" =~ ^[Yy]$ ]]; then
  echo "✅ Response streaming ENABLED"
  export ENABLE_STREAMING=true
else
  echo "❌ Response streaming DISABLED"
  export ENABLE_STREAMING=false
fi

# Display feature configuration
echo
echo "Claude DC configuration:"
echo "------------------------"
echo "* Screen: ${WIDTH}x${HEIGHT}"
echo "* Display: :${DISPLAY_NUM}"
echo "* Streaming responses: $([ "$ENABLE_STREAMING" == "true" ] && echo "✅ enabled" || echo "❌ disabled")"
echo "* Prompt caching: $([ "$ENABLE_PROMPT_CACHING" == "true" ] && echo "✅ enabled" || echo "❌ disabled")"
echo "* Extended output: $([ "$ENABLE_EXTENDED_OUTPUT" == "true" ] && echo "✅ enabled" || echo "❌ disabled")"
echo "* Token efficient: $([ "$ENABLE_TOKEN_EFFICIENT" == "true" ] && echo "✅ enabled" || echo "❌ disabled")"
echo "* Thinking enabled: ✅ enabled (always on)"
echo

# Create a Python wrapper script to run Streamlit directly
WRAPPER_SCRIPT="/home/computeruse/run_claude_dc.py"
cat > $WRAPPER_SCRIPT << 'EOF'
#!/usr/bin/env python3
"""
Simple wrapper to launch Claude DC with proper environment setup
"""
import os
import sys
import subprocess
from pathlib import Path

# Ensure all paths are set properly
repo_root = Path("/home/computeruse/github/palios-taey-nova")
claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo = claude_dc_root / "computeruse/computer_use_demo"

# Add paths to Python path
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(claude_dc_root) not in sys.path:
    sys.path.insert(0, str(claude_dc_root))
if str(claude_dc_root / "computeruse") not in sys.path:
    sys.path.insert(0, str(claude_dc_root / "computeruse"))

# Launch Streamlit directly with proper environment
os.chdir(computer_use_demo)
subprocess.run([
    "streamlit", "run", "streamlit.py",
    "--server.port=8501", 
    "--server.headless=true"
])
EOF

chmod +x $WRAPPER_SCRIPT

# Launch Streamlit
echo "Starting Claude DC..."
echo "--------------------"
echo "* VNC access: http://localhost:6080"
echo "* Streamlit UI: http://localhost:8501"
echo "* Combined UI: http://localhost:8080"
echo

# Create a Claude Code launcher script with proper UTF-8 encoding
CLAUDE_CODE_SCRIPT="/home/computeruse/run_claude_code.sh"
cat > $CLAUDE_CODE_SCRIPT << 'EOF'
#!/bin/bash
# Run Claude Code in an XTerm window with proper UTF-8 encoding
xterm -fa 'Monospace' -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 PATH=$PATH:/home/computeruse/.nvm/versions/node/v18.20.8/bin claude $*"
EOF

chmod +x $CLAUDE_CODE_SCRIPT
echo "✅ Created Claude Code launcher script at $CLAUDE_CODE_SCRIPT"
echo "* To run Claude Code: $CLAUDE_CODE_SCRIPT"

# Start Claude DC in the background
cd /home/computeruse
python3 $WRAPPER_SCRIPT