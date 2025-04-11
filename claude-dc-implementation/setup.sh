#!/bin/bash
# Setup script for Claude DC environment

# Create necessary directories
mkdir -p /home/computeruse/secrets

# Copy the modified secrets file from GitHub to the secrets directory
# IMPORTANT: You'll need to modify the API keys manually after copying to remove the random text
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/palios-taey-secrets.json /home/computeruse/secrets/

# Copy the Python files to their appropriate locations
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/updated_basic_chat.py /home/computeruse/computer_use_demo/basic_chat.py
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/simple_token_manager.py /home/computeruse/computer_use_demo/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/updated_test_token_manager.py /home/computeruse/computer_use_demo/test_token_manager.py

# Copy the README files
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/EMERGENCY_README.md /home/computeruse/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/README.md /home/computeruse/

# Make the scripts executable
chmod +x /home/computeruse/computer_use_demo/basic_chat.py
chmod +x /home/computeruse/computer_use_demo/test_token_manager.py

# Now edit the secrets file to remove the random text from API keys
echo "IMPORTANT: Now edit the secrets file to remove the random text from the API keys:"
echo "nano /home/computeruse/secrets/palios-taey-secrets.json"

echo "Setup completed! Now you can run the basic chat script:"
echo "cd /home/computeruse/computer_use_demo/"
echo "python basic_chat.py"
