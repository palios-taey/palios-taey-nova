#!/usr/bin/env bash
# Deploy Claude DC code from development to production

# Define paths
HOST_DEV_PATH="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
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

# Stop the running container if it exists
echo "Stopping Claude DC production container..."
docker stop claude_dc 2>/dev/null || true

# Copy development files to production
echo "Deploying code from development to production..."
cp -r "$HOST_DEV_PATH"/* "$PROD_PATH/"

# Restart container
echo "Restarting Claude DC production container..."
docker start claude_dc 2>/dev/null || true

# If container doesn't exist or failed to start, show instructions
if [ $? -ne 0 ]; then
    echo "Claude DC container not found or couldn't be restarted."
    echo "You may need to create it first with:"
    echo "docker run -d --name claude_dc \\
  -e ANTHROPIC_API_KEY=\$ANTHROPIC_API_KEY \\
  -p 8501:8501 -p 6080:6080 -p 5900:5900 \\
  -v \"$PROD_PATH:/home/computeruse/computer_use_demo/\" \\
  anthropic-computer-use:latest"
    exit 1
fi

echo "Deployment complete! Claude DC is now running with the updated code."
echo "Streamlit UI available at: http://localhost:8501"
echo "Viewing container logs:"
docker logs claude_dc --tail 20