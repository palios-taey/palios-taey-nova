#!/bin/bash
# Deployment script for Claude DC GROK implementation

# Set up color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOURCE_DIR="/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo_grok"
TARGET_DIR="/home/computeruse/computer_use_demo"
BACKUP_DIR="/home/computeruse/computer_use_demo_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "\n${BLUE}===================================================${NC}"
echo -e "${BLUE}   Claude DC GROK Implementation Deployment${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}ERROR: Source directory $SOURCE_DIR not found!${NC}"
    exit 1
fi

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Target directory $TARGET_DIR not found, creating it...${NC}"
    mkdir -p "$TARGET_DIR"
fi

# 1. Run verification tests
echo -e "${YELLOW}Running verification tests...${NC}"
cd "$SOURCE_DIR"
./run_tests.sh
test_result=$?

if [ $test_result -ne 0 ]; then
    echo -e "${RED}Verification tests failed. Aborting deployment.${NC}"
    echo -e "${YELLOW}Please fix the issues and try again.${NC}"
    exit 1
fi

# 2. Create backup of current production
echo -e "${YELLOW}Creating backup of current production environment...${NC}"
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="$BACKUP_DIR/computer_use_demo_backup_$TIMESTAMP"

if [ -d "$TARGET_DIR" ]; then
    cp -r "$TARGET_DIR" "$BACKUP_PATH"
    echo -e "${GREEN}Backup created at: $BACKUP_PATH${NC}"
else
    echo -e "${YELLOW}No existing production environment to backup.${NC}"
fi

# 3. Deploy new implementation
echo -e "${YELLOW}Deploying new implementation...${NC}"
rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/"
deploy_result=$?

if [ $deploy_result -ne 0 ]; then
    echo -e "${RED}Deployment failed. Restoring from backup...${NC}"
    rm -rf "$TARGET_DIR"
    cp -r "$BACKUP_PATH" "$TARGET_DIR"
    echo -e "${GREEN}Restored from backup.${NC}"
    exit 1
fi

# 4. Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
cd "$TARGET_DIR"
python verify.py --imports
verify_result=$?

if [ $verify_result -ne 0 ]; then
    echo -e "${RED}Deployment verification failed. Consider rolling back.${NC}"
    echo -e "${YELLOW}To rollback, run: cp -r $BACKUP_PATH/* $TARGET_DIR/${NC}"
else
    echo -e "${GREEN}Deployment verified successfully!${NC}"
fi

# 5. Final status
echo -e "\n${BLUE}===================================================${NC}"
if [ $verify_result -eq 0 ]; then
    echo -e "${GREEN}   Deployment SUCCESSFUL!${NC}"
    echo -e "${GREEN}   New implementation is ready for use.${NC}"
    
    echo -e "${YELLOW}   To start Streamlit UI, run:${NC}"
    echo -e "   cd $TARGET_DIR"
    echo -e "   streamlit run streamlit_app.py"
else
    echo -e "${RED}   Deployment encountered issues.${NC}"
    echo -e "${YELLOW}   Consider rolling back with:${NC}"
    echo -e "   cp -r $BACKUP_PATH/* $TARGET_DIR/"
fi
echo -e "${BLUE}===================================================${NC}\n"

exit $verify_result