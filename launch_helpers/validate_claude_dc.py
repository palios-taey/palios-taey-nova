#!/usr/bin/env python3
"""
Validation script for Claude DC Phase 2 Enhancements
Checks if all required components and features are properly set up
"""

import importlib
import os
import sys
from pathlib import Path

# Add repository root to Python path
REPO_ROOT = Path('/home/jesse/projects/palios-taey-nova')
CLAUDE_DC_ROOT = REPO_ROOT / 'claude-dc-implementation'
COMPUTER_USE_DEMO = CLAUDE_DC_ROOT / 'computeruse' / 'computer_use_demo'

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CLAUDE_DC_ROOT))
sys.path.insert(0, str(CLAUDE_DC_ROOT / 'computeruse'))

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_imports():
    """Check if required imports work correctly"""
    print_section("Checking imports")
    
    try:
        import computer_use_demo
        from computer_use_demo import (
            PROMPT_CACHING_BETA_FLAG,
            OUTPUT_128K_BETA_FLAG,
            DEFAULT_MAX_TOKENS,
        )
        print("✅ Base module imports work")
    except ImportError as e:
        print(f"❌ Failed to import from computer_use_demo: {e}")
        return False
    
    try:
        from computer_use_demo.loop import sampling_loop
        print("✅ loop.py imports work")
    except ImportError as e:
        print(f"❌ Failed to import from loop.py: {e}")
        return False
    
    try:
        from computer_use_demo.tools import ToolResult, ToolVersion
        print("✅ tools imports work")
    except ImportError as e:
        print(f"❌ Failed to import from tools module: {e}")
        return False
    
    try:
        # Try testing streamlit imports
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit is not installed")
        return False
    
    return True

def check_api_functionality():
    """Check if Anthropic API functionality works"""
    print_section("Checking Anthropic API functionality")
    
    try:
        from anthropic import Anthropic
        print("✅ Anthropic SDK is installed")
    except ImportError:
        print("❌ Anthropic SDK is not installed")
        return False
    
    # Check API key configuration
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("✅ ANTHROPIC_API_KEY is set in environment")
    else:
        anthropic_dir = Path.home() / '.anthropic'
        api_key_file = anthropic_dir / 'api_key'
        if api_key_file.exists():
            print("✅ API key file exists at ~/.anthropic/api_key")
        else:
            print("⚠️ No API key found in environment or ~/.anthropic/api_key")
            print("   You will need to enter an API key in the UI")
    
    return True

def check_streaming_support():
    """Check if streaming support is properly configured"""
    print_section("Checking streaming support")
    
    try:
        # Check loop.py for streaming parameter
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if '"stream": True' in loop_content:
            print("✅ Streaming is enabled in loop.py")
        else:
            print("❌ Streaming parameter not found in loop.py")
            return False
        
        # Check streamlit.py for streaming callbacks
        with open(COMPUTER_USE_DEMO / 'streamlit.py', 'r') as f:
            streamlit_content = f.read()
            
        if '_streaming_output_callback' in streamlit_content:
            print("✅ Streaming callback handler found in streamlit.py")
        else:
            print("❌ Streaming callback handler not found in streamlit.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking streaming support: {e}")
        return False

def check_prompt_caching():
    """Check if prompt caching is properly configured"""
    print_section("Checking prompt caching beta")
    
    try:
        # Import the required constant
        from computer_use_demo import PROMPT_CACHING_BETA_FLAG
        
        # Check loop.py for prompt caching functionality
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if PROMPT_CACHING_BETA_FLAG in loop_content and '_inject_prompt_caching' in loop_content:
            print("✅ Prompt caching is configured in loop.py")
        else:
            print("❌ Prompt caching not properly configured in loop.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking prompt caching: {e}")
        return False

def check_extended_output():
    """Check if 128K extended output is properly configured"""
    print_section("Checking 128K extended output")
    
    try:
        # Import the required constants
        from computer_use_demo import OUTPUT_128K_BETA_FLAG, DEFAULT_MAX_TOKENS
        
        # Check if max tokens is properly set
        if DEFAULT_MAX_TOKENS >= 65000:
            print(f"✅ Default max tokens set to {DEFAULT_MAX_TOKENS}")
        else:
            print(f"❌ Default max tokens too low: {DEFAULT_MAX_TOKENS}")
            return False
        
        # Check loop.py for extended output flag
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if OUTPUT_128K_BETA_FLAG in loop_content and "if \"claude-3-7\" in model" in loop_content:
            print("✅ Extended output is configured for Claude 3.7 models")
        else:
            print("❌ Extended output not properly configured in loop.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking extended output: {e}")
        return False

def check_real_time_tool_output():
    """Check if real-time tool output is properly configured"""
    print_section("Checking real-time tool output")
    
    try:
        # Check loop.py for tool streaming
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if "streaming=True" in loop_content and "set_stream_callback" in loop_content:
            print("✅ Real-time tool streaming is configured in loop.py")
        else:
            print("❌ Real-time tool streaming not properly configured in loop.py")
            return False
        
        # Check streamlit.py for tool callbacks
        with open(COMPUTER_USE_DEMO / 'streamlit.py', 'r') as f:
            streamlit_content = f.read()
            
        if "is_streaming" in streamlit_content and "tool_placeholders" in streamlit_content:
            print("✅ Tool streaming UI handlers found in streamlit.py")
        else:
            print("❌ Tool streaming UI handlers not found in streamlit.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking real-time tool output: {e}")
        return False

def main():
    """Run all validation checks"""
    print("\nClaude DC Phase 2 Enhancements Validation")
    print("=========================================")
    
    # Run all checks
    imports_ok = check_imports()
    api_ok = check_api_functionality()
    streaming_ok = check_streaming_support()
    caching_ok = check_prompt_caching()
    extended_output_ok = check_extended_output()
    tool_streaming_ok = check_real_time_tool_output()
    
    # Print summary
    print_section("Validation Summary")
    all_checks = [
        ("Module Imports", imports_ok),
        ("Anthropic API", api_ok),
        ("Streaming Responses", streaming_ok),
        ("Prompt Caching", caching_ok),
        ("128K Extended Output", extended_output_ok),
        ("Real-Time Tool Output", tool_streaming_ok)
    ]
    
    for name, result in all_checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    # Final result
    if all(result for _, result in all_checks):
        print("\n✅ All checks passed! Claude DC Phase 2 enhancements are properly configured.")
        print("You can now run Claude DC with: ./claude_dc_launch.sh")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues before running Claude DC.")
        return 1

if __name__ == "__main__":
    sys.exit(main())