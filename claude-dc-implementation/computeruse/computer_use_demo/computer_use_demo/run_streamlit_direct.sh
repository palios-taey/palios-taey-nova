#!/bin/bash
# Direct Streamlit launch script that doesn't use background processes
# This helps us see exactly what's happening with Streamlit

set -e

# Default port
PORT=8501

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --port)
      PORT="$2"
      shift
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --port PORT     Port to run Streamlit on (default: 8501)"
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

echo "Starting Streamlit directly on port $PORT..."

# Kill any existing Streamlit processes
pkill -f "streamlit run" || echo "No existing Streamlit processes"

# Set environment variables for Streamlit
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_ENABLE_CORS=true
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Run a simple test app to verify Streamlit is working
echo "#!/usr/bin/env python3
import streamlit as st

st.title('Claude DC Streaming Test')
st.write('If you can see this, Streamlit is working correctly!')

# Add a simple interactive element
if st.button('Click me'):
    st.success('Button clicked!')
" > test_app.py

# Run the test app
echo "Running test_app.py on port $PORT..."
echo "You should be able to access it at: http://localhost:$PORT"
echo "Press Ctrl+C to exit"

python -m streamlit run test_app.py