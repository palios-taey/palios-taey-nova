#!/usr/bin/env python3
"""
Test script to validate the Claude DC implementation.
This script performs basic tests to ensure the implementation works correctly.
"""

import os
import sys
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_implementation")

try:
    from loop import (
        agent_loop,
        DEFAULT_SYSTEM_PROMPT,
        BETA_FLAGS,
        PROMPT_CACHING_FLAG,
        EXTENDED_OUTPUT_FLAG,
        COMPUTER_TOOL,
        BASH_TOOL
    )
except ImportError as e:
    logger.error(f"Error importing agent_loop module: {e}")
    sys.exit(1)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

async def test_api_configuration():
    """Test the API configuration (beta flags, thinking setup)"""
    print_header("Testing API Configuration")
    
    # Check beta flags
    print(f"Beta flags: {BETA_FLAGS}")
    if not isinstance(BETA_FLAGS, dict):
        print("❌ Beta flags should be defined as a dictionary")
        return False
    
    # Check beta flag contents
    required_keys = ["computer_use_20241022", "computer_use_20250124"]
    missing_keys = [key for key in required_keys if key not in BETA_FLAGS]
    if missing_keys:
        print(f"❌ Missing required beta flags: {missing_keys}")
        return False
    
    print("✅ Beta flags properly configured")
    
    # Check prompt caching flag
    print(f"Prompt caching flag: {PROMPT_CACHING_FLAG}")
    if PROMPT_CACHING_FLAG != "cache-control-2024-07-01":
        print("❌ Incorrect prompt caching flag")
        return False
    
    print("✅ Prompt caching flag properly configured")
    
    # Check extended output flag
    print(f"Extended output flag: {EXTENDED_OUTPUT_FLAG}")
    if EXTENDED_OUTPUT_FLAG != "output-128k-2025-02-19":
        print("❌ Incorrect extended output flag")
        return False
    
    print("✅ Extended output flag properly configured")
    
    # Check thinking parameter implementation
    print("Checking thinking parameter implementation...")
    # This is a simplified check - it just verifies that thinking is configured as a parameter
    # A full check would require executing the API call, which we avoid for this test
    
    # Look for the thinking configuration pattern in the agent_loop function source
    import inspect
    agent_loop_source = inspect.getsource(agent_loop)
    
    if "thinking_budget" not in agent_loop_source or "extra_body" not in agent_loop_source:
        print("❌ Thinking parameter implementation not found")
        return False
    
    if "thinking-" in agent_loop_source or "THINKING_FLAG" in agent_loop_source:
        print("❌ Thinking should not be implemented as a beta flag")
        return False
    
    if 'extra_body["thinking"]' not in agent_loop_source:
        print("❌ Thinking should be set in extra_body")
        return False
    
    print("✅ Thinking correctly implemented as a parameter, not a beta flag")
    
    return True

async def test_tool_configuration():
    """Test the tool configuration and validation"""
    print_header("Testing Tool Configuration")
    
    # Check computer tool definition
    print("Checking computer tool definition...")
    if not COMPUTER_TOOL.get("name") == "computer":
        print("❌ Computer tool should be named 'computer'")
        return False
    
    if not COMPUTER_TOOL.get("input_schema", {}).get("properties", {}).get("action"):
        print("❌ Computer tool should have 'action' property in input schema")
        return False
    
    print("✅ Computer tool properly defined")
    
    # Check bash tool definition
    print("Checking bash tool definition...")
    if not BASH_TOOL.get("name") == "bash":
        print("❌ Bash tool should be named 'bash'")
        return False
    
    if not BASH_TOOL.get("input_schema", {}).get("properties", {}).get("command"):
        print("❌ Bash tool should have 'command' property in input schema")
        return False
    
    print("✅ Bash tool properly defined")
    
    # Check tools module imports
    print("Checking tools module...")
    try:
        from tools import execute_bash_tool, execute_computer_tool
        print("✅ Tools module imports successfully")
    except ImportError as e:
        print(f"❌ Tools module import failed: {e}")
        print("This error is expected if running the test outside the implementation directory")
        
    return True

async def test_agent_loop_interface():
    """Test the agent loop interface"""
    print_header("Testing Agent Loop Interface")
    
    # Check agent_loop function signature
    import inspect
    sig = inspect.signature(agent_loop)
    params = sig.parameters
    
    required_params = [
        "model", "messages", "tools", "output_callback",
        "thinking_budget", "enable_prompt_caching", "enable_extended_output"
    ]
    
    missing_params = [param for param in required_params if param not in params]
    if missing_params:
        print(f"❌ Agent loop is missing required parameters: {missing_params}")
        return False
    
    print("✅ Agent loop has all required parameters")
    
    # Test betas implementation
    agent_loop_source = inspect.getsource(agent_loop)
    if "api_params" not in agent_loop_source or "anthropic_beta" not in agent_loop_source:
        print("❌ Beta flags should be passed as anthropic_beta parameter")
        return False
    
    print("✅ Beta flags correctly configured as anthropic_beta parameter")
    
    # Test extra_body unpacking
    if "**extra_body" not in inspect.getsource(agent_loop):
        print("❌ extra_body should be unpacked with ** operator")
        return False
    
    print("✅ extra_body correctly unpacked with ** operator")
    
    return True

async def test_streamlit_app():
    """Test the Streamlit app implementation"""
    print_header("Testing Streamlit App")
    
    # Check if the streamlit_app.py file exists
    import os
    if not os.path.exists("streamlit_app.py"):
        print("❌ streamlit_app.py file not found")
        return False
    
    print("✅ streamlit_app.py file exists")
    
    # Check if the file is valid Python
    try:
        with open("streamlit_app.py", "r") as f:
            content = f.read()
        
        # Try to compile the code to check for syntax errors
        compile(content, "streamlit_app.py", "exec")
        print("✅ streamlit_app.py is valid Python code")
    except Exception as e:
        print(f"❌ streamlit_app.py has errors: {e}")
        return False
    
    # Check for key Streamlit components
    if "st.chat_message" not in content:
        print("❌ streamlit_app.py should use st.chat_message for chat interface")
    else:
        print("✅ streamlit_app.py uses chat message components")
    
    if "st.sidebar" not in content:
        print("❌ streamlit_app.py should use st.sidebar for configuration")
    else:
        print("✅ streamlit_app.py uses sidebar for configuration")
    
    if "api_key" not in content.lower():
        print("❌ streamlit_app.py should handle API key input")
    else:
        print("✅ streamlit_app.py handles API key input")
    
    if "enable_thinking" not in content:
        print("❌ streamlit_app.py should have thinking configuration")
    else:
        print("✅ streamlit_app.py has thinking configuration")
    
    return True

async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test the Claude DC implementation")
    parser.add_argument("--tests", type=str, choices=["all", "api", "tools", "loop", "streamlit"], 
                       default="all", help="Which tests to run")
    args = parser.parse_args()
    
    print_header("Claude DC Implementation Tester")
    
    results = {}
    
    if args.tests in ["all", "api"]:
        results["api_configuration"] = await test_api_configuration()
    
    if args.tests in ["all", "tools"]:
        results["tool_configuration"] = await test_tool_configuration()
    
    if args.tests in ["all", "loop"]:
        results["agent_loop"] = await test_agent_loop_interface()
    
    if args.tests in ["all", "streamlit"]:
        results["streamlit_app"] = await test_streamlit_app()
    
    # Print summary
    print_header("Test Results")
    
    for test, result in results.items():
        print(f"{test}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTesting interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)