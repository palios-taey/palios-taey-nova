#!/bin/bash
# Setup script for Claude DC environment

# Create necessary directories
mkdir -p /home/computeruse/cache
mkdir -p /home/computeruse/env_backup
mkdir -p /home/computeruse/my_broken_backup_20250414
mkdir -p /home/computeruse/my_enhanced_protection_system_202504142055
mkdir -p /home/computeruse/my_stable_backup_complete
mkdir -p /home/computeruse/secrets
mkdir -p /home/computeruse/test_rate_protection
mkdir -p /home/computeruse/utils/config
mkdir -p /home/computeruse/test 

# Copy the modified secrets file from GitHub to the secrets directory
# IMPORTANT: You'll need to modify the API keys manually after copying to remove the random text
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/* /home/computeruse/secrets/

# Copy cache and utils contents to their appropriate locations
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/

# Overwrite computer_use_demo with optimized configurations
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/

# Copy backups
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/my_enhanced_protection_system_202504142055/* /home/computeruse/my_enhanced_protection_system_202504142055/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/env_backup/* /home/computeruse/env_backup/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/test_rate_protection/* /home/computeruse/test_rate_protection/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/test/* /home/computeruse/test/

# Files - these were missing spaces between source and destination
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/claude-dc-extended-use-guidance.md /home/computeruse/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/chatgpt-input-token-research.md /home/computeruse/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/YOUR_Home.md /home/computeruse/

# Setup git config
git config --global user.email "jesselarose@gmail.com"
git config --global user.name "palios-taey"

# Now edit the secrets file to remove the random text from API keys
echo "IMPORTANT: Now edit the secrets file to remove the random text from the API keys:"
echo "nano /home/computeruse/secrets/palios-taey-secrets.json"

echo "Setup completed! Now you can run the basic chat script: "
