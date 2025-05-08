#!/usr/bin/env python3
"""
Test script for the enhanced streaming implementation with buffer pattern.

This script provides a direct way to test tool execution during streaming
with the buffer pattern implementation that prevents race conditions.
"""

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
        logging.FileHandler("test_buffer_streaming.log")
    ]
)
logger = logging.getLogger("test_buffer_streaming")

# Import the buffer-enhanced streaming implementation
try:
    from streaming.unified_streaming_loop import unified_streaming_agent_loop
    from streaming.tool_call_buffer import ToolCallBuffer
    STREAMING_AVAILABLE = True
    logger.info("Buffer-enhanced streaming implementation loaded successfully")
except Exception as e:
    logger.error(f"Error loading buffer-enhanced streaming implementation: {str(e)}")
    STREAMING_AVAILABLE = False

async def test_buffer_streaming():
    """Test the buffer-enhanced streaming implementation with tool usage."""
    
    if not STREAMING_AVAILABLE:
        print("Buffer-enhanced streaming implementation not available.")
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
    
    # Define test prompts designed to test the buffer pattern
    test_prompts = [
        # Basic bash tool use to test buffer pattern
        "Run the 'ls -la' command and tell me what files are in the current directory.",
        
        # Test with partially specified command to verify extraction
        "List all Python files in the current directory.",
        
        # Test with incomplete command specification to test buffer pattern
        "Show me what processes are running on the system right now.",
        
        # Test with explicit command in quotes
        "Please execute 'ps aux | grep python' and explain what each python process is doing.",
        
        # Test with a complex pipe command to stress the buffer pattern
        "Run 'find . -name \"*.py\" | sort | head -5' and tell me what are the first 5 Python files you found.",
    ]
    
    conversation_history = []
    
    print("\n\n===== BUFFER STREAMING TEST =====")
    print("This test verifies the buffer pattern implementation that prevents")
    print("partial tool calls from being executed prematurely during streaming.")
    print("==========================================\n")
    
    # Process each test prompt
    for i, prompt in enumerate(test_prompts):
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
            
            # Add test summary
            test_summary = {
                "test_number": i+1,
                "prompt": prompt,
                "status": "SUCCESS",
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 4000,
                "buffer_pattern": True
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
                "buffer_pattern": True
            }
            logger.error(f"Error summary: {json.dumps(error_summary)}")
    
    # Print overall summary
    print("\n\n===== TEST SUMMARY =====")
    print(f"Total tests attempted: {len(test_prompts)}")
    print(f"With buffer pattern: Yes")
    print(f"Model: claude-3-7-sonnet-20250219")
    print(f"Max tokens: 4000, Thinking budget: None (disabled)")
    print("==========================")

if __name__ == "__main__":
    asyncio.run(test_buffer_streaming())