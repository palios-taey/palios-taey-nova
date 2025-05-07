#!/bin/bash
# Master deployment script for streaming implementation

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

echo -e "${YELLOW}===== Streaming Implementation Deployment =====${NC}"

# Create backup directory
BACKUP_DIR="/home/computeruse/computer_use_demo_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Create backup of current implementation
echo -e "\n${YELLOW}Creating full backup...${NC}"
cp -r /home/computeruse/computer_use_demo/* "$BACKUP_DIR"
echo -e "${GREEN}Full backup created successfully${NC}"

# Create deploy directory if it doesn't exist
mkdir -p /home/computeruse/computer_use_demo/deploy

# Verify setup before deployment
echo -e "\n${YELLOW}Verifying environment setup...${NC}"
python /home/computeruse/computer_use_demo/streaming/verify_setup.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Setup verification failed. Aborting deployment.${NC}"
    exit 1
fi

# Deploy non-critical files first
echo -e "\n${YELLOW}Deploying non-critical files...${NC}"

# Ensure directories exist
mkdir -p /home/computeruse/computer_use_demo/streaming/tools
mkdir -p /home/computeruse/computer_use_demo/streaming/models
mkdir -p /home/computeruse/computer_use_demo/streaming/logs

# Make deploy scripts executable
chmod +x /home/computeruse/computer_use_demo/deploy/deploy_loop.py
chmod +x /home/computeruse/computer_use_demo/deploy/deploy_streamlit.py

# Deploy critical files
echo -e "\n${YELLOW}Deploying critical files with DCCC...${NC}"
echo "These files must be deployed by DCCC as they require careful modification."

# Execute the deployment scripts
echo -e "\n${YELLOW}Running loop.py deployment script...${NC}"
python /home/computeruse/computer_use_demo/deploy/deploy_loop.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to deploy loop.py. Aborting.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Running streamlit.py deployment script...${NC}"
python /home/computeruse/computer_use_demo/deploy/deploy_streamlit.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to deploy streamlit.py. Aborting.${NC}"
    exit 1
fi

# Verify deployment
echo -e "\n${YELLOW}Verifying deployment...${NC}"
if [ -f "/home/computeruse/computer_use_demo/loop.py" ] && \
   [ -f "/home/computeruse/computer_use_demo/streamlit.py" ] && \
   [ -f "/home/computeruse/computer_use_demo/streaming_integration.py" ]; then
    echo -e "${GREEN}Deployment verified. All files in place.${NC}"
else
    echo -e "${RED}Deployment verification failed. Some files are missing.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}You can now test the streaming implementation with:${NC}"
echo -e "  cd /home/computeruse/computer_use_demo"
echo -e "  python -m streamlit run streamlit.py"
echo -e "\n${YELLOW}To roll back, restore from backup directory:${NC}"
echo -e "  $BACKUP_DIR"