#!/usr/bin/env python3
"""
Test script for verifying the Claude DC development environment is working correctly.
This script checks either container status or local environment, verifies code functionality,
and produces a test report.
"""

import os
import subprocess
import sys
import time
import requests
import logging
import argparse
import shutil
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_dev_environment')

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test Claude DC development environment')
parser.add_argument('--local', action='store_true', help='Run tests in local mode without Docker')
parser.add_argument('--test-dir', type=str, default='/home/computeruse/test_environment', 
                    help='Directory containing test environment files')
args = parser.parse_args()

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

def check_local_environment():
    """Check if the local test environment is set up correctly."""
    test_dir = Path(args.test_dir)
    
    # Check if test directory exists
    if not test_dir.exists():
        logger.error(f"Test directory {test_dir} does not exist")
        return False
    
    # Check for critical files
    required_files = ["loop.py", "streamlit.py"]
    for file in required_files:
        if not (test_dir / file).exists():
            logger.error(f"Required file {file} not found in test directory")
            return False
    
    # Try importing the loop module to verify syntax
    try:
        loop_path = str(test_dir / "loop.py")
        spec = importlib.util.spec_from_file_location("loop", loop_path)
        loop_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loop_module)
        logger.info("Successfully imported loop.py - syntax check passed")
    except Exception as e:
        logger.error(f"Error importing loop.py: {e}")
        return False
    
    # Check if streamlit is installed
    try:
        import streamlit
        logger.info(f"Streamlit {streamlit.__version__} is installed")
    except ImportError:
        logger.error("Streamlit not installed. Please install it with: pip install streamlit")
        return False
    
    # Try to run the streamlit app in a separate process (and kill it right away)
    try:
        streamlit_path = str(test_dir / "streamlit.py")
        process = subprocess.Popen(
            ["python", "-m", "streamlit", "run", streamlit_path, "--server.port=8502", "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Give it a moment to start or fail
        time.sleep(2)
        # Check if process is still running (if it crashed immediately, we'll know)
        if process.poll() is not None:
            # It failed
            stdout, stderr = process.communicate()
            logger.error(f"Streamlit app failed to start: {stderr.decode()}")
            return False
        else:
            # It seems to be running, kill it
            process.terminate()
            logger.info("Streamlit app could start successfully (test run only)")
            return True
    except Exception as e:
        logger.error(f"Error testing Streamlit app: {e}")
        return False

def check_enhanced_features():
    """Check if the enhanced features from Phase 2 are properly implemented."""
    logger.info("Checking for Phase 2 enhancements...")
    
    # For a local test, we examine the code directly
    test_dir = Path(args.test_dir)
    
    # Check for streaming implementation
    try:
        with open(test_dir / "loop.py", "r") as f:
            loop_content = f.read()
        
        features = {
            "streaming": "stream=True" in loop_content,
            "prompt_caching": "prompt-caching" in loop_content or "PROMPT_CACHING_BETA_FLAG" in loop_content,
            "extended_output": "output-128k" in loop_content or "OUTPUT_128K_BETA_FLAG" in loop_content,
            "thinking_budget": "thinking" in loop_content and "budget_tokens" in loop_content,
            "tool_streaming": "stream_command_output" in loop_content or "_stream_output" in loop_content,
        }
        
        for feature, implemented in features.items():
            if implemented:
                logger.info(f"✅ {feature} feature is implemented")
            else:
                logger.warning(f"❌ {feature} feature appears to be missing")
        
        # Return True if most features are implemented
        return sum(features.values()) >= 3
    
    except Exception as e:
        logger.error(f"Error checking features: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Testing Claude DC development environment...")
    test_passed = True
    
    # Check environment variables
    if not check_environment_variables():
        logger.error("Environment variable check failed")
        test_passed = False
    
    # Determine which tests to run based on mode
    if args.local:
        logger.info("Running tests in LOCAL mode")
        
        # Check local environment setup
        if not check_local_environment():
            logger.error("Local environment check failed")
            test_passed = False
        
        # Check for enhanced features
        if not check_enhanced_features():
            logger.warning("Some Phase 2 enhancements may be missing")
            # Don't fail the test for this, just warn
    else:
        logger.info("Running tests in DOCKER mode")
        
        # Check container status
        if not check_container_status():
            logger.error("Container status check failed")
            test_passed = False
        
        # Check Streamlit port
        if not check_streamlit_port():
            logger.error("Streamlit port check failed")
            test_passed = False
        
        # Check VNC port
        if not check_vnc_port():
            logger.error("VNC port check failed")
            # This is not critical, so we'll just warn
            logger.warning("VNC interface might not be working correctly")
    
    if test_passed:
        logger.info("✅ All tests passed! Development environment is set up correctly.")
        logger.info("You can now safely proceed with testing the Phase 2 enhancements.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()