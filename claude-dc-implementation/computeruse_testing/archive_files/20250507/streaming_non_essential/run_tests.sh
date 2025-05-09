#!/bin/bash
# Test suite for the streaming implementation

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color

echo -e "${YELLOW}===== Streaming Implementation Test Suite =====${NC}"

# First, verify setup
echo -e "\n${YELLOW}Verifying setup...${NC}"
./verify_setup.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Setup verification failed. Please fix the issues before continuing.${NC}"
    exit 1
fi

# Run the non-interactive minimal test
echo -e "\n${YELLOW}Running non-interactive minimal streaming test...${NC}"
read -p "Press Enter to continue or Ctrl+C to cancel..."
./non_interactive_test.py

# Run the non-interactive tool streaming test
echo -e "\n${YELLOW}Running non-interactive tool streaming test...${NC}"
read -p "Press Enter to continue or Ctrl+C to cancel..."
./non_interactive_tool_test.py

# Run the integration test with different phases
for phase in phase1 phase2 phase3; do
    echo -e "\n${YELLOW}Running integration test - Phase: ${phase}...${NC}"
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    ./integration_test.py --phase "${phase}"
done

echo -e "\n${GREEN}All tests completed!${NC}"
echo -e "${YELLOW}The streaming implementation is ready for integration.${NC}"