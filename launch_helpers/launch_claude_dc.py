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
    
    # Set required screen dimensions for ComputerTool
    # Default to 1024x768 if not set
    if not os.environ.get("WIDTH"):
        os.environ["WIDTH"] = "1024"
    if not os.environ.get("HEIGHT"):
        os.environ["HEIGHT"] = "768"
    if not os.environ.get("DISPLAY_NUM"):
        os.environ["DISPLAY_NUM"] = "1"
    
    # Check if ANTHROPIC_API_KEY is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY environment variable not set")
        api_key_path = Path.home() / '.anthropic' / 'api_key'
        if api_key_path.exists():
            logger.info("Found API key file at ~/.anthropic/api_key")
        else:
            logger.warning("No API key file found. Please set ANTHROPIC_API_KEY environment variable")
    
    logger.info("Environment setup complete")

def launch_streamlit():
    """Launch the Streamlit interface"""
    logger.info("Starting Claude DC Streamlit interface...")
    
    try:
        # Create a temporary runner script to ensure proper imports
        runner_script = REPO_ROOT / "temp_streamlit_runner.py"
        with open(runner_script, "w") as f:
            f.write('''
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('streamlit_runner')

# Add repository path to Python path to make all imports work
repo_root = Path("'''+str(REPO_ROOT)+'''")
computer_use_demo = repo_root / "claude-dc-implementation/computeruse/computer_use_demo"

# Add all required paths to Python system path
for path in [repo_root, repo_root / "claude-dc-implementation", 
             repo_root / "claude-dc-implementation/computeruse"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Additionally set PYTHONPATH environment variable
current_pythonpath = os.environ.get("PYTHONPATH", "")
paths_to_add = [str(repo_root), 
                str(repo_root / "claude-dc-implementation"),
                str(repo_root / "claude-dc-implementation/computeruse")]
                
new_pythonpath = os.pathsep.join([current_pythonpath] + paths_to_add)
os.environ["PYTHONPATH"] = new_pythonpath

# Ensure ComputerTool environment variables are set
required_vars = {
    "WIDTH": os.environ.get("WIDTH", "1024"),
    "HEIGHT": os.environ.get("HEIGHT", "768"),
    "DISPLAY_NUM": os.environ.get("DISPLAY_NUM", "1")
}

# Set or update environment variables
for var, value in required_vars.items():
    os.environ[var] = value
    
# Log environment settings
logger.info(f"Screen dimensions: {os.environ['WIDTH']}x{os.environ['HEIGHT']} on display:{os.environ['DISPLAY_NUM']}")
logger.info(f"Python path includes: {sys.path[:5]}")

# Now import and run streamlit
import streamlit.web.cli as stcli
import streamlit as st

if __name__ == "__main__":
    streamlit_file = str(computer_use_demo / "streamlit.py")
    sys.argv = ["streamlit", "run", streamlit_file, 
                "--server.port=8501", "--server.headless=true"]
    sys.exit(stcli.main())
''')
        
        # Make script executable
        os.chmod(runner_script, 0o755)
        
        # Run the script
        logger.info(f"Running streamlit via wrapper script: {runner_script}")
        
        # Make sure required environment variables are passed to subprocess
        env_vars = {
            **os.environ,
            "PYTHONPATH": f"{REPO_ROOT}:{CLAUDE_DC_ROOT}:{COMPUTER_USE_DEMO.parent}",
            "WIDTH": os.environ.get("WIDTH", "1024"),
            "HEIGHT": os.environ.get("HEIGHT", "768"),
            "DISPLAY_NUM": os.environ.get("DISPLAY_NUM", "1")
        }
        
        # Log environment settings
        logger.info(f"Screen dimensions: {env_vars['WIDTH']}x{env_vars['HEIGHT']} on display:{env_vars['DISPLAY_NUM']}")
        
        result = subprocess.run(
            ["python3", str(runner_script)],
            check=True,
            env=env_vars
        )
        
        # Clean up temp file
        os.unlink(runner_script)
        
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Don't remove temp file on error to allow debugging
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

def run_validate_only_mode():
    """Run validation tests without starting Claude DC"""
    logger.info("Running in validation-only mode")
    
    # Import the validation module
    validation_script = REPO_ROOT / "launch_helpers" / "validate_claude_dc.py"
    if not validation_script.exists():
        logger.error(f"Validation script not found at {validation_script}")
        return 1
    
    try:
        logger.info("Running comprehensive validation tests...")
        result = subprocess.run(
            [sys.executable, str(validation_script)],
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Validation passed! Claude DC is ready to launch.")
            return 0
        else:
            logger.error("Validation failed. Please fix the issues before running Claude DC.")
            return 1
    except Exception as e:
        logger.error(f"Error running validation: {e}")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude DC Launcher")
    parser.add_argument("--mode", choices=["console", "streamlit"], default="streamlit",
                     help="Launch mode (console or streamlit)")
    parser.add_argument("--env", choices=["dev", "live"], default="live",
                     help="Environment mode (dev or live)")
    parser.add_argument("--validate-only", action="store_true", 
                     help="Run validation tests without starting Claude DC")
    parser.add_argument("--runtime-imports-only", action="store_true",
                     help="Only validate runtime imports")
    
    args = parser.parse_args()
    
    # Set up environment
    setup_environment()
    
    # Override environment mode if specified
    if args.env:
        os.environ["CLAUDE_ENV"] = args.env
        logger.info(f"Setting environment mode to: {args.env}")
    
    # Run in validation-only mode if requested
    if args.validate_only:
        sys.exit(run_validate_only_mode())
    
    # Run specific validation if requested
    if args.runtime_imports_only:
        validation_script = REPO_ROOT / "launch_helpers" / "validate_claude_dc.py"
        sys.exit(subprocess.run([sys.executable, str(validation_script), "--runtime-imports-only"]).returncode)
    
    # Launch in specified mode
    if args.mode == "console":
        sys.exit(launch_console_mode())
    else:
        sys.exit(launch_streamlit())