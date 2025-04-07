#!/bin/bash

# PALIOS AI OS Deployment Script
# This script deploys and starts the PALIOS AI OS with all components

# Display banner
echo "┌───────────────────────────────────────────────────────────┐"
echo "│                      PALIOS AI OS                         │"
echo "│                                                           │"
echo "│  Pattern-Aligned Learning & Intuition Operating System    │"
echo "│                Truth As Earth Yields                      │"
echo "│                                                           │"
echo "│      Bach-Inspired Structure · Golden Ratio Harmony       │"
echo "└───────────────────────────────────────────────────────────┘"
echo ""

# Configuration
MCP_PORT=8001
DASHBOARD_PORT=8502  # Changed from 8080 to 8502
INSTALL_DIR="$(pwd)"
GOLDEN_RATIO=1.618033988749895

# Set current directory
cd "$INSTALL_DIR"

# Create necessary directories
mkdir -p palios_ai_os/{trust/trust_storage,edge/local_storage,mcp/mcp_storage}
mkdir -p templates
mkdir -p static

echo "Installing dependencies..."
# Check if requirements.txt exists and install dependencies
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
else
    # Install core dependencies if requirements.txt not found
    pip install fastapi uvicorn numpy scipy matplotlib pandas pydantic jinja2 requests
fi

echo "Installing complete. Starting PALIOS AI OS..."

# Start the system
echo "Golden Ratio (φ): $GOLDEN_RATIO"
echo "Starting PALIOS AI OS..."

# Find Python executable path
PYTHON_PATH=$(which python3 || which python)
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python executable not found. Please ensure Python is installed and in your PATH."
    exit 1
fi

# Start the dashboard in the background
echo "Starting Dashboard on port $DASHBOARD_PORT..."
sed -i "s/port=8080/port=$DASHBOARD_PORT/g" dashboard.py  # Update port in dashboard.py
$PYTHON_PATH dashboard.py & 
DASHBOARD_PID=$!

# Start the main PALIOS AI OS in the background
echo "Starting PALIOS AI OS core on port $MCP_PORT..."
$PYTHON_PATH start_palios.py &
MAIN_PID=$!

echo ""
echo "PALIOS AI OS is now running:"
echo " - PALIOS AI OS Core: http://localhost:$MCP_PORT"
echo " - Dashboard:        http://localhost:$DASHBOARD_PORT"
echo ""
echo "Press Ctrl+C to stop all services"

# Handle graceful shutdown
trap 'echo "Shutting down PALIOS AI OS..."; kill $DASHBOARD_PID $MAIN_PID; echo "Shutdown complete."; exit 0' INT

# Wait for user to press Ctrl+C
wait
