#!/bin/bash
# Restart script for Claude DC's Streamlit interface

set -e

echo "Starting Claude DC with Streaming Implementation..."

# Set correct working directory
cd /home/computeruse/computer_use_demo

# Check if streamlit is already running and kill it
STREAMLIT_PID=$(pgrep -f "streamlit run" || echo "")
if [ -n "$STREAMLIT_PID" ]; then
    echo "Stopping existing Streamlit process..."
    kill $STREAMLIT_PID
    sleep 2
fi

# Start streamlit in the background
echo "Starting Streamlit UI with streaming capabilities..."
nohup python -m streamlit run streamlit.py > streamlit.log 2>&1 &

# Wait a moment
sleep 2

# Check if it started correctly
if pgrep -f "streamlit run" > /dev/null; then
    echo "✅ Claude DC's Streamlit UI is now running with streaming capabilities!"
    echo "You can access it through the normal UI interface."
    echo ""
    echo "To check the status of the streaming implementation:"
    echo "1. Look for the Streaming Status section in the sidebar"
    echo "2. Check streamlit.log for any errors: tail -f streamlit.log"
    echo ""
    echo "If you need to roll back:"
    echo "Restore from backup at: /home/computeruse/computer_use_demo_backups/20250506_234947"
else
    echo "❌ Failed to start Claude DC's Streamlit UI"
    echo "Check streamlit.log for errors"
fi