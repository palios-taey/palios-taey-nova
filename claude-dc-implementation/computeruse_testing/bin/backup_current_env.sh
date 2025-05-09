#!/usr/bin/env bash
# Backup current Claude DC environment

# Define paths
PROD_PATH="/home/computeruse/computer_use_demo"
BACKUP_DIR="/home/computeruse/my_stable_backup_complete"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${TIMESTAMP}"

echo "Creating backup of current Claude DC environment..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if production path exists
if [ ! -d "$PROD_PATH" ]; then
    echo "ERROR: Production directory doesn't exist: $PROD_PATH"
    exit 1
fi

# Create timestamped backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Copy files to backup location
echo "Copying files from $PROD_PATH to $BACKUP_DIR/$BACKUP_NAME"
cp -r "$PROD_PATH"/* "$BACKUP_DIR/$BACKUP_NAME/"

# Log backup creation
echo "Backup created at: $BACKUP_DIR/$BACKUP_NAME"
echo "Backup contents:"
ls -la "$BACKUP_DIR/$BACKUP_NAME/"

echo "Backup complete!"