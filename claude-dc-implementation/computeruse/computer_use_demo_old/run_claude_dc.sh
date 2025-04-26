#!/bin/bash
# Simplified launcher for Claude DC

# Log file location
LOG_FILE="/home/computeruse/claude_dc_run.log"

echo "Starting Claude DC..."
echo "$(date) Starting Claude DC" > $LOG_FILE

# First, check the API directly to see which parameter style works
echo "Testing API parameters..."
cd /home/computeruse
python minimal_direct_claude.py >> $LOG_FILE 2>&1

# Regardless of test results, try to run the actual application
echo "Starting Claude DC application..."
cd /home/computeruse/computer_use_demo

# Make sure streamlit is installed
pip install -r requirements.txt >> $LOG_FILE 2>&1

# Launch the application
streamlit run claude_ui.py

echo "Claude DC stopped at $(date)" >> $LOG_FILE