#!/bin/bash
# Script to deploy the tested system to production

# Exit on error
set -e

# Timestamp for backups
TIMESTAMP=$(date +%Y%m%d%H%M)

# Create comprehensive backup of current production
echo "Creating backup of current production environment..."
mkdir -p /home/computeruse/computer_use_demo/backups/pre_deployment_${TIMESTAMP}
cp -r /home/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/backups/pre_deployment_${TIMESTAMP}/
echo "Backup created at /home/computeruse/computer_use_demo/backups/pre_deployment_${TIMESTAMP}/"

# Deploy the tested system
echo "Deploying the tested system to production..."

# 1. Copy the fixed safe_ops module
echo "Deploying safe_ops module..."
cp -r /home/computeruse/computer_use_demo/tests/complete_system_test/safe_ops/* /home/computeruse/computer_use_demo/safe_ops/

# 2. Deploy the tool intercept module
echo "Deploying tool_intercept module..."
mkdir -p /home/computeruse/computer_use_demo/tool_intercept
cp -r /home/computeruse/computer_use_demo/tests/complete_system_test/tool_intercept/* /home/computeruse/computer_use_demo/tool_intercept/

# 3. Update core system files
echo "Deploying loop.py and streamlit.py..."
cp /home/computeruse/computer_use_demo/tests/complete_system_test/loop.py /home/computeruse/computer_use_demo/
cp /home/computeruse/computer_use_demo/tests/complete_system_test/streamlit.py /home/computeruse/computer_use_demo/

echo "Deployment completed successfully!"
echo "The environment now has all protection systems properly integrated."