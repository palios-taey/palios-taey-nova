#!/bin/bash
# Test runner for enhanced tests

# Set up environment
cd "$(dirname "$0")"
TESTING_AREA="$(pwd)"
export PYTHONPATH="$PYTHONPATH:$TESTING_AREA"

# Display header
echo "====================================================="
echo "Running Enhanced Tests for Claude DC Streaming Fix"
echo "====================================================="
echo "Current directory: $TESTING_AREA"
echo

# Make the test scripts executable
chmod +x enhanced_tests/test_loop.py

# Run the tests
echo "Running loop tests..."
cd enhanced_tests
python3 test_loop.py
TEST_RESULT=$?

# Display summary
echo 
echo "====================================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "All tests PASSED!"
    echo "The streaming fix is working correctly."
else
    echo "Some tests FAILED!"
    echo "Please check the logs above for details."
fi
echo "====================================================="