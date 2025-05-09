#!/bin/bash
# Script to check if required ports are accessible

echo "Checking important ports for Claude DC..."

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    
    # Try netstat first
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ Port $port ($service) is in use"
        
        # Try to get the process using the port
        local pid=$(netstat -tuln | grep ":$port " | awk '{print $7}' | cut -d '/' -f 1)
        if [ -n "$pid" ]; then
            echo "   Process: $(ps -p $pid -o comm=)"
        fi
    else
        echo "❌ Port $port ($service) is not in use"
    fi
    
    # Try curl to check if the port responds
    if curl -s -m 1 http://localhost:$port >/dev/null 2>&1; then
        echo "✅ Port $port ($service) responds to HTTP requests"
    else
        echo "❌ Port $port ($service) does not respond to HTTP requests"
    fi
    
    echo ""
}

# Check important ports
check_port 8501 "Streamlit"
check_port 8080 "Demo UI"
check_port 6080 "VNC"

# Show all listening ports
echo "All listening ports:"
netstat -tuln | grep "LISTEN"