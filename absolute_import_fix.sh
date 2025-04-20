#!/bin/bash
# Fix imports using absolute paths instead of relative imports

echo "Fixing imports to use absolute paths..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p /home/computeruse/backups
cp /home/computeruse/computer_use_demo/loop.py /home/computeruse/backups/loop.py.bak_${TIMESTAMP}
cp /home/computeruse/computer_use_demo/claude_ui.py /home/computeruse/backups/claude_ui.py.bak_${TIMESTAMP}
echo "Created backups in /home/computeruse/backups/"

# Update loop.py to use absolute imports
sed -i 's/from .tools import/from computer_use_demo.tools import/g' /home/computeruse/computer_use_demo/loop.py

# Update claude_ui.py to use absolute imports
sed -i 's/from loop import/from computer_use_demo.loop import/g' /home/computeruse/computer_use_demo/claude_ui.py

# Create a new launch script that properly sets up Python path
cat > /home/computeruse/launch_fixed.py << 'LAUNCHEOF'
#!/usr/bin/env python3
"""
Fixed launcher for Claude DC that properly sets up Python path.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('launch_fixed')

def main():
    """Set up environment properly and launch Streamlit."""
    # Set environment variables
    os.environ['CLAUDE_ENV'] = 'dev'
    
    # Make sure computer_use_demo is in Python path
    computer_use_path = "/home/computeruse/computer_use_demo"
    parent_dir = os.path.dirname(computer_use_path)
    
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        logger.info(f"Added {parent_dir} to Python path")
    
    # Get path to claude_ui.py
    claude_ui_path = os.path.join(computer_use_path, "claude_ui.py")
    
    if not os.path.exists(claude_ui_path):
        logger.error(f"Claude UI file not found at {claude_ui_path}")
        return 1
    
    logger.info(f"Starting Claude DC UI from {claude_ui_path}")
    
    # Run with subprocess to ensure environment is properly set
    cmd = [
        sys.executable,
        "-m", "streamlit", "run", claude_ui_path,
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = parent_dir + ":" + env.get("PYTHONPATH", "")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=True
        )
        return result.returncode
    except Exception as e:
        logger.error(f"Error launching Streamlit: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
LAUNCHEOF

chmod +x /home/computeruse/launch_fixed.py

# Create simple package file to make imports work
touch /home/computeruse/computer_use_demo/__init__.py

echo "Fixed imports and created new launcher!"
echo ""
echo "To launch Claude DC with fixed imports:"
echo "cd /home/computeruse"
echo "python3 launch_fixed.py"
echo ""
echo "This launcher sets up the Python path correctly to handle imports."