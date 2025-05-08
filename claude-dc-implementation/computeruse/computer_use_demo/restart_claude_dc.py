#!/usr/bin/env python3
"""
Script to restart Claude DC with streaming capabilities.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def main():
    """
    Restart Claude DC with streaming capabilities.
    """
    print("Restarting Claude DC with streaming capabilities...")
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    # Kill any existing streamlit processes
    try:
        subprocess.run(["pkill", "-f", "streamlit"], check=False)
        print("Stopped existing Streamlit processes.")
        time.sleep(2)  # Give processes time to stop
    except Exception as e:
        print(f"Error stopping Streamlit: {e}")
    
    # Start streamlit with the proper module
    cmd = ["python", "-m", "streamlit", "run", "streamlit.py"]
    print(f"Starting Streamlit with command: {' '.join(cmd)}")
    
    try:
        # Using subprocess.Popen to run in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait a moment to check if the process started successfully
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Claude DC has been successfully restarted with streaming capabilities!")
            print("You can access it through your web browser.")
            return 0
        else:
            out, err = process.communicate()
            print(f"❌ Failed to start Claude DC. Process exited with code {process.returncode}")
            print(f"Output: {out}")
            print(f"Error: {err}")
            return 1
    except Exception as e:
        print(f"❌ Error starting Claude DC: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())