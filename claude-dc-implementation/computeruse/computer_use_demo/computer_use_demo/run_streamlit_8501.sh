#!/bin/bash
# Streamlit launch script specifically targeting port 8501
# This is the port that the container is expecting

set -e

# Clear any existing streamlit processes
pkill -f "streamlit run" 2>/dev/null || echo "No existing Streamlit processes"

# Change to the computer_use_demo directory
cd /home/computeruse/computer_use_demo

# Create a simple test app first to verify basic functionality
cat > simple_test.py << 'EOF'
import streamlit as st

st.title("Basic Streamlit Test")
st.write("If you can see this, Streamlit is working at the basic level!")

if st.button("Click me"):
    st.success("Button clicked!")
EOF

echo "Starting a basic Streamlit test app on port 8501..."
echo "This is just to verify Streamlit works at all"
echo "Access at: http://localhost:8501"
echo ""
echo "Press Ctrl+C when you've verified it works"
echo "------------------------------------------"

# Run the simple test with explicit 8501 port
STREAMLIT_SERVER_PORT=8501 STREAMLIT_SERVER_ADDRESS=0.0.0.0 STREAMLIT_SERVER_HEADLESS=true streamlit run simple_test.py