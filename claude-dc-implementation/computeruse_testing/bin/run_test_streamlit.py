#!/usr/bin/env python3
"""
Script to run the Streamlit app for testing.
This launches the streamlit.py file in the test_environment directory.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_test_streamlit')

def main():
    """Main function to launch the test Streamlit app."""
    # Determine the test environment directory
    test_dir = "/home/computeruse/test_environment"
    
    # Check if directory exists
    if not os.path.isdir(test_dir):
        logger.error(f"Test directory not found: {test_dir}")
        print(f"ERROR: Test directory not found: {test_dir}")
        sys.exit(1)
    
    # Check if streamlit.py exists
    streamlit_path = os.path.join(test_dir, "streamlit.py")
    if not os.path.isfile(streamlit_path):
        logger.error(f"Streamlit file not found: {streamlit_path}")
        print(f"ERROR: Streamlit file not found: {streamlit_path}")
        sys.exit(1)
    
    # Set environment variables for testing
    os.environ['CLAUDE_ENV'] = 'dev'
    
    # Set the current working directory
    os.chdir(test_dir)
    
    # Start the Streamlit application
    try:
        logger.info("Starting Test Streamlit application...")
        print("Starting Test Streamlit application...")
        
        # Run the Streamlit app
        subprocess.run(
            ["python", "-m", "streamlit", "run", "streamlit.py", 
             "--server.port=8502", "--server.address=0.0.0.0"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        print(f"ERROR: Failed to start Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test Streamlit stopped by user.")
        print("Test Streamlit stopped by user.")
    
    return 0

if __name__ == "__main__":
    main()