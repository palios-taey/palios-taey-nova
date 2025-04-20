#!/usr/bin/env python3
"""
Unified launcher for Claude DC with proper Python path setup.
This script ensures all imports work correctly across the application.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc_launcher')

# Determine repository root and module paths
REPO_ROOT = Path('/home/jesse/projects/palios-taey-nova')
CLAUDE_DC_ROOT = REPO_ROOT / 'claude-dc-implementation'
COMPUTER_USE_DEMO = CLAUDE_DC_ROOT / 'computeruse' / 'computer_use_demo'

def setup_environment():
    """Set up the environment variables and Python path for Claude DC"""
    # Add module paths to Python path
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(CLAUDE_DC_ROOT))
    sys.path.insert(0, str(CLAUDE_DC_ROOT / 'computeruse'))
    
    # Set necessary environment variables
    os.environ["CLAUDE_ENV"] = "live"  # Can be overridden with command line args
    
    # Check if ANTHROPIC_API_KEY is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY environment variable not set")
        if Path.home() / '.anthropic' / 'api_key' in os.path.exists():
            logger.info("Found API key file at ~/.anthropic/api_key")
        else:
            logger.warning("No API key file found. Please set ANTHROPIC_API_KEY environment variable")
    
    logger.info("Environment setup complete")

def launch_streamlit():
    """Launch the Streamlit interface"""
    logger.info("Starting Claude DC Streamlit interface...")
    
    try:
        # Change to the computer_use_demo directory
        os.chdir(COMPUTER_USE_DEMO)
        
        # Launch streamlit with the correct module path
        result = subprocess.run(
            [
                "python3", "-m", "streamlit", "run", 
                str(COMPUTER_USE_DEMO / "streamlit.py"),
                "--server.port", "8501",
                "--server.headless", "true"
            ],
            check=True
        )
        
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1

def launch_console_mode():
    """Launch Claude DC in console mode"""
    logger.info("Starting Claude DC in console mode...")
    
    try:
        # Change to the computer_use_demo directory
        os.chdir(COMPUTER_USE_DEMO)
        
        # Import and run the loop directly
        from computer_use_demo.loop import sampling_loop
        
        # Run in console mode (implementation would go here)
        logger.info("Console mode not fully implemented yet. Use Streamlit interface instead.")
        return 0
    except Exception as e:
        logger.error(f"An error occurred in console mode: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude DC Launcher")
    parser.add_argument("--mode", choices=["console", "streamlit"], default="streamlit",
                     help="Launch mode (console or streamlit)")
    parser.add_argument("--env", choices=["dev", "live"], default="live",
                     help="Environment mode (dev or live)")
    
    args = parser.parse_args()
    
    # Set up environment
    setup_environment()
    
    # Override environment mode if specified
    if args.env:
        os.environ["CLAUDE_ENV"] = args.env
        logger.info(f"Setting environment mode to: {args.env}")
    
    # Launch in specified mode
    if args.mode == "console":
        sys.exit(launch_console_mode())
    else:
        sys.exit(launch_streamlit())