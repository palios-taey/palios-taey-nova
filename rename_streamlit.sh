#!/bin/bash
# Script to rename streamlit.py to avoid import conflicts

echo "Fixing Claude DC import issues by renaming streamlit.py..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current streamlit.py
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
cp /home/computeruse/computer_use_demo/streamlit.py /home/computeruse/computer_use_demo/streamlit.py.bak_${TIMESTAMP}
echo "Created backup at /home/computeruse/computer_use_demo/streamlit.py.bak_${TIMESTAMP}"

# Rename the file to claude_ui.py to avoid circular imports
mv /home/computeruse/computer_use_demo/streamlit.py /home/computeruse/computer_use_demo/claude_ui.py
echo "Renamed streamlit.py to claude_ui.py"

# Create a launcher script
cat > /home/computeruse/launch_claude.py << 'EOF'
#!/usr/bin/env python3
"""
Launcher script for Claude Computer Use Demo.
This avoids the circular import by using a separate launcher file.
"""

import os
import subprocess
import sys

def main():
    # Set environment variables
    os.environ['CLAUDE_ENV'] = 'dev'
    
    # Get the path to the claude_ui.py file
    claude_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "computer_use_demo", "claude_ui.py")
    
    if not os.path.exists(claude_ui_path):
        print(f"ERROR: Claude UI file not found at {claude_ui_path}")
        return 1
        
    print(f"Starting Claude DC UI from {claude_ui_path}")
    
    # Launch the UI using streamlit
    result = subprocess.run([
        "python", "-m", "streamlit", "run", claude_ui_path,
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x /home/computeruse/launch_claude.py

echo "Created launcher script at /home/computeruse/launch_claude.py"
echo "To launch Claude DC, run:"
echo "cd /home/computeruse"
echo "python3 launch_claude.py"