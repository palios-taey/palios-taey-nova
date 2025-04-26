#!/bin/bash
# Launcher for minimal Streamlit UI

echo "Starting minimal Claude DC UI..."

# First, kill any existing Streamlit processes
echo "Checking for existing Streamlit processes..."
pkill -f streamlit || echo "No existing Streamlit processes found"
sleep 1

# Run the basic test to make sure the API is working
echo "Testing API connectivity..."
python basic_stream_test.py

# Launch the Streamlit app
echo "Launching Streamlit UI..."
streamlit run minimal_streamlit.py