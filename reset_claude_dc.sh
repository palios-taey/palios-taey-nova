#!/bin/bash
# Script to reset Claude DC to a default state while preserving important files

echo "Resetting Claude DC environment to defaults..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current environment
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/computeruse/reset_backup_${TIMESTAMP}"

echo "Creating backup at ${BACKUP_DIR}..."
mkdir -p "${BACKUP_DIR}"

# Back up key directories before resetting
if [ -d "/home/computeruse/computer_use_demo" ]; then
    echo "Backing up computer_use_demo directory..."
    cp -r /home/computeruse/computer_use_demo "${BACKUP_DIR}/"
fi

if [ -d "/home/computeruse/test_environment" ]; then
    echo "Backing up test_environment directory..."
    cp -r /home/computeruse/test_environment "${BACKUP_DIR}/"
fi

# Make sure we have the repository available
if [ ! -d "/home/computeruse/github/palios-taey-nova" ]; then
    echo "ERROR: Repository not found at /home/computeruse/github/palios-taey-nova"
    echo "Please ensure the repository is mounted in the container"
    exit 1
fi

# Clean up existing directories
echo "Removing existing environment directories..."
rm -rf /home/computeruse/computer_use_demo
rm -rf /home/computeruse/test_environment
rm -rf /home/computeruse/bin

# Create fresh directories
echo "Creating fresh directories..."
mkdir -p /home/computeruse/computer_use_demo
mkdir -p /home/computeruse/test_environment
mkdir -p /home/computeruse/bin
mkdir -p /home/computeruse/references

# Copy fresh versions of the files from repository
echo "Copying default files from repository..."
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/computer_use_demo/
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/* /home/computeruse/bin/
chmod +x /home/computeruse/bin/*

# Copy reference documents
echo "Copying reference documents..."
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/* /home/computeruse/references/

# Copy the error log to references
cp /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/references/claude-dc-error-log20250418.md /home/computeruse/references/

# Create symbolic links for convenience
ln -sf /home/computeruse/bin/run_claude_dc.py /home/computeruse/run_claude_dc.py

# Set environment variable
export CLAUDE_ENV=dev

echo "Reset complete! Claude DC environment has been reset to defaults."
echo "To start Claude DC, run: python3 /home/computeruse/run_claude_dc.py --local"