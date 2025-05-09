#!/usr/bin/env python3
"""
Test script for evaluating Phase 2 features in Claude DC implementation.
This script directly tests streaming, prompt caching, and extended output features.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import importlib.util
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_phase2_features')

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test Phase 2 features in Claude DC')
parser.add_argument('--test-dir', type=str, default='/home/computeruse/test_environment', 
                    help='Directory containing test environment files')
args = parser.parse_args()

def check_api_key():
    """Verify Anthropic API key is set."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return False
    return True

def test_streaming():
    """Test streaming functionality by importing and using the loop module."""
    test_dir = Path(args.test_dir)
    
    try:
        # Create a simple test module to use the loop's functionality
        test_script_path = test_dir / "test_streaming.py"
        with open(test_script_path, "w") as f:
            f.write("""
import os
import sys
from loop import sampling_loop
import asyncio
from anthropic import Anthropic

# Output collector
outputs = []

def output_callback(content):
    if hasattr(content, 'get') and content.get('is_delta', False):
        print(f"Streaming delta: {content.get('text', '')}")
        outputs.append(content.get('text', ''))
    else:
        print(f"Got content block: {content}")

def tool_output_callback(result, tool_id):
    print(f"Tool output from {tool_id}: {result}")

def api_response_callback(req, resp, err):
    if err:
        print(f"API error: {err}")

async def test_streaming():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    client = Anthropic(api_key=api_key)
    
    # Simple test message
    messages = [{"role": "user", "content": [{"type": "text", "text": "Generate 50 words about streaming in Claude. Include the word 'streaming' at least 3 times."}]}]
    
    result = await sampling_loop(
        model="claude-3-7-sonnet-20250219",
        provider="anthropic",
        system_prompt_suffix="",
        messages=messages,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        api_key=api_key,
        max_tokens=10240,
        tool_version="computer_use_20250124",
        thinking_budget=4096,
    )
    
    # Check if we got streaming chunks
    print(f"Received {len(outputs)} streaming chunks")
    if len(outputs) > 1:
        print("✅ Streaming is working!")
    else:
        print("❌ Streaming is not working - only got one chunk")
    
    return len(outputs) > 1

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(test_streaming())
    sys.exit(0 if success else 1)
""")
        
        # Make it executable
        test_script_path.chmod(0o755)
        
        # Run the test script
        logger.info("Running streaming test...")
        os.chdir(test_dir)
        import subprocess
        result = subprocess.run([sys.executable, "test_streaming.py"], 
                               capture_output=True, text=True)
        
        # Check result
        if "Streaming is working!" in result.stdout:
            logger.info("✅ Streaming test passed!")
            return True
        else:
            logger.error(f"❌ Streaming test failed: {result.stdout}")
            return False
    except Exception as e:
        logger.error(f"Error testing streaming: {e}")
        return False

def test_prompt_caching():
    """Test prompt caching by checking code implementation."""
    test_dir = Path(args.test_dir)
    
    try:
        with open(test_dir / "loop.py", "r") as f:
            loop_content = f.read()
        
        # Check for prompt caching features
        has_caching_flag = "prompt-caching-2024-07-31" in loop_content
        has_inject_func = "_inject_prompt_caching" in loop_content
        uses_ephemeral = "ephemeral" in loop_content
        
        if has_caching_flag and has_inject_func and uses_ephemeral:
            logger.info("✅ Prompt caching implementation found in the code")
            return True
        else:
            logger.warning("❌ Some prompt caching components may be missing:")
            if not has_caching_flag:
                logger.warning("  - Missing prompt-caching beta flag")
            if not has_inject_func:
                logger.warning("  - Missing _inject_prompt_caching function")
            if not uses_ephemeral:
                logger.warning("  - Missing ephemeral cache control")
            return False
    except Exception as e:
        logger.error(f"Error checking prompt caching: {e}")
        return False

def test_extended_output():
    """Test extended output capability by checking code implementation."""
    test_dir = Path(args.test_dir)
    
    try:
        with open(test_dir / "loop.py", "r") as f:
            loop_content = f.read()
        
        # Check for extended output features
        has_output_flag = "output-128k" in loop_content
        uses_large_tokens = "65536" in loop_content or "128000" in loop_content
        has_thinking_budget = "thinking" in loop_content and "budget_tokens" in loop_content
        
        if has_output_flag and uses_large_tokens and has_thinking_budget:
            logger.info("✅ Extended output implementation found in the code")
            return True
        else:
            logger.warning("❌ Some extended output components may be missing:")
            if not has_output_flag:
                logger.warning("  - Missing output-128k beta flag")
            if not uses_large_tokens:
                logger.warning("  - No large token limits found")
            if not has_thinking_budget:
                logger.warning("  - Missing thinking budget configuration")
            return False
    except Exception as e:
        logger.error(f"Error checking extended output: {e}")
        return False

def test_tool_streaming():
    """Test tool output streaming by checking code implementation."""
    test_dir = Path(args.test_dir)
    
    try:
        # Look for streaming tool implementations
        streaming_tool_path = test_dir / "tools" / "streaming_tool.py"
        tool_streaming_exists = streaming_tool_path.exists()
        
        # Check bash.py for streaming
        with open(test_dir / "tools/bash.py", "r") as f:
            bash_content = f.read()
        
        bash_uses_streaming = "stream" in bash_content and "stream_command_output" in bash_content
        
        # Check collection.py for streaming
        collection_path = test_dir / "tools/collection.py"
        if collection_path.exists():
            with open(collection_path, "r") as f:
                collection_content = f.read()
            collection_supports_streaming = "streaming" in collection_content
        else:
            collection_supports_streaming = False
        
        if tool_streaming_exists and bash_uses_streaming and collection_supports_streaming:
            logger.info("✅ Tool streaming implementation found in the code")
            return True
        else:
            logger.warning("❌ Some tool streaming components may be missing:")
            if not tool_streaming_exists:
                logger.warning("  - Missing streaming_tool.py file")
            if not bash_uses_streaming:
                logger.warning("  - Bash tool doesn't implement streaming")
            if not collection_supports_streaming:
                logger.warning("  - Tool collection doesn't support streaming")
            return False
    except Exception as e:
        logger.error(f"Error checking tool streaming: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Testing Phase 2 features in Claude DC...")
    
    # Check environment
    if not check_api_key():
        logger.error("API key check failed - cannot proceed with tests")
        sys.exit(1)
    
    # Test directory
    test_dir = Path(args.test_dir)
    if not test_dir.exists() or not (test_dir / "loop.py").exists():
        logger.error(f"Test directory {test_dir} does not exist or is missing important files")
        sys.exit(1)
    
    # Test Phase 2 features
    streaming_test = test_streaming()
    prompt_caching_test = test_prompt_caching()
    extended_output_test = test_extended_output()
    tool_streaming_test = test_tool_streaming()
    
    # Results summary
    logger.info("\n===== PHASE 2 FEATURE TEST RESULTS =====")
    logger.info(f"Streaming: {'✅ PASS' if streaming_test else '❌ FAIL'}")
    logger.info(f"Prompt Caching: {'✅ PASS' if prompt_caching_test else '❌ FAIL'}")
    logger.info(f"Extended Output: {'✅ PASS' if extended_output_test else '❌ FAIL'}")
    logger.info(f"Tool Streaming: {'✅ PASS' if tool_streaming_test else '❌ FAIL'}")
    
    # Overall assessment
    passing_tests = sum([streaming_test, prompt_caching_test, extended_output_test, tool_streaming_test])
    if passing_tests >= 3:
        logger.info(f"\n✅ OVERALL ASSESSMENT: PASSED ({passing_tests}/4 features implemented)")
        logger.info("The Phase 2 enhancements appear to be implemented correctly!")
        if passing_tests < 4:
            logger.info("Note: Some features may need additional work.")
    else:
        logger.warning(f"\n⚠️ OVERALL ASSESSMENT: PARTIAL ({passing_tests}/4 features implemented)")
        logger.warning("Several Phase 2 features are missing or incomplete.")
    
    # Create a report file
    report = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": {
            "streaming": streaming_test,
            "prompt_caching": prompt_caching_test,
            "extended_output": extended_output_test,
            "tool_streaming": tool_streaming_test
        },
        "overall_score": passing_tests,
        "passed": passing_tests >= 3
    }
    
    report_path = test_dir / "phase2_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Test report saved to {report_path}")
    
    # Return success if at least 3/4 tests pass
    sys.exit(0 if passing_tests >= 3 else 1)

if __name__ == "__main__":
    main()