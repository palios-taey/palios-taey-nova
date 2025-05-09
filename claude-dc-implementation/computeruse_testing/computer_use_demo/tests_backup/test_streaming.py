#!/usr/bin/env python3
"""
Test script for the streaming implementation with tool usage.

This script provides a direct way to test tool execution during streaming.
It focuses specifically on the bash tool which properly supports streaming output.

Usage:
    ./test_streaming.py           # Run all tests
    ./test_streaming.py 2         # Run only test #2 (bash ls command)
    ./test_streaming.py -h        # Show help
"""

# Add argparse for better command-line help
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test script for the fixed streaming implementation with tool usage."
    )
    parser.add_argument(
        "test_number", 
        nargs="?", 
        type=int, 
        help="Test number to run (1-based index). If not provided, all tests will run."
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    return parser.parse_args()

import os
import sys
import asyncio
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_streaming.log")
    ]
)
logger = logging.getLogger("test_streaming")

# Import the streaming implementation
try:
    from streaming.unified_streaming_loop import unified_streaming_agent_loop
    STREAMING_AVAILABLE = True
    logger.info("Streaming implementation loaded successfully")
except Exception as e:
    logger.error(f"Error loading streaming implementation: {str(e)}")
    STREAMING_AVAILABLE = False

async def test_streaming():
    """Test the streaming implementation with tool usage."""
    
    if not STREAMING_AVAILABLE:
        print("Streaming implementation not available.")
        return
    
    # Load API key
    api_key = None
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
                    print("Warning: API key format doesn't look right")
        except Exception as e:
            logger.error(f"Error loading API key: {str(e)}")
            print(f"Error loading API key: {str(e)}")
    
    if not api_key:
        print("API key not found. Unable to continue.")
        return
    
    # Define test prompts
    test_prompts = [
        # Simple query with no tool use
        "Tell me a brief overview of what Claude DC is.",
        
        # Basic bash tool use
        "Run the 'ls -la' command and explain what each part of the output means.",
        
        # More complex bash command with pipes
        "Run the command 'ps aux | grep python' and explain the output.",
        
        # Bash command with multiple options
        "Use the 'find' command to locate all Python files in the current directory, then explain what each file might be for based on its name.",
        
        # Bash command that might stress-test the streaming implementation
        "Run 'cat /etc/passwd | grep -v nologin | sort' and explain what each user account is for.",
        
        # File tool use (if implemented - currently commented out)
        # "Show me the contents of the feature_toggles.json file."
    ]
    
    conversation_history = []
    
    # Parse command line arguments
    args = parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Determine which tests to run
    test_to_run = None
    if args.test_number is not None:
        test_to_run = args.test_number - 1  # Convert to 0-based index
        if test_to_run < 0 or test_to_run >= len(test_prompts):
            print(f"Invalid test number. Choose between 1 and {len(test_prompts)}.")
            logger.error(f"Invalid test number provided: {args.test_number}")
            return
        logger.info(f"Running single test #{args.test_number}: {test_prompts[test_to_run]}")
    else:
        logger.info(f"Running all {len(test_prompts)} tests")
    
    # Test streaming with selected or all prompts
    test_range = [test_to_run] if test_to_run is not None else range(len(test_prompts))
    for i in test_range:
        prompt = test_prompts[i]
        print(f"\n\n--- Test {i+1}: {prompt} ---\n")
        
        def on_text(text):
            print(text, end="", flush=True)
        
        def on_thinking(thinking):
            # Show more thinking content for better debugging
            thinking_preview = thinking[:100] + "..." if len(thinking) > 100 else thinking
            print(f"\n[Thinking: {thinking_preview}]", flush=True)
        
        def on_tool_use(tool_name, tool_input):
            # Format the tool input for better readability
            input_str = json.dumps(tool_input, indent=2) if isinstance(tool_input, dict) else str(tool_input)
            print(f"\n[Using tool: {tool_name}]", flush=True)
            print(f"[Tool input: {input_str}]", flush=True)
        
        def on_tool_result(tool_name, tool_input, tool_result):
            # Show more details about the tool result
            result_preview = ""
            if hasattr(tool_result, "output") and tool_result.output:
                result_preview = tool_result.output[:50] + "..." if len(tool_result.output) > 50 else tool_result.output
            elif hasattr(tool_result, "error") and tool_result.error:
                result_preview = f"ERROR: {tool_result.error[:50]}..." if len(tool_result.error) > 50 else f"ERROR: {tool_result.error}"
            
            print(f"\n[Tool completed: {tool_name}]", flush=True)
            print(f"[Result preview: {result_preview}]", flush=True)
            
        def on_progress(message, progress):
            # Add progress tracking
            print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
            
        def on_error(error_message, recoverable=False):
            # Handle errors more explicitly
            status = "Recoverable" if recoverable else "Fatal"
            print(f"\n[{status} Error: {error_message}]", flush=True)
        
        try:
            # Run the streaming implementation with the test prompt
            # Disable thinking for tool use tests to avoid API errors
            # The API requires special handling of thinking with tool use
            conversation_history = await unified_streaming_agent_loop(
                user_input=prompt,
                conversation_history=conversation_history,
                api_key=api_key,
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                thinking_budget=None,  # Set to None to disable thinking
                use_real_adapters=True,  # Enable real tool implementations
                callbacks={
                    "on_text": on_text,
                    "on_thinking": on_thinking,
                    "on_tool_use": on_tool_use,
                    "on_tool_result": on_tool_result,
                    "on_progress": on_progress,
                    "on_error": on_error
                }
            )
            
            print("\n\n[Test completed successfully]")
            
            # Log successful test with summary information
            logger.info(f"Test {i+1} completed successfully")
            
            # Add test summary
            test_summary = {
                "test_number": i+1,
                "prompt": prompt,
                "status": "SUCCESS",
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 4000,
                "thinking_budget": None,  # Disabled thinking for tool tests
                "streaming_available": STREAMING_AVAILABLE
            }
            logger.info(f"Test summary: {json.dumps(test_summary)}")
            
        except Exception as e:
            logger.error(f"Error during test: {str(e)}")
            print(f"\n\n[Test failed with error: {str(e)}]")
            
            # Log failed test with details
            error_summary = {
                "test_number": i+1,
                "prompt": prompt,
                "status": "FAILED",
                "error": str(e),
                "streaming_available": STREAMING_AVAILABLE
            }
            logger.error(f"Error summary: {json.dumps(error_summary)}")
    
    # Print overall summary
    print("\n\n===== TEST SUMMARY =====")
    print(f"Total tests attempted: {len(test_range)}")
    print(f"Streaming available: {'Yes' if STREAMING_AVAILABLE else 'No'}")
    print(f"Model: claude-3-7-sonnet-20250219")
    print(f"Max tokens: 4000, Thinking budget: None (disabled)")
    print("==========================")

if __name__ == "__main__":
    asyncio.run(test_streaming())