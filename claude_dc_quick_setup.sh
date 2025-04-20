#!/bin/bash
# Consolidated setup script for Claude DC environment

# Run the main setup script
echo "Running main setup script..."
/home/computeruse/github/palios-taey-nova/scripts/setup.sh


# Install Docker in rootless mode (no sudo required)
echo "Setting up Docker in rootless mode..."

# First check if Docker is already available
if command -v docker &> /dev/null; then
    echo "Docker already installed, skipping installation"
else
    echo "Installing Docker in rootless mode..."
    # Install uidmap package if possible (required for rootless mode)
    apt-get install -y uidmap || echo "Cannot install uidmap, continuing anyway..."
    
    # Download and run rootless installation script
    curl -fsSL https://get.docker.com/rootless | sh || echo "Rootless Docker installation failed, will use local mode"
    
    # Set environment variables
    export PATH=/home/$USER/bin:$PATH
    export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
    
    # Add these variables to .bashrc for persistence
    echo 'export PATH=/home/$USER/bin:$PATH' >> ~/.bashrc
    echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc
fi

# Run the Claude DC implementation setup
echo "Running Claude DC implementation setup..."

# Create all required directories
mkdir -p /home/computeruse/cache
mkdir -p /home/computeruse/secrets
mkdir -p /home/computeruse/utils/config 
mkdir -p /home/computeruse/references
mkdir -p /home/computeruse/test_environment
mkdir -p /home/computeruse/bin

# Define source base path
SOURCE_BASE="/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse"

# Copy entire directory structures to maintain organization
echo "Copying directory structures..."
# Copy standard directories (this automatically includes all files)
cp -r "$SOURCE_BASE/cache/"* /home/computeruse/cache/ 2>/dev/null || true
cp -r "$SOURCE_BASE/secrets/"* /home/computeruse/secrets/ 2>/dev/null || true
cp -r "$SOURCE_BASE/utils/"* /home/computeruse/utils/ 2>/dev/null || true
cp -r "$SOURCE_BASE/references/"* /home/computeruse/references/ 2>/dev/null || true

# Copy executable scripts from bin directory to /home/computeruse/bin
echo "Copying executable scripts..."
cp -r "$SOURCE_BASE/bin/"* /home/computeruse/bin/ 2>/dev/null || true
chmod +x /home/computeruse/bin/* 2>/dev/null || true

# Create symlinks in root directory for critical scripts
echo "Creating symlinks for critical scripts in root directory..."
ln -sf /home/computeruse/bin/run_claude_dc.py /home/computeruse/run_claude_dc.py
ln -sf /home/computeruse/bin/run_dev_container.sh /home/computeruse/run_dev_container.sh
ln -sf /home/computeruse/bin/test_dev_environment.py /home/computeruse/test_dev_environment.py
ln -sf /home/computeruse/bin/backup_current_env.sh /home/computeruse/backup_current_env.sh
ln -sf /home/computeruse/bin/deploy_to_production.sh /home/computeruse/deploy_to_production.sh

# Copy documentation files to root directory
echo "Copying documentation files..."
cp "$SOURCE_BASE/"*.md /home/computeruse/ 2>/dev/null || true

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
echo "Setting up computer_use_demo environment..."
mkdir -p /home/computeruse/computer_use_demo/tools

# Copy the updated files from test environment to production
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/

# Make sure the launcher script is executable
chmod +x /home/computeruse/run_claude_dc.py

# Set Claude options
echo "Please set the following Claude options manually:"
echo "   - Model: claude-3-7-sonnet-20250219"
echo "   - Verify end of API key"
echo "   - Max output tokens: 65536"
echo "   - Thinking Enabled: check"
echo "   - Thinking Budget: 32768"
echo "   - Click Reset button"
echo ""
echo "Setup complete!"
echo "You may need to refresh the browser to see the changes."
# Run the Claude DC in local mode to avoid Docker issues
echo "Starting Claude DC in local mode (no Docker required)..."
cd /home/computeruse/
python3 run_claude_dc.py --local
