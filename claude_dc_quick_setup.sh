#!/bin/bash
# Consolidated setup script for Claude DC environment

# Enable debug mode if DEBUG=1 is set
if [ "$DEBUG" = "1" ]; then
    set -x
    echo "Debug mode enabled"
fi

# Run the main setup script
echo "Running main setup script..."
/home/computeruse/github/palios-taey-nova/scripts/setup.sh

# Run the Claude DC implementation setup
echo "Running Claude DC implementation setup..."
mkdir -p /home/computeruse/cache
mkdir -p /home/computeruse/secrets
mkdir -p /home/computeruse/utils/config 
mkdir -p /home/computeruse/references
mkdir -p /home/computeruse/bin
mkdir -p /home/computeruse/dccc

# Copy /home/computeruse/ directories
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/* /home/computeruse/secrets/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/* /home/computeruse/bin/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/dccc/* /home/computeruse/dccc/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/CLAUDE.md /home/computeruse/

# Setup git config
git config --global user.email "jesselarose@gmail.com"
git config --global user.name "palios-taey"

# Remove 'testkey-' from all files in secrets directory
echo "Removing 'testkey-' prefixes from secret files..."
find /home/computeruse/secrets -type f -exec sed -i 's/testkey-//g' {} \;

# Set up SSH configuration
echo "Setting up SSH configuration..."

# Create .ssh directory if it doesn't exist
mkdir -p /home/computeruse/.ssh
chmod 700 /home/computeruse/.ssh

# Copy SSH key to standard location if it exists in secrets
if [ -f "/home/computeruse/secrets/id_ed25519" ]; then
    echo "Moving SSH key from secrets to .ssh directory..."
    cp /home/computeruse/secrets/id_ed25519 /home/computeruse/.ssh/
    chmod 600 /home/computeruse/.ssh/id_ed25519
    
    # Copy public key if it exists
    if [ -f "/home/computeruse/secrets/id_ed25519.pub" ]; then
        cp /home/computeruse/secrets/id_ed25519.pub /home/computeruse/.ssh/
        chmod 644 /home/computeruse/.ssh/id_ed25519.pub
    fi
fi

# Create SSH config file
cat > /home/computeruse/.ssh/config << EOF
Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
EOF
chmod 600 /home/computeruse/.ssh/config

# Test SSH connection
echo "Testing SSH connection to GitHub..."
ssh -o StrictHostKeyChecking=no -T git@github.com || echo "SSH test complete - Note: Exit code 1 is normal for GitHub"

# Change repository remote from HTTPS to SSH
echo "Changing repository remote from HTTPS to SSH..."
cd /home/computeruse/github/palios-taey-nova
git remote set-url origin git@github.com:palios-taey/palios-taey-nova.git

# Set up Claude Code environment
echo "Setting up Claude Code environment..."

# Switch to /home/computeruse directory
cd /home/computeruse

# Install NVM
echo "Installing NVM..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js v18.20.8
echo "Installing Node.js v18.20.8..."
nvm install 18.20.8
nvm use 18.20.8

# Install Claude-Code
echo "Installing Claude-Code..."
npm install -g @anthropic-ai/claude-code

# Verify installations
echo "Node.js version: $(node -v)"
echo "Claude-Code version: $(claude --version 2>/dev/null || echo 'Not installed')"

# Add NVM setup to .bashrc
echo 'export NVM_DIR="$HOME/.nvm"' >> $HOME/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> $HOME/.bashrc

# Set up Claude Code API key from secrets
echo "Setting up Claude Code API key..."
# Create Claude Code config directory
mkdir -p /home/computeruse/.claude

# Extract Claude Code API key from secrets file
if [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
    CLAUDE_CODE_API_KEY=$(grep -o '"claude_code"[[:space:]]*:[[:space:]]*"[^"]*"' /home/computeruse/secrets/palios-taey-secrets.json | sed 's/.*"claude_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    
    if [ ! -z "$CLAUDE_CODE_API_KEY" ]; then
        echo "Claude Code API key found in secrets"
        
        # Create config file with API key
        cat > /home/computeruse/.claude/config.json << EOF
{
  "apiKey": "$CLAUDE_CODE_API_KEY"
}
EOF
        chmod 600 /home/computeruse/.claude/config.json
        
        # Export API key as environment variable
        export ANTHROPIC_API_KEY="$CLAUDE_CODE_API_KEY"
    else
        echo "Error: Claude Code API key not found in secrets file"
    fi
else
    echo "Error: Secrets file not found"
fi

# Set proper encoding environment variables (these are crucial)
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Launch Claude Code with the EXACT command that worked before, only changing font size to 6
echo "Launching Claude Code with xterm..."
if [ ! -z "$CLAUDE_CODE_API_KEY" ]; then
    echo "Using API key from secrets for Claude Code"
    xterm -fa 'Monospace' -fs 6 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 ANTHROPIC_API_KEY=\"$CLAUDE_CODE_API_KEY\" /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
else
    echo "WARNING: No API key found, Claude Code will prompt for key on first run"
    xterm -fa 'Monospace' -fs 6 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
fi

# Set Claude options
echo "Please set the following Claude options manually:"
echo "   - Model: claude-3-7-sonnet-20250219"
echo "   - Verify end of API key"
echo "   - Enable token-efficient tools beta - check"
echo "   - Max output tokens: 12000"
echo "   - Thinking Enabled: check"
echo "   - Thinking Budget: 4000"
echo "   - Click Reset button"
echo ""



