#!/bin/bash
# Simple test runner for streaming implementation tests

# Set up colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================${NC}"
echo -e "${BLUE}  Claude DC Streaming Tests Runner  ${NC}"
echo -e "${BLUE}===================================${NC}"

# Check if API key is available
SECRETS_FILE="/home/computeruse/secrets/palios-taey-secrets.json"
if [ ! -f "$SECRETS_FILE" ]; then
    echo -e "${RED}Error: Secrets file not found at $SECRETS_FILE${NC}"
    echo "Please ensure the API key is properly configured."
    exit 1
fi

# Menu function
show_menu() {
    echo -e "\n${YELLOW}Available Test Options:${NC}"
    echo "1) Run Direct Bash Tool Test"
    echo "2) Run Full Streaming Test Suite"
    echo "3) Run Single Streaming Test"
    echo "4) Run Minimal Test"
    echo "q) Quit"
    echo -e "\nEnter your choice:"
}

# Main execution
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            echo -e "\n${YELLOW}Running Direct Bash Tool Test...${NC}"
            echo -e "${BLUE}-------------------------------------${NC}"
            ./test_bash_tool_direct.py
            echo -e "${BLUE}-------------------------------------${NC}"
            echo -e "${GREEN}Direct Bash Tool Test completed.${NC}"
            ;;
        2)
            echo -e "\n${YELLOW}Running Full Streaming Test Suite...${NC}"
            echo -e "${BLUE}-------------------------------------${NC}"
            ./test_fixed_streaming.py
            echo -e "${BLUE}-------------------------------------${NC}"
            echo -e "${GREEN}Full Streaming Test Suite completed.${NC}"
            ;;
        3)
            echo -e "\n${YELLOW}Which test number would you like to run?${NC}"
            echo "1. Simple query (no tool use)"
            echo "2. Basic bash command (ls -la)"
            echo "3. Complex bash command (ps and grep)"
            echo "4. Find command"
            echo "5. Cat and grep command"
            read -r test_num
            
            if [[ "$test_num" =~ ^[1-5]$ ]]; then
                echo -e "\n${YELLOW}Running Streaming Test #$test_num...${NC}"
                echo -e "${BLUE}-------------------------------------${NC}"
                ./test_fixed_streaming.py "$test_num"
                echo -e "${BLUE}-------------------------------------${NC}"
                echo -e "${GREEN}Streaming Test #$test_num completed.${NC}"
            else
                echo -e "${RED}Invalid test number. Please select 1-5.${NC}"
            fi
            ;;
        4)
            echo -e "\n${YELLOW}Running Minimal Test...${NC}"
            echo -e "${BLUE}-------------------------------------${NC}"
            if [ -f "./test_streaming_minimal.py" ]; then
                python ./test_streaming_minimal.py
            else
                echo -e "${RED}Minimal test script not found.${NC}"
            fi
            echo -e "${BLUE}-------------------------------------${NC}"
            echo -e "${GREEN}Minimal Test completed.${NC}"
            ;;
        q|Q)
            echo -e "${GREEN}Exiting test runner. Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            ;;
    esac
done