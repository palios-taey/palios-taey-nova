#!/bin/bash
# Setup script for Claude DC environment

# Create necessary directories
mkdir -p /home/computeruse/secrets
mkdir -p /home/computeruse/cache
mkdir -p /home/computeruse/utils/config
mkdir -p /home/computeruse/env_backup
mkdir -p /home/computeruse/my_backup_20250411_195735

# Copy the modified secrets file from GitHub to the secrets directory
# IMPORTANT: You'll need to modify the API keys manually after copying to remove the random text
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/palios-taey-secrets.json /home/computeruse/secrets/

# Copy cache and utils contents to their appropriate locations
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/

# Overwrite computer_use_demo with optimized configurations
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/

# Copy the README files
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/EMERGENCY_README.md /home/computeruse/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/README.md /home/computeruse/

# Make the scripts executable
chmod +x /home/computeruse/computer_use_demo/basic_chat.py
chmod +x /home/computeruse/computer_use_demo/test_token_manager.py
# Make the test scripts executable
chmod +x /home/computeruse/computer_use_demo/test_token_manager.py
chmod +x /home/computeruse/computer_use_demo/test_verify_environment.py


# Now edit the secrets file to remove the random text from API keys
echo "IMPORTANT: Now edit the secrets file to remove the random text from the API keys:"
echo "nano /home/computeruse/secrets/palios-taey-secrets.json"

echo "Setup completed! Now you can run the basic chat script: "
