#!/usr/bin/env python3
"""
Simple direct launcher for Claude DC.
This script sets up the environment and launches Claude DC.
"""

import os
import sys
import subprocess
import time

def main():
    """Main launcher function."""
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set target directory
    claude_dc_dir = os.path.join(current_dir, "computer_use_demo")
    
    print(f"Starting Claude DC from {claude_dc_dir}")
    
    # Change to the Claude DC directory
    os.chdir(claude_dc_dir)
    
    # Set up the environment
    print("Setting up environment...")
    
    # Kill any existing Streamlit processes
    try:
        subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.PIPE)
        time.sleep(1)  # Wait for processes to terminate
    except Exception:
        pass
    
    # Install required packages
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return 1
    
    # Run the launcher
    print("Launching Claude DC...")
    
    # Adjust PYTHONPATH to avoid import conflicts
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = f"{claude_dc_dir}:{my_env.get('PYTHONPATH', '')}"
    
    # Launch Streamlit directly
    cmd = ["streamlit", "run", os.path.join(claude_dc_dir, "claude_ui.py")]
    
    # Print the command for debugging
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute streamlit
    try:
        subprocess.run(cmd, check=True, env=my_env)
    except KeyboardInterrupt:
        print("\nClaude DC stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error launching Claude DC: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())