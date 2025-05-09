#!/usr/bin/env bash
# Deploy Claude DC code from development to production

# Define paths
HOST_DEV_PATH="/home/computeruse/test_environment"
PROD_PATH="/home/computeruse/computer_use_demo"
BACKUP_DIR="/home/computeruse/my_stable_backup_complete"
BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Preparing to deploy Claude DC code to production..."

# Verify paths exist
if [ ! -d "$HOST_DEV_PATH" ]; then
    echo "ERROR: Development code path doesn't exist: $HOST_DEV_PATH"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup current production files
echo "Creating backup of current production at $BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
mkdir -p "$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"

if [ -d "$PROD_PATH" ]; then
    cp -r "$PROD_PATH"/* "$BACKUP_DIR/backup_$BACKUP_TIMESTAMP/"
    echo "Backup complete."
else
    echo "WARNING: Production directory doesn't exist yet. Creating it now."
    mkdir -p "$PROD_PATH"
fi

# Copy development files to production without Docker container
echo "Deploying code from development to production..."
cp -r "$HOST_DEV_PATH"/* "$PROD_PATH/"

# Check for any existing Claude DC processes and stop them
echo "Checking for any running Claude DC processes..."
pkill -f "streamlit run" 2>/dev/null || true
pkill -f "run_claude_dc.py" 2>/dev/null || true

# Give processes time to terminate
sleep 2

echo "Deployment complete! Claude DC code has been updated."
echo "To start Claude DC, run: python3 /home/computeruse/run_claude_dc.py --local"
echo "Streamlit UI will be available at: http://localhost:8501"