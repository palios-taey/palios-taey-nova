#!/bin/bash
# Script to launch Claude DC directly from the test environment

echo "Setting environment variables for Claude DC..."
export CLAUDE_ENV=dev

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    # Try to read from file
    if [ -f "$HOME/.anthropic/api_key" ]; then
        export ANTHROPIC_API_KEY=$(cat $HOME/.anthropic/api_key)
    else
        echo "Please enter your Anthropic API key:"
        read API_KEY
        mkdir -p $HOME/.anthropic
        echo "$API_KEY" > $HOME/.anthropic/api_key
        export ANTHROPIC_API_KEY="$API_KEY"
    fi
fi

# First try to start from test environment
if [ -d "/home/computeruse/test_environment" ] && [ -f "/home/computeruse/test_environment/streamlit.py" ]; then
    echo "Starting Claude DC from test environment..."
    cd /home/computeruse/test_environment
    python3 -m streamlit run streamlit.py --server.port=8501 --server.address=0.0.0.0
    exit 0
fi

# Fall back to computer_use_demo if test environment doesn't exist
if [ -d "/home/computeruse/computer_use_demo" ] && [ -f "/home/computeruse/computer_use_demo/streamlit.py" ]; then
    echo "Starting Claude DC from computer_use_demo..."
    cd /home/computeruse/computer_use_demo
    python3 -m streamlit run streamlit.py --server.port=8501 --server.address=0.0.0.0
    exit 0
fi

# If neither environment exists, show error
echo "ERROR: No valid Claude DC environment found!"
echo "Please run the setup script first to create a valid environment."
exit 1