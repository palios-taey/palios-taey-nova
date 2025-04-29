#!/bin/bash
# Deploy the streamlit_starter implementation to the computer_use_demo directory

# Create a backup of the current environment
BACKUP_DIR="/home/computeruse/computer_use_demo_backup_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup at $BACKUP_DIR"
cp -r /home/computeruse/computer_use_demo $BACKUP_DIR

# Copy the new implementation to the computer_use_demo directory
echo "Deploying new implementation..."
cp -f /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/streamlit_starter/loop.py /home/computeruse/computer_use_demo/
cp -f /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/streamlit_starter/streamlit_app.py /home/computeruse/computer_use_demo/

# Make sure tools directory exists
mkdir -p /home/computeruse/computer_use_demo/tools

# Copy tool implementations
cp -fr /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/streamlit_starter/tools/* /home/computeruse/computer_use_demo/tools/

# Ensure permissions are correct
chmod -R 755 /home/computeruse/computer_use_demo/tools

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/streamlit_starter/requirements.txt

echo "Deployment complete. You can now run the application with:"
echo "cd /home/computeruse/computer_use_demo && streamlit run streamlit_app.py"