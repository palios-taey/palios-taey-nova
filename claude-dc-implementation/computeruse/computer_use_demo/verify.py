#!/usr/bin/env python3
"""
Verification script for the custom production environment.

This script performs comprehensive validation of all components to ensure
they're working correctly.
"""

import os
import sys
import asyncio
import logging
import importlib
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("verify")

# Add the current directory to the path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def verify_imports():
    """Verify that all required modules can be imported."""
    logger.info("Verifying imports...")
    
    try:
        # Core components
        import loop
        import streamlit
        
        # Models
        from models import tool_models
        
        # Tools
        from tools import registry
        from tools import bash
        from tools import edit
        from tools import computer
        
        # Utils
        from utils import streaming
        from utils import error_handling
        
        logger.info("All imports successful.")
        return True
    
    except ImportError as e:
        logger.error(f"Import failed: {str(e)}")
        return False

async def verify_anthropic_sdk():
    """Verify that the Anthropic SDK is installed and working."""
    logger.info("Verifying Anthropic SDK...")
    
    try:
        import anthropic
        logger.info(f"Anthropic SDK version {anthropic.__version__} installed.")
        
        # Check if API key is available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set in environment.")
        
        return True
    
    except ImportError:
        logger.error("Anthropic SDK not installed.")
        return False

async def verify_streamlit():
    """Verify that Streamlit is installed and working."""
    logger.info("Verifying Streamlit...")
    
    try:
        import streamlit
        logger.info(f"Streamlit version {streamlit.__version__} installed.")
        return True
    
    except ImportError:
        logger.error("Streamlit not installed.")
        return False

async def verify_pyautogui():
    """Verify that PyAutoGUI is installed and working."""
    logger.info("Verifying PyAutoGUI...")
    
    try:
        import pyautogui
        logger.info(f"PyAutoGUI version {pyautogui.__version__} installed.")
        return True
    
    except ImportError:
        logger.error("PyAutoGUI not installed.")
        return False

async def verify_tools():
    """Verify that all tools are registered and working."""
    logger.info("Verifying tool registry...")
    
    try:
        from tools.registry import initialize_tools, get_tool_registry
        
        # Initialize tools
        initialize_tools()
        
        # Get the tool registry
        registry = get_tool_registry()
        
        # Check if essential tools are registered
        required_tools = ["bash", "str_replace_editor", "computer"]
        missing_tools = [tool for tool in required_tools if tool not in registry]
        
        if missing_tools:
            logger.error(f"Missing tools: {', '.join(missing_tools)}")
            return False
        
        logger.info(f"All required tools registered: {', '.join(required_tools)}")
        return True
    
    except Exception as e:
        logger.error(f"Tool verification failed: {str(e)}")
        return False

async def verify_bash_tool():
    """Verify that the bash tool is working."""
    logger.info("Verifying bash tool...")
    
    try:
        from tools.bash import execute_bash
        
        # Execute a simple command
        result = await execute_bash({"command": "echo 'Hello, World!'"})
        
        if result.error:
            logger.error(f"Bash tool error: {result.error}")
            return False
        
        if "Hello, World!" not in result.output:
            logger.error(f"Unexpected output: {result.output}")
            return False
        
        logger.info("Bash tool working correctly.")
        return True
    
    except Exception as e:
        logger.error(f"Bash tool verification failed: {str(e)}")
        return False

async def verify_edit_tool():
    """Verify that the edit tool is working."""
    logger.info("Verifying edit tool...")
    
    try:
        from tools.edit import execute_edit
        
        # Create a test file
        test_file = "/tmp/verify_edit_test.txt"
        test_content = "Test content for verification."
        
        # Create the file
        result = await execute_edit({
            "command": "create",
            "path": test_file,
            "content": test_content
        })
        
        if result.error:
            logger.error(f"Edit tool create error: {result.error}")
            return False
        
        # View the file
        result = await execute_edit({
            "command": "view",
            "path": test_file
        })
        
        if result.error:
            logger.error(f"Edit tool view error: {result.error}")
            return False
        
        if test_content not in result.output:
            logger.error(f"Unexpected output: {result.output}")
            return False
        
        # Clean up
        os.remove(test_file)
        
        logger.info("Edit tool working correctly.")
        return True
    
    except Exception as e:
        logger.error(f"Edit tool verification failed: {str(e)}")
        try:
            # Clean up
            os.remove(test_file)
        except:
            pass
        return False

async def verify_agent_loop():
    """Verify that the agent loop can be initialized."""
    logger.info("Verifying agent loop...")
    
    try:
        from loop import StreamingSession
        
        # Initialize a session
        session = StreamingSession(
            conversation_history=[],
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            model="claude-3-7-sonnet-20240425",
            max_tokens=1000,
            thinking_budget=1000
        )
        
        logger.info("Agent loop session initialized successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Agent loop verification failed: {str(e)}")
        return False

async def run_full_verification():
    """Run all verification tests."""
    logger.info("Starting full verification...")
    
    # Track failures
    failures = 0
    
    # Verify imports
    if not await verify_imports():
        failures += 1
    
    # Verify Anthropic SDK
    if not await verify_anthropic_sdk():
        failures += 1
    
    # Verify Streamlit
    if not await verify_streamlit():
        failures += 1
    
    # Verify PyAutoGUI
    if not await verify_pyautogui():
        failures += 1
    
    # Verify tools
    if not await verify_tools():
        failures += 1
    
    # Verify bash tool
    if not await verify_bash_tool():
        failures += 1
    
    # Verify edit tool
    if not await verify_edit_tool():
        failures += 1
    
    # Verify agent loop
    if not await verify_agent_loop():
        failures += 1
    
    # Report result
    if failures == 0:
        logger.info("All verification tests passed!")
        return True
    else:
        logger.error(f"{failures} verification tests failed.")
        return False

async def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(description="Verify the custom production environment.")
    parser.add_argument("--full", action="store_true", help="Run full verification")
    parser.add_argument("--imports", action="store_true", help="Verify imports only")
    parser.add_argument("--tools", action="store_true", help="Verify tools only")
    args = parser.parse_args()
    
    if args.imports:
        result = await verify_imports()
    elif args.tools:
        result = await verify_tools() and await verify_bash_tool() and await verify_edit_tool()
    else:
        result = await run_full_verification()
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    asyncio.run(main())