#!/bin/bash
# Comprehensive test suite runner for Claude DC implementation

# Set up color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}ERROR: ANTHROPIC_API_KEY environment variable not set!${NC}"
    echo "Please set it with: export ANTHROPIC_API_KEY=your_api_key"
    exit 1
fi

# Create a directory for test artifacts
mkdir -p test_results

echo -e "\n${BLUE}===================================================${NC}"
echo -e "${BLUE}   Running Claude DC Implementation Test Suite${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Function to run a test and log results
run_test() {
    test_name=$1
    test_command=$2
    test_description=$3
    
    echo -e "${YELLOW}[$test_name]${NC} $test_description"
    echo "Running: $test_command"
    
    # Run the test and capture output
    output_file="test_results/${test_name}_output.log"
    start_time=$(date +%s.%N)
    eval "$test_command" > "$output_file" 2>&1
    exit_code=$?
    end_time=$(date +%s.%N)
    
    # Calculate duration
    duration=$(echo "$end_time - $start_time" | bc)
    duration=$(printf "%.2f" $duration)
    
    # Check result
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC} in ${duration}s"
        echo "$test_name: PASSED ($duration seconds)" >> test_results/summary.txt
    else
        echo -e "${RED}❌ FAILED${NC} in ${duration}s - see $output_file for details"
        echo "$test_name: FAILED ($duration seconds)" >> test_results/summary.txt
        cat "$output_file" | tail -10
    fi
    echo ""
    
    return $exit_code
}

# Initialize test summary
echo "Claude DC Test Results - $(date)" > test_results/summary.txt
echo "=========================================" >> test_results/summary.txt

# 1. Basic Verification Tests
run_test "verify_imports" "python verify.py --imports" "Checking import dependencies"
import_result=$?

# If imports fail, don't bother running other tests
if [ $import_result -ne 0 ]; then
    echo -e "${RED}Critical import dependencies failed. Skipping remaining tests.${NC}"
    exit 1
fi

# 2. API Connectivity Test
run_test "verify_api" "python verify.py --api" "Testing API connectivity"
api_result=$?

# 3. Tool Implementation Tests
run_test "tool_tests" "python test_tools.py" "Testing tool implementations"
tools_result=$?

# 4. Streaming Implementation Tests
run_test "streaming_tests" "python test_streaming.py" "Testing streaming implementation"
streaming_result=$?

# 5. Generate final report
echo -e "\n${BLUE}===================================================${NC}"
echo -e "${BLUE}   Test Suite Summary${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Calculate overall status
overall_status=0
if [ $import_result -ne 0 ] || [ $api_result -ne 0 ] || [ $tools_result -ne 0 ] || [ $streaming_result -ne 0 ]; then
    overall_status=1
fi

# Print summary
cat test_results/summary.txt

# Final verdict
echo -e "\n${BLUE}===================================================${NC}"
if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}   All tests PASSED! The implementation is ready.${NC}"
else
    echo -e "${RED}   Some tests FAILED. Please fix the issues.${NC}"
fi
echo -e "${BLUE}===================================================${NC}\n"

exit $overall_status