#!/usr/bin/env python3
"""
Verification script for Claude DC implementation.
Tests the core functionality to ensure everything is working correctly.
"""

import os
import sys
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("verify")

# Try importing the required modules
def check_imports():
    """Check if all required modules are installed"""
    required_modules = {
        "anthropic": "0.50.0",
        "pydantic": "2.5.2",
        "streamlit": "1.31.0",
        "nest_asyncio": "1.5.8"
    }
    
    missing_modules = []
    incorrect_versions = []
    
    for module_name, expected_version in required_modules.items():
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "unknown")
            
            if version != expected_version:
                incorrect_versions.append(f"{module_name} (found v{version}, expected v{expected_version})")
                
        except ImportError:
            missing_modules.append(module_name)
    
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        return False
        
    if incorrect_versions:
        logger.warning(f"Modules with incorrect versions: {', '.join(incorrect_versions)}")
    
    logger.info("All required modules are installed")
    return True

# Test importing the agent loop
def test_agent_loop_import():
    """Test importing the agent loop module"""
    try:
        from loop import agent_loop, chat_with_claude
        logger.info("Successfully imported agent_loop and chat_with_claude from loop.py")
        return True
    except ImportError as e:
        logger.error(f"Failed to import agent_loop: {e}")
        return False

# Test importing tool implementations
def test_tool_imports():
    """Test importing tool implementations"""
    try:
        from tools import execute_bash_tool, execute_computer_tool, execute_edit_tool
        logger.info("Successfully imported all tool implementations")
        return True
    except ImportError as e:
        logger.error(f"Failed to import tools: {e}")
        return False

# Test Streamlit app import
def test_streamlit_import():
    """Test importing the Streamlit app"""
    try:
        # Only import the file, don't run it
        import streamlit_app
        logger.info("Successfully imported streamlit_app.py")
        return True
    except ImportError as e:
        logger.error(f"Failed to import streamlit_app: {e}")
        return False

# Test a simple API call
async def test_api_call():
    """Test a simple API call to verify API key and connectivity"""
    # Check if API key is set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY is not set in the environment")
        return False
    
    try:
        from anthropic import AsyncAnthropic
        
        # Create client with beta flag in header
        client = AsyncAnthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": "tools-2024-05-16"}
        )
        
        # Make a simple non-streaming call
        response = await client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say hello in one word"}]
        )
        
        # Check if response is valid
        if response and response.content and isinstance(response.content, list) and len(response.content) > 0:
            logger.info(f"API call successful, got response: {response.content[0].text}")
            return True
        else:
            logger.error(f"API call returned unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return False

# Run all tests
async def run_tests(args):
    """Run all the verification tests"""
    results = {}
    
    # Always run import tests
    results["imports"] = check_imports()
    results["agent_loop_import"] = test_agent_loop_import()
    results["tool_imports"] = test_tool_imports() 
    results["streamlit_import"] = test_streamlit_import()
    
    # Run API test if requested
    if args.api or args.all:
        results["api_call"] = await test_api_call()
    
    # Print summary
    print("\n" + "=" * 60)
    print(" Verification Results ".center(60, "="))
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.ljust(20)}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    print(f" Overall: {'✅ PASSED' if all_passed else '❌ FAILED'} ".center(60, "="))
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Verify Claude DC implementation")
    parser.add_argument("--imports", action="store_true", help="Test imports only")
    parser.add_argument("--api", action="store_true", help="Test API connectivity")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    # Default to running imports test only
    if not (args.imports or args.api or args.all):
        args.imports = True
    
    try:
        import nest_asyncio
        nest_asyncio.apply()
        
        exit_code = asyncio.run(run_tests(args))
        return exit_code
    except KeyboardInterrupt:
        print("\nVerification interrupted.")
        return 130
    except Exception as e:
        print(f"\nUnexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())