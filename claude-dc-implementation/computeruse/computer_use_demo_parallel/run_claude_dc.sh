#!/bin/bash
# Orchestration script for Claude DC's Streamlit interface
# Allows switching between streaming and non-streaming modes
# IMPORTANT: This script is specifically designed for the container setup
# where port 8501 is exposed for Streamlit

set -e

# Default mode is streaming
MODE="streaming"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --no-streaming)
      MODE="non-streaming"
      shift
      ;;
    --streaming)
      MODE="streaming"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --streaming     Run Claude DC with streaming capabilities (default)"
      echo "  --no-streaming  Run Claude DC without streaming capabilities"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Try '$0 --help' for more information."
      exit 1
      ;;
  esac
done

echo "Starting Claude DC in $MODE mode..."

# Set correct working directory
cd /home/computeruse/computer_use_demo

# Check if streamlit is already running and kill it
STREAMLIT_PID=$(pgrep -f "streamlit run" || echo "")
if [ -n "$STREAMLIT_PID" ]; then
    echo "Stopping existing Streamlit process..."
    kill $STREAMLIT_PID
    sleep 2
fi

# Define environment variables for Streamlit
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=true

# Start streamlit with the appropriate entry point
if [ "$MODE" == "streaming" ]; then
    # Remove any old logs
    rm -f streamlit_streaming.log

    echo "Starting Streamlit UI with streaming capabilities..."
    echo "Using port: $STREAMLIT_SERVER_PORT"
    echo "Access URL: http://localhost:8501"
    
    # Run directly in foreground so we can see output
    streamlit run streamlit_streaming.py
else
    # Remove any old logs
    rm -f claude_dc_ui.log
    
    echo "Starting Streamlit UI without streaming capabilities..."
    echo "Using port: $STREAMLIT_SERVER_PORT"
    echo "Access URL: http://localhost:8501"
    
    # Run directly in foreground so we can see output
    streamlit run claude_dc_ui.py
fi