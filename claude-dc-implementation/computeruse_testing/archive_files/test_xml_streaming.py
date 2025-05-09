#!/usr/bin/env python3
"""
Test script for the XML-style function call support in streaming.

This script tests the enhanced buffer pattern implementation
that supports XML-based function calls during streaming.
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
        logging.FileHandler("test_xml_streaming.log")
    ]
)
logger = logging.getLogger("test_xml_streaming")

# Add streaming directory to path
streaming_dir = Path(__file__).parent / "streaming"
if str(streaming_dir) not in sys.path:
    sys.path.insert(0, str(streaming_dir))

# Import the XML-enhanced streaming implementation using direct imports
try:
    from unified_streaming_loop import unified_streaming_agent_loop
    from tool_call_buffer import ToolCallBuffer
    from xml_tool_validator import validate_xml_structure
    XML_STREAMING_AVAILABLE = True
    logger.info("XML-enhanced streaming implementation loaded successfully")
except Exception as e:
    logger.error(f"Error loading XML-enhanced streaming implementation: {str(e)}")
    XML_STREAMING_AVAILABLE = False

async def test_xml_streaming():
    """Test the XML-enhanced streaming implementation with tool usage."""
    
    if not XML_STREAMING_AVAILABLE:
        print("XML-enhanced streaming implementation not available.")
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
        except Exception as e:
            logger.error(f"Error loading API key: {str(e)}")
            print(f"Error loading API key: {str(e)}")
    
    if not api_key:
        print("API key not found. Unable to continue.")
        return
    
    # Define test prompts designed to test XML function calls
    test_prompts = [
        # Basic bash tool use with explicit instructions to use XML format
        "Run the 'ls -la' command and tell me what files are in the current directory. Use the XML function call format.",
        
        # Test with more complex command
        "Show me all Python files in the current directory using the ls command. Make sure to use the correct XML function call format.",
        
        # Test with command that requires parameter extraction
        "Tell me how much disk space is being used on this system. Use the XML function call syntax.",
        
        # Test with complex command that tests the XML buffer pattern
        "Run a command to find all Python files in the current directory and count them. Use XML function call format.",
        
        # Test with explicit syntax reminder
        "Run the command 'ps aux | grep python' and remember to use the proper XML format with <function_calls> tags.",
    ]
    
    conversation_history = []
    
    print("\n\n===== XML FUNCTION CALL STREAMING TEST =====")
    print("This test verifies the XML function call format implementation")
    print("that helps Claude DC correctly structure function calls during streaming.")
    print("====================================================\n")
    
    # Test the XML validation function directly
    test_xml = """<function_calls>
<invoke name="dc_bash">
<parameter name="command">ls -la</parameter>
</invoke>
</function_calls>"""
    
    is_valid, message, data = validate_xml_structure(test_xml)
    print(f"XML Validation Test: {'Passed' if is_valid else 'Failed'}")
    print(f"Message: {message}")
    print(f"Extracted data: {data}")
    print("\n----------------------------------------------------\n")
    
    # Process each test prompt
    for i, prompt in enumerate(test_prompts):
        print(f"\n\n--- Test {i+1}: {prompt} ---\n")
        
        def on_text(text):
            print(text, end="", flush=True)
        
        def on_thinking(thinking):
            # Show thinking content for debugging
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
                "xml_format": True
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
                "xml_format": True
            }
            logger.error(f"Error summary: {json.dumps(error_summary)}")
    
    # Print overall summary
    print("\n\n===== TEST SUMMARY =====")
    print(f"Total tests attempted: {len(test_prompts)}")
    print(f"With XML function call format: Yes")
    print(f"Model: claude-3-7-sonnet-20250219")
    print(f"Max tokens: 4000, Thinking budget: None (disabled)")
    print("==========================")

if __name__ == "__main__":
    asyncio.run(test_xml_streaming())