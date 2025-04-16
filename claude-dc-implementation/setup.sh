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
rsync -av --delete /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/ /home/computeruse/computer_use_demo/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/

# Setup git config
git config --global user.email "jesselarose@gmail.com"
git config --global user.name "palios-taey"

pkill -9 python
pkill -9 python3
pkill -9 streamlit

find /home/computeruse -name "__pycache__" -type d -exec rm -rf {} +
find /home/computeruse -name "*.pyc" -exec rm {} +

# Ensure only these files/directories exist
ls -la /home/computeruse/computer_use_demo/
# Should only show loop.py, streamlit.py, requirements.txt, and tools/

cd /home/computeruse
streamlit run computer_use_demo/streamlit.py

# Now edit the secrets file to remove the random text from API keys
echo "IMPORTANT: Now edit the secrets file to remove the random text from the API keys:"
echo "nano /home/computeruse/secrets/palios-taey-secrets.json"

echo "Setup completed! Now you can work with Claude Computer Use!"
