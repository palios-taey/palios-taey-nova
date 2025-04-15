#!/bin/bash
# Script to deploy the tested Safe File Operations to production
set -e

echo "Creating production backup..."
mkdir -p /home/computeruse/my_fixed_backup_20250414
cp -r /home/computeruse/computer_use_demo/safe_ops /home/computeruse/my_fixed_backup_20250414/

echo "Deploying tested Safe File Operations to production..."
mkdir -p /home/computeruse/computer_use_demo/safe_ops
cp /home/computeruse/test_rate_protection/*.py /home/computeruse/computer_use_demo/safe_ops/

echo "Creating documentation..."
echo "Safe File Operations fixed on $(date)" > /home/computeruse/my_fixed_backup_20250414/README.md
echo "Fix implemented to prevent rate limit errors by:" >> /home/computeruse/my_fixed_backup_20250414/README.md
echo "1. Reducing target usage to 60% of rate limit" >> /home/computeruse/my_fixed_backup_20250414/README.md
echo "2. Implementing proper file chunking" >> /home/computeruse/my_fixed_backup_20250414/README.md
echo "3. Using tiktoken for accurate token estimation" >> /home/computeruse/my_fixed_backup_20250414/README.md
echo "4. Adding small delays between operations" >> /home/computeruse/my_fixed_backup_20250414/README.md
echo "5. Integrating with Token Management" >> /home/computeruse/my_fixed_backup_20250414/README.md

echo "Deployment complete!"
