#!/bin/bash
# Script to run the Streamlit UI for Claude DC

# Set up color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}WARNING: ANTHROPIC_API_KEY environment variable not set!${NC}"
    echo "To set it, run: export ANTHROPIC_API_KEY=your_api_key"
fi

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   Starting Claude DC Streamlit UI${NC}"
echo -e "${BLUE}===================================================${NC}"
echo -e "${GREEN}Using Streamlit version: $(streamlit --version)${NC}"
echo -e "${GREEN}Using Python: $(python --version)${NC}"

# Start Streamlit
echo -e "${BLUE}Starting Streamlit server...${NC}"
echo -e "${GREEN}Using the new streamlit.py implementation${NC}"
streamlit run streamlit.py