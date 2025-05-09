#!/bin/bash
# Script to update the Anthropic SDK to the required version

# Set up color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   Updating Anthropic SDK to v0.50.0${NC}"
echo -e "${BLUE}===================================================${NC}"

# Check current version
CURRENT_VERSION=$(pip show anthropic 2>/dev/null | grep Version | awk '{print $2}')

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${YELLOW}Anthropic SDK not installed. Installing version 0.50.0...${NC}"
else
    echo -e "${YELLOW}Current Anthropic SDK version: $CURRENT_VERSION${NC}"
    echo -e "${YELLOW}Uninstalling current version...${NC}"
    pip uninstall -y anthropic
fi

# Install required version
echo -e "${GREEN}Installing Anthropic SDK v0.50.0...${NC}"
pip install anthropic==0.50.0

# Verify installation
NEW_VERSION=$(pip show anthropic | grep Version | awk '{print $2}')
echo -e "${GREEN}Anthropic SDK updated to version: $NEW_VERSION${NC}"

if [ "$NEW_VERSION" != "0.50.0" ]; then
    echo -e "${RED}WARNING: Version mismatch detected. Expected 0.50.0, got $NEW_VERSION${NC}"
    echo -e "${RED}This may cause compatibility issues.${NC}"
else
    echo -e "${GREEN}Update successful!${NC}"
fi

echo -e "${BLUE}===================================================${NC}"
echo -e "${GREEN}Run the Streamlit app with: ./run_streamlit.sh${NC}"
echo -e "${BLUE}===================================================${NC}"