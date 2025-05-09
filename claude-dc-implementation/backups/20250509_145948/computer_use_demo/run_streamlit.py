#!/usr/bin/env python3
"""
Script to run streamlit with the Claude DC implementation.
"""

import os
import sys
import subprocess
import time

def main():
    """Run the streamlit app with the Claude DC implementation."""
    print("Starting Claude DC with Streaming Implementation...")
    
    # Set correct working directory
    os.chdir('/home/computeruse/computer_use_demo')
    
    # Check if streamlit is already running and kill it
    try:
        output = subprocess.check_output(['pgrep', '-f', 'streamlit run']).decode().strip()
        if output:
            print("Stopping existing Streamlit process...")
            subprocess.run(['kill', output], check=False)
            time.sleep(2)
    except subprocess.CalledProcessError:
        # No streamlit process running, continue
        pass
    
    # Start streamlit
    print("Starting Streamlit UI with streaming capabilities...")
    try:
        # Run in foreground for testing
        subprocess.run([
            'python', '-m', 'streamlit', 'run', 
            '/home/computeruse/computer_use_demo/streamlit.py'
        ], check=True)
        
        print("✅ Claude DC's Streamlit UI is now running with streaming capabilities!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Claude DC's Streamlit UI. Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())