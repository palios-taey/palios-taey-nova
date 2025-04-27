#!/usr/bin/env python3
"""
Test script for the Claude Computer Use implementation.
Tests various aspects of the implementation to validate functionality.
"""

import os
import sys
import asyncio
import argparse
import inspect
from typing import Dict, Any, List, Optional
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_script")

# Import the agent_loop module
try:
    from loop import (
        agent_loop,
        COMPUTER_TOOL,
        BASH_TOOL,
        DEFAULT_SYSTEM_PROMPT,
        BETA_FLAGS,
        PROMPT_CACHING_FLAG,
        EXTENDED_OUTPUT_FLAG
    )
except ImportError as e:
    logger.error(f"Error importing agent_loop module: {e}")
    sys.exit(1)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

async def test_beta_flags():
    """Test beta flags configuration"""
    print_header("Testing Beta Flags Configuration")
    
    # Check if beta flags are properly defined
    print(f"Beta flags defined: {BETA_FLAGS}")
    if not isinstance(BETA_FLAGS, dict):
        print("❌ Beta flags should be defined as a dictionary")
        return False
    
    # Check if required beta flags are present
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
    
    return True

async def test_api_integration():
    """Test API integration (without actually making an API call)"""
    print_header("Testing API Integration")
    
    # Check if the agent_loop function has the correct parameters
    import inspect
    sig = inspect.signature(agent_loop)
    
    required_params = [
        "model", "messages", "tools", "output_callback", 
        "max_tokens", "thinking_budget", "enable_prompt_caching",
        "enable_extended_output"
    ]
    
    missing_params = [param for param in required_params if param not in sig.parameters]
    if missing_params:
        print(f"❌ Agent loop is missing required parameters: {missing_params}")
        return False
    
    print("✅ Agent loop has all required parameters")
    
    # Check if thinking is implemented as a parameter, not a beta flag
    agent_loop_source = inspect.getsource(agent_loop)
    if "thinking_budget" not in agent_loop_source or "extra_body" not in agent_loop_source:
        print("❌ Thinking must be implemented as a parameter in extra_body")
        return False
    
    if "thinking" not in agent_loop_source or "thinking-" in agent_loop_source:
        print("❌ Thinking must not be implemented as a beta flag")
        return False
    
    print("✅ Thinking is properly implemented as a parameter")
    
    return True

async def test_tool_validation():
    """Test tool parameter validation"""
    print_header("Testing Tool Parameter Validation")
    
    # Check if tool definitions are properly configured
    if not hasattr(COMPUTER_TOOL, "get") or not COMPUTER_TOOL.get("input_schema"):
        print("❌ Computer tool definition is missing input schema")
        return False
    
    if not hasattr(BASH_TOOL, "get") or not BASH_TOOL.get("input_schema"):
        print("❌ Bash tool definition is missing input schema")
        return False
    
    print("✅ Tool definitions are properly configured")
    
    # Check if there's parameter validation logic
    agent_loop_source = inspect.getsource(agent_loop)
    validation_terms = ["validate", "parameter", "required", "missing"]
    
    if not any(term in agent_loop_source for term in validation_terms):
        print("❌ Parameter validation logic is missing or insufficient")
        return False
    
    print("✅ Parameter validation logic is present")
    
    return True

async def test_error_handling():
    """Test error handling"""
    print_header("Testing Error Handling")
    
    # Check if there's proper exception handling
    agent_loop_source = inspect.getsource(agent_loop)
    
    if "try:" not in agent_loop_source or "except" not in agent_loop_source:
        print("❌ Exception handling is missing")
        return False
    
    exception_types = ["APIStatusError", "APIResponseValidationError", "APIError", "Exception"]
    missing_exceptions = [exc for exc in exception_types if exc not in agent_loop_source]
    
    if missing_exceptions:
        print(f"❌ Missing exception handling for: {missing_exceptions}")
        return False
    
    print("✅ Proper exception handling is present")
    
    return True

async def main():
    """Main test function"""
    print_header("Claude Computer Use Implementation Test")
    
    # Test beta flags
    beta_flags_ok = await test_beta_flags()
    
    # Test API integration
    api_integration_ok = await test_api_integration()
    
    # Test tool validation
    tool_validation_ok = await test_tool_validation()
    
    # Test error handling
    error_handling_ok = await test_error_handling()
    
    # Print summary
    print_header("Test Summary")
    
    print(f"Beta Flags Configuration: {'✅' if beta_flags_ok else '❌'}")
    print(f"API Integration: {'✅' if api_integration_ok else '❌'}")
    print(f"Tool Parameter Validation: {'✅' if tool_validation_ok else '❌'}")
    print(f"Error Handling: {'✅' if error_handling_ok else '❌'}")
    
    overall_result = all([beta_flags_ok, api_integration_ok, tool_validation_ok, error_handling_ok])
    print(f"\nOverall Result: {'✅ PASSED' if overall_result else '❌ FAILED'}")
    
    return 0 if overall_result else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTesting interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        sys.exit(1)