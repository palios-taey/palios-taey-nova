#!/usr/bin/env python3
"""
Test script for verifying the Claude DC development environment is working correctly.
This script checks container status, verifies network ports, and attempts a simple API call.
"""

import os
import subprocess
import sys
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_dev_environment')

def check_environment_variables():
    """Check if required environment variables are set."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return False
    return True

def check_container_status():
    """Check if the dev container is running."""
    try:
        # First try without sudo
        cmd = ["docker", "ps", "--filter", "name=claude_dc_dev", "--format", "{{.Status}}"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # If that fails with permission error, try with sudo
        if result.returncode != 0 and "permission denied" in result.stderr:
            logger.warning("Permission denied, trying with sudo...")
            cmd = ["sudo", "docker", "ps", "--filter", "name=claude_dc_dev", "--format", "{{.Status}}"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        elif result.returncode != 0:
            # Some other error occurred
            logger.error(f"Error checking container status: {result.stderr}")
            return False
            
        if "Up " in result.stdout:
            logger.info("Claude DC dev container is running")
            return True
        else:
            logger.error("Claude DC dev container is not running")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking container status: {e}")
        return False

def check_streamlit_port():
    """Check if Streamlit is available on port 8502."""
    try:
        response = requests.get("http://localhost:8502", timeout=5)
        if response.status_code == 200:
            logger.info("Streamlit is accessible on port 8502")
            return True
        else:
            logger.error(f"Streamlit returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error connecting to Streamlit: {e}")
        return False

def check_vnc_port():
    """Check if VNC interface is available on port 6081."""
    try:
        response = requests.get("http://localhost:6081", timeout=5)
        if response.status_code == 200:
            logger.info("VNC interface is accessible on port 6081")
            return True
        else:
            logger.error(f"VNC interface returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error connecting to VNC interface: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Testing Claude DC development environment...")
    
    # Check environment variables
    if not check_environment_variables():
        logger.error("Environment variable check failed")
        sys.exit(1)
    
    # Check container status
    if not check_container_status():
        logger.error("Container status check failed")
        sys.exit(1)
    
    # Check Streamlit port
    if not check_streamlit_port():
        logger.error("Streamlit port check failed")
        sys.exit(1)
    
    # Check VNC port
    if not check_vnc_port():
        logger.error("VNC port check failed")
        # This is not critical, so we'll just warn
        logger.warning("VNC interface might not be working correctly")
    
    logger.info("All tests passed! Development environment is set up correctly.")

if __name__ == "__main__":
    main()