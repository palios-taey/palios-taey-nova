#\!/usr/bin/env python3
"""
Launch script for Claude DC Computer Use demo.
This script starts the Streamlit application in the computer_use_demo directory.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/computeruse/claude_dc.log'
)
logger = logging.getLogger('run_claude_dc')

def main():
    """Main function to start Claude DC."""
    # Determine the computer_use_demo directory
    computer_use_demo = "/home/computeruse/computer_use_demo"
    
    # Check if directory exists
    if not os.path.isdir(computer_use_demo):
        logger.error(f"Directory not found: {computer_use_demo}")
        print(f"ERROR: Directory not found: {computer_use_demo}")
        sys.exit(1)
    
    # Check if streamlit.py exists
    streamlit_path = os.path.join(computer_use_demo, "streamlit.py")
    if not os.path.isfile(streamlit_path):
        logger.error(f"Streamlit file not found: {streamlit_path}")
        print(f"ERROR: Streamlit file not found: {streamlit_path}")
        sys.exit(1)
    
    # Check for required environment variables
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable not set\!")
        print("WARNING: ANTHROPIC_API_KEY environment variable not set\!")
        # Continue anyway, Streamlit will show a field to enter it
    
    # Set the current working directory
    os.chdir(computer_use_demo)
    
    # Start the Streamlit application
    try:
        logger.info("Starting Claude DC Streamlit application...")
        print("Starting Claude DC Streamlit application...")
        
        # Run the Streamlit app
        subprocess.run(
            ["python", "-m", "streamlit", "run", "streamlit.py", "--server.port=8501", 
             "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        print(f"ERROR: Failed to start Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Claude DC stopped by user.")
        print("Claude DC stopped by user.")
    
    return 0

if __name__ == "__main__":
    main()
