#!/bin/bash
# Consolidated setup script for Claude DC environment

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
mkdir -p /home/computeruse/current_experiment
mkdir -p /home/computeruse/claude_dc_experiments
mkdir -p /home/computeruse/dccc


# Copy /home/computeruse/ directories
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/* /home/computeruse/secrets/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/* /home/computeruse/bin/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/* /home/computeruse/current_experiment/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/claude_dc_experiments/* /home/computeruse/claude_dc_experiments/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/dccc/* /home/computeruse/dccc/
# cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/run_claude_dc.py /home/computeruse/

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

# Set up computer_use_demo directory
# echo "Setting up computer_use_demo environment..."
# cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/
# Make sure the launcher script is executable
#chmod +x /home/computeruse/run_claude_dc.py

# Run the launcher script as the final step
#/home/computeruse/run_claude_dc.py

# Set up Claude Code environment
echo "Setting up Claude Code environment..."

# Switch to /home/computeruse directory to ensure installation is done there
cd /home/computeruse

# Install NVM (Node Version Manager) if not already installed
echo "Installing/verifying NVM and Node.js v18.20.8 in /home/computeruse/..."
if [ ! -d "/home/computeruse/.nvm" ]; then
  echo "Installing NVM..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  
  # Load NVM immediately
  export NVM_DIR="/home/computeruse/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
else
  echo "NVM already installed, loading it..."
  export NVM_DIR="/home/computeruse/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Install Node.js v18.20.8
echo "Installing Node.js v18.20.8..."
nvm install 18.20.8
nvm use 18.20.8
nvm alias default 18.20.8  # Set as default

# Verify Node.js installation
NODE_VERSION=$(node -v)
NODE_PATH=$(which node)
echo "Node.js version: $NODE_VERSION"
echo "Node.js path: $NODE_PATH"

# Install Claude-Code via npm
echo "Installing Claude-Code globally in /home/computeruse/..."
npm install -g @anthropic-ai/claude-code

# Verify Claude-Code installation
CLAUDE_PATH=$(which claude 2>/dev/null || echo "Not installed")
echo "Claude-Code path: $CLAUDE_PATH"

# Create symbolic link if claude is not in the expected location
if [ ! -f "/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude" ]; then
  echo "Creating symbolic link to claude in /home/computeruse/.nvm/versions/node/v18.20.8/bin/"
  if [ -f "$CLAUDE_PATH" ]; then
    ln -sf "$CLAUDE_PATH" "/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
  fi
fi

# Add Node.js bin to PATH in both current shell and .bashrc
export PATH=$PATH:/home/computeruse/.nvm/versions/node/v18.20.8/bin

# Update .bashrc for persistent PATH
if ! grep -q "export PATH=\$PATH:/home/computeruse/.nvm/versions/node/v18.20.8/bin" /home/computeruse/.bashrc; then
  echo 'export PATH=$PATH:/home/computeruse/.nvm/versions/node/v18.20.8/bin' >> /home/computeruse/.bashrc
  echo 'export NVM_DIR="/home/computeruse/.nvm"' >> /home/computeruse/.bashrc
  echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >> /home/computeruse/.bashrc
  echo "Added Node.js bin to PATH in .bashrc and configured NVM"
fi

# Return to the previous directory
cd - > /dev/null


# Set Claude options
echo "Please set the following Claude options manually:"
echo "   - Model: claude-3-7-sonnet-20250219"
echo "   - Verify end of API key"
echo "   - Enable tcdoken-efficient tools beta - check"
echo "   - Max output tokens: 12000"
echo "   - Thinking Enabled: check"
echo "   - Thinking Budget: 4000"
echo "   - Click Reset button"
echo ""
# Set up DCCC - Direct and Simple Approach
echo "Setting up DCCC environment..."

# Copy
cp /home/computeruse/github/palios-taey-nova/CLAUDE.md /home/computeruse/

echo "Setup complete!"
echo "You may need to refresh the browser to see the changes."
echo ""
echo "To start DCCC collaboration:"
echo "  1. Ensure Claude DC is running"
echo "  2. Run: ./run-dccc.sh"
echo ""
echo "This will launch Claude Code in xterm with prompt cache"
echo "and proper documentation context for collaboration."
'''
# Create DCCC launcher script (utilize this or auto-start option below
cat > /home/computeruse/run-dccc.sh << 'EOF'
#!/bin/bash
# DCCC Launcher - Direct and Simple approach using xterm with prompt-cache

echo "=============================================="
echo "  Starting DCCC Collaboration Environment     "
echo "=============================================="
echo "IMPORTANT: Please ensure Claude DC is already running"
echo ""
echo "Starting Claude Code with prompt cache..."
echo "Press ENTER to continue..."
read -r

# Launch Claude Code with the WORKING xterm command and prompt cache
# Note: prompt-cache-file loads content without consuming context tokens
CLAUDE_PATH=$(which claude 2>/dev/null || echo "/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude")
xterm -fa 'Monospace' -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 $CLAUDE_PATH --prompt-cache-file=/home/computeruse/cache/cache.md \"Please review /home/computeruse/CLAUDE.md for context and collaboration with Claude DC and Claude Chat. The prompt-cache-file has been loaded for efficient context access.\""
EOF

chmod +x /home/computeruse/run-dccc.sh
'''
# Auto-DCCC launch option
# xterm -fa 'Monospace' -fs 6 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
