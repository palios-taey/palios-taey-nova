#!/bin/bash
# Script to fix loop.py API parameter handling

echo "Fixing loop.py beta parameter handling..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current loop.py
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
cp /home/computeruse/computer_use_demo/loop.py /home/computeruse/computer_use_demo/loop.py.bak_${TIMESTAMP}
echo "Created backup at /home/computeruse/computer_use_demo/loop.py.bak_${TIMESTAMP}"

# Update the api_params handling in loop.py
sed -i '
/# Prepare API call parameters/,/# Call the API with streaming enabled/ {
    /api_params\["beta"\] = betas/ {
        s/api_params\["beta"\] = betas/api_params["extra_headers"] = {"x-beta": ",".join(betas)}/
    }
}
' /home/computeruse/computer_use_demo/loop.py

echo "Updated beta parameter handling in loop.py"
echo "To start Claude DC with the fixed code, run:"
echo "cd /home/computeruse"
echo "python3 launch_claude.py"