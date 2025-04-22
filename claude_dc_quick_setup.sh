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


# Copy /home/computeruse/ directories
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/* /home/computeruse/secrets/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/* /home/computeruse/bin/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/* /home/computeruse/current_experiment/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/claude_dc_experiments/* /home/computeruse/claude_dc_experiments/
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
if [ -f "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/setup_claude_dc_environment.sh" ]; then
      echo "Setting up Claude Code environment..."
      /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/setup_claude_dc_environment.sh
fi

cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/run-claude-code-simple.sh /home/computeruse/
chmod +x /home/computeruse/run-claude-code-simple.sh


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
# Set up DCCC (Claude DC + Claude Code) environment
echo "Setting up DCCC environment..."

# 1. Set up Claude Code with xterm solution (simple and reliable)
echo "Setting up Claude Code xterm launcher..."
echo '#!/bin/bash
# Launch Claude Code in xterm with proper encoding
xterm -fa "Monospace" -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude $*"' > /home/computeruse/claude-code
chmod +x /home/computeruse/claude-code

# 2. Create DCCC directory and copy necessary files
echo "Setting up DCCC documentation..."
mkdir -p /home/computeruse/dccc
if [ -f "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_CODE_DCCC.md" ]; then
    cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_CODE_DCCC.md /home/computeruse/dccc/CLAUDE.md
    cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md /home/computeruse/dccc/
fi

# 3. Copy the start-dccc.sh launcher script
echo "Setting up DCCC launcher..."
if [ -f "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/start-dccc.sh" ]; then
    cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/start-dccc.sh /home/computeruse/
    chmod +x /home/computeruse/start-dccc.sh
    echo "Copied start-dccc.sh to home directory"
else
    # Fallback if the script is not found
    echo "Creating minimal start-dccc.sh in home directory..."
    echo '#!/bin/bash
# DCCC Launcher - Starts Claude Code with proper context and prompt cache
cd /home/computeruse
echo "=============================================="
echo "  Starting DCCC Collaboration Environment     "
echo "=============================================="
echo "Starting Claude Code with prompt cache..."
echo "Press ENTER to continue..."
read -r
./claude-code --prompt-cache-file=/home/computeruse/cache/cache.md "Please review /home/computeruse/dccc/CLAUDE.md for context. You are running in the Claude DC environment and will be collaborating directly with Claude DC."' > /home/computeruse/start-dccc.sh
    chmod +x /home/computeruse/start-dccc.sh
fi

echo "Setup complete!"
echo "You may need to refresh the browser to see the changes."
echo ""
echo "To start DCCC collaboration:"
echo "  1. Ensure Claude DC is running"
echo "  2. Run: ./start-dccc.sh"
echo ""
echo "For quick Claude Code access:"
echo "  Run: ./claude-code or /home/computeruse/claude-code"
# Run the launcher script as the final step
# /home/computeruse/run_claude_dc.py
