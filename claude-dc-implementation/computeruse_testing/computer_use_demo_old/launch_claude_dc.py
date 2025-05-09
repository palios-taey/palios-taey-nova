#!/usr/bin/env python3
"""
Launcher for Claude DC UI.
This script starts the Claude DC user interface with all needed dependencies.
"""

import os
import sys
import subprocess
import logging
import time
import shutil

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/launcher_debug.log"),  # Changed to a more visible location
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("launcher")

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Make sure logs directory exists
    logs_dir = os.path.join(current_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logger.debug(f"Ensuring logs directory exists: {logs_dir}")
    
    # Kill any existing Streamlit processes
    try:
        logger.debug("Checking for existing Streamlit processes")
        kill_cmd = "pkill -f streamlit"
        subprocess.run(kill_cmd, shell=True, stderr=subprocess.PIPE)
        logger.debug("Waiting 2 seconds for processes to terminate")
        time.sleep(2)  # Give processes time to terminate
    except Exception as e:
        logger.debug(f"Error killing existing processes (can be ignored): {e}")
    
    # Update claude_ui.py logging to use the logs directory
    try:
        ui_file = os.path.join(current_dir, "claude_ui.py")
        logger.debug(f"Updating logging in {ui_file}")
        
        with open(ui_file, 'r') as f:
            content = f.read()
        
        # Update the logging configuration
        if "streamlit.log" in content:
            modified_content = content.replace(
                'logging.FileHandler("streamlit.log")',
                'logging.FileHandler("logs/streamlit_debug.log")'
            )
            with open(ui_file, 'w') as f:
                f.write(modified_content)
            logger.debug("Updated logging configuration in claude_ui.py")
    except Exception as e:
        logger.error(f"Error updating claude_ui.py: {e}")
    
    # Ensure all requirements are installed
    try:
        logger.info("Checking requirements...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", os.path.join(current_dir, "requirements.txt")],
            check=True,
            stdout=subprocess.PIPE,  # Capture output
            stderr=subprocess.PIPE
        )
        logger.info("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing requirements: {e}")
        logger.error(f"Stderr: {e.stderr.decode('utf-8')}")
        print(f"Error installing requirements: {e}")
        return 1
    
    # Ensure streamlit is in the system path
    try:
        streamlit_path = subprocess.run(
            ["which", "streamlit"], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        ).stdout.decode().strip()
        logger.debug(f"Found streamlit at: {streamlit_path}")
    except subprocess.CalledProcessError:
        logger.error("Streamlit not found in PATH. Installing explicitly...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "streamlit==1.44.0", "--force-reinstall"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("Streamlit installed explicitly")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing streamlit: {e}")
            logger.error(f"Stderr: {e.stderr.decode('utf-8')}")
            print(f"Error installing streamlit: {e}")
            return 1
    
    # Launch streamlit with the UI file
    ui_path = os.path.join(current_dir, "claude_ui.py")
    logger.debug(f"Claude UI file path: {ui_path}")
    
    if not os.path.exists(ui_path):
        logger.error(f"UI file not found: {ui_path}")
        print(f"Error: UI file not found: {ui_path}")
        return 1
    
    # Add env var to help with debugging
    my_env = os.environ.copy()
    my_env["STREAMLIT_LOGGER_LEVEL"] = "debug"
    
    cmd = [sys.executable, "-m", "streamlit", "run", ui_path, "--logger.level=debug"]
    
    logger.info(f"Launching Claude DC UI with command: {' '.join(cmd)}")
    print(f"Launching Claude DC UI: {' '.join(cmd)}")
    
    # Execute streamlit
    try:
        subprocess.run(cmd, check=True, env=my_env)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error launching Claude DC UI: {e}")
        print(f"Error launching Claude DC UI: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Launcher interrupted by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
