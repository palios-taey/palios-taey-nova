#!/bin/bash
# Background launcher for Claude DC's Streamlit interface with streaming

set -e

# Kill any existing Streamlit process
pkill -f "streamlit run" 2>/dev/null || echo "No existing Streamlit process"

# Set environment variables for Streamlit
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=true

# Change to the computer_use_demo directory
cd /home/computeruse/computer_use_demo

# Remove any old logs
rm -f streamlit_streaming.log

# Start Streamlit in the background
nohup streamlit run streamlit_streaming.py > streamlit_streaming.log 2>&1 &

# Wait a moment for it to start
sleep 5

# Check if it started correctly
if pgrep -f "streamlit run" > /dev/null; then
    echo "✅ Claude DC's Streamlit UI is now running with streaming!"
    echo "Access URL: http://localhost:8501"
    echo ""
    echo "To check the status:"
    echo "tail -f streamlit_streaming.log"
    echo ""
    echo "To stop the process:"
    echo "pkill -f 'streamlit run'"
else
    echo "❌ Failed to start Claude DC's Streamlit UI"
    echo "Check streamlit_streaming.log for errors"
fi