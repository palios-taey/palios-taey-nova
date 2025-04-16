#!/bin/bash
# Setup script for Claude DC environment

# Create necessary directories
mkdir -p /home/computeruse/cache
mkdir -p /home/computeruse/secrets
mkdir -p /home/computeruse/utils/config 
mkdir -p /home/computeruse/references

# Copy the modified secrets file from GitHub to the secrets directory
# IMPORTANT: You'll need to modify the API keys manually after copying to remove the random text


# Copy /home/computeruse/ directories
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/cache/* /home/computeruse/cache/
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/secrets/* /home/computeruse/secrets/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/utils/* /home/computeruse/utils/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/


# Setup git config
git config --global user.email "jesselarose@gmail.com"
git config --global user.name "palios-taey"

# Now edit the secrets file to remove the random text from API keys
echo "IMPORTANT: Now edit the secrets file to remove the random text from the secrets:"
echo "nano /home/computeruse/secrets/palios-taey-secrets.json"
echo "nano /home/computeruse/secrets/id_ed25519"

echo "Setup completed!"
