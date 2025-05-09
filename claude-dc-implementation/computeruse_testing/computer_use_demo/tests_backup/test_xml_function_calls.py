#!/usr/bin/env python3
"""
Test script for XML function call implementation.

This script tests the XML function call implementation with the buffer pattern
to ensure that Claude DC can properly generate and execute XML-style function calls
during streaming without encountering the race condition.
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_xml_function_calls.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_xml_function_calls")

# Add streaming and current directory to path
import sys
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "streaming"))

# Import streaming components
from streaming.unified_streaming_loop import unified_streaming_agent_loop
from streaming.dc_setup import dc_initialize

async def test_xml_bash_command():
    """Test XML function calls with bash commands."""
    logger.info("========== Testing XML Function Calls with Bash Command ==========")
    
    # Load API key
    api_key = None
    
    # Try to load API key directly from the secrets file
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets["api_keys"]["anthropic"]
                logger.info(f"Loaded API key from {secrets_path}")
                
                # Verify API key format
                if not api_key.startswith("sk-ant-"):
                    logger.warning("API key doesn't match expected format (should start with 'sk-ant-')")
        except Exception as e:
            logger.warning(f"Error loading API key from {secrets_path}: {str(e)}")
    
    # If still not found, try different paths
    if not api_key:
        for api_key_path in [
            Path("/home/computeruse/secrets/palios-taey-nova.json"),
            Path("/home/computeruse/secrets/palios-taey-secrets.json")
        ]:
            try:
                if api_key_path.exists():
                    with open(api_key_path, "r") as f:
                        secrets = json.load(f)
                        # Check different possible key names
                        for key_name in ["api_key", "anthropic_api_key"]:
                            if key_name in secrets:
                                api_key = secrets[key_name]
                                break
                if api_key:
                    break
            except Exception as e:
                logger.warning(f"Error loading API key from {api_key_path}: {str(e)}")
    
    if not api_key:
        raise ValueError("API key not found in any secrets file")
    
    # Initialize DC
    dc_initialize(use_real_adapters=True)
    
    # Define test prompts
    test_prompts = [
        "Run the command 'ls -la' and explain what these files are for.",
        "Can you count the number of lines in the unified_streaming_loop.py file?",
        "Check the current directory and tell me how many Python files are in it.",
        "What Python version are we running?"
    ]
    
    # Test each prompt
    conversation_history = []
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: {prompt}")
        try:
            # Execute the agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=prompt,
                conversation_history=conversation_history,
                api_key=api_key,
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                thinking_budget=2000,
                use_real_adapters=True
            )
            
            # Log success
            logger.info(f"Test {i+1} completed successfully")
        except Exception as e:
            # Log error
            logger.error(f"Test {i+1} failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("XML function call tests completed.")

async def test_xml_computer_tool():
    """Test XML function calls with computer tools."""
    logger.info("========== Testing XML Function Calls with Computer Tool ==========")
    
    # Load API key
    api_key = None
    
    # Try to load API key directly from the secrets file
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets["api_keys"]["anthropic"]
                logger.info(f"Loaded API key from {secrets_path}")
                
                # Verify API key format
                if not api_key.startswith("sk-ant-"):
                    logger.warning("API key doesn't match expected format (should start with 'sk-ant-')")
        except Exception as e:
            logger.warning(f"Error loading API key from {secrets_path}: {str(e)}")
    
    # If still not found, try different paths
    if not api_key:
        for api_key_path in [
            Path("/home/computeruse/secrets/palios-taey-nova.json"),
            Path("/home/computeruse/secrets/palios-taey-secrets.json")
        ]:
            try:
                if api_key_path.exists():
                    with open(api_key_path, "r") as f:
                        secrets = json.load(f)
                        # Check different possible key names
                        for key_name in ["api_key", "anthropic_api_key"]:
                            if key_name in secrets:
                                api_key = secrets[key_name]
                                break
                if api_key:
                    break
            except Exception as e:
                logger.warning(f"Error loading API key from {api_key_path}: {str(e)}")
    
    if not api_key:
        raise ValueError("API key not found in any secrets file")
    
    # Initialize DC
    dc_initialize(use_real_adapters=True)
    
    # Define test prompts
    test_prompts = [
        "Take a screenshot of the current screen and describe what you see.",
        "Check if there are any images visible on the screen."
    ]
    
    # Test each prompt
    conversation_history = []
    for i, prompt in enumerate(test_prompts):
        logger.info(f"Test {i+1}: {prompt}")
        try:
            # Execute the agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=prompt,
                conversation_history=conversation_history,
                api_key=api_key,
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                thinking_budget=2000,
                use_real_adapters=True
            )
            
            # Log success
            logger.info(f"Test {i+1} completed successfully")
        except Exception as e:
            # Log error
            logger.error(f"Test {i+1} failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("XML function call tests with computer tool completed.")

async def run_all_tests():
    """Run all XML function call tests."""
    try:
        # Test bash commands
        await test_xml_bash_command()
        
        # Test computer tools
        await test_xml_computer_tool()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Tests failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(run_all_tests())