#!/usr/bin/env python3
"""
Test script for the enhanced streaming implementation with research-based improvements.

This script tests the fixed streaming implementation with various test cases to verify:
1. Proper handling of missing/invalid command parameter
2. Improved parameter extraction from user messages using reliability-based patterns
3. Robust error handling with clear, actionable error messages
4. Correct tool_use_id tracking for proper conversation state management
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("streaming_test")

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import unified streaming loop
try:
    from streaming.unified_streaming_loop_fixed import unified_streaming_agent_loop
    from streaming.tools.dc_bash_fixed import dc_execute_bash_tool_streaming
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this from the correct directory")
    sys.exit(1)


async def test_bash_tool_directly():
    """Test the bash tool implementation directly with various parameter formats."""
    print("\n=== Testing Bash Tool Directly ===\n")
    
    # Test cases for bash tool
    test_cases = [
        # Valid cases
        {"command": "ls -la"},
        {"command": "echo 'Hello World'"},
        
        # Invalid cases - should produce helpful error messages
        {},  # Empty params
        {"prompt": "ls -la"},  # Wrong parameter name
        {"command": ""},  # Empty command
        {"command": None},  # Non-string command
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {test_case} ---\n")
        
        try:
            # Execute the tool with test case
            print("Output:")
            async for chunk in dc_execute_bash_tool_streaming(test_case):
                print(chunk, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_parameter_extraction():
    """Test parameter extraction from user messages using reliability-based patterns."""
    print("\n=== Testing Parameter Extraction (Research-Based Patterns) ===\n")
    
    # Import the function directly to test without API calls
    from streaming.unified_streaming_loop_fixed import set_default_tool_parameters
    
    # Test cases for parameter extraction with confidence levels
    test_cases = [
        # High confidence test cases (quotes)
        {"message": "Run the command 'ls -la'", "expected_success": True, "expected_confidence": "HIGH"},
        {"message": "Please execute \"echo 'Hello World'\"", "expected_success": True, "expected_confidence": "HIGH"},
        {"message": "Check this: `cat /etc/hosts`", "expected_success": True, "expected_confidence": "HIGH"},
        
        # Medium confidence test cases (action phrases)
        {"message": "Run the ls -la command", "expected_success": True, "expected_confidence": "MEDIUM"},
        {"message": "Please execute echo 'Hello World'", "expected_success": True, "expected_confidence": "MEDIUM"},
        {"message": "Type pwd to see the current directory", "expected_success": True, "expected_confidence": "MEDIUM"},
        {"message": "Use grep pattern file.txt to find matches", "expected_success": True, "expected_confidence": "MEDIUM"},
        
        # Medium confidence test cases (common commands)
        {"message": "ls -la will show all files including hidden ones", "expected_success": True, "expected_confidence": "MEDIUM"},
        {"message": "grep -r 'searchterm' /path will recursively search", "expected_success": True, "expected_confidence": "MEDIUM"},
        
        # Low confidence / expected failures
        {"message": "I'd like to see what's in the directory", "expected_success": False, "expected_confidence": None},
        {"message": "Show me the system status", "expected_success": False, "expected_confidence": None},
    ]
    
    results = []
    
    print("Testing parameter extraction directly (no API calls):")
    for i, test_case in enumerate(test_cases):
        message = test_case["message"]
        expected_success = test_case["expected_success"]
        expected_confidence = test_case["expected_confidence"]
        
        print(f"\n--- Test Case {i+1}: \"{message}\" ---")
        print(f"  Expected: Success={expected_success}, Confidence={expected_confidence}")
        
        # Create a conversation history with the test message
        conversation_history = [
            {"role": "user", "content": message}
        ]
        
        # Create empty tool input to simulate missing parameters
        tool_input = {}
        
        # Call the extraction function directly
        updated_tool_input = set_default_tool_parameters("dc_bash", tool_input, conversation_history)
        
        # Check if command was extracted
        if "command" in updated_tool_input and updated_tool_input["command"] and \
           not updated_tool_input["command"].startswith("echo 'Error"):
            # Command extracted successfully
            success = True
            # Determine confidence level from log (simplified check)
            command = updated_tool_input["command"]
            print(f"  Result: SUCCESS - Command extracted: '{command}'")
            results.append({"message": message, "success": True, "command": command})
        else:
            # Command extraction failed
            success = False
            print(f"  Result: FAILED - Could not extract command")
            results.append({"message": message, "success": False})
        
        # Check if result matches expectation
        if success == expected_success:
            print(f"  ✅ Test PASSED")
        else:
            print(f"  ❌ Test FAILED")
    
    print("\n=== Parameter Extraction Summary ===")
    print(f"Total test cases: {len(test_cases)}")
    successful_extractions = sum(1 for r in results if r.get("success", False))
    print(f"Successful extractions: {successful_extractions}")
    print(f"Failed extractions: {len(results) - successful_extractions}")
    
    # Now test with the actual API if key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("\nTesting full agent loop with parameter extraction (uses API):")
        
        # Select a few representative test cases for API testing
        api_test_cases = [
            {"message": "Run the command 'ls -la'", "expected_success": True},
            {"message": "Please execute echo 'Hello World'", "expected_success": True},
            {"message": "I'd like to see what's in the directory", "expected_success": False},
        ]
        
        for i, test_case in enumerate(api_test_cases):
            message = test_case["message"]
            
            print(f"\n--- API Test Case {i+1}: \"{message}\" ---\n")
            
            # Create a conversation history with the test message
            conversation_history = [
                {"role": "user", "content": message}
            ]
            
            try:
                # Call the streaming agent with empty tool input but extraction from history
                print("Response:")
                updated_history = await unified_streaming_agent_loop(
                    user_input="",  # No new user input
                    conversation_history=conversation_history,
                    api_key=api_key,
                    max_tokens=1000,
                    thinking_budget=None  # Disable thinking for tool use
                )
                
                # Check if tool was used
                tool_used = False
                for msg in updated_history:
                    if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                        for block in msg.get("content", []):
                            if block.get("type") == "tool_use":
                                tool_name = block.get("name", "")
                                tool_input = block.get("input", {})
                                if tool_name == "dc_bash" and "command" in tool_input:
                                    tool_used = True
                                    print(f"\nTool used successfully with command: {tool_input['command']}")
                
                if not tool_used:
                    print("\nNo tool use detected or parameter extraction failed.")
                    
            except Exception as e:
                print(f"Error: {str(e)}")
    else:
        print("\nSkipping API tests: ANTHROPIC_API_KEY not set in environment")


async def test_full_agent_loop():
    """Test the full streaming agent loop with the enhanced implementation."""
    print("\n=== Testing Full Agent Loop ===\n")
    
    # Test messages that should result in tool use
    test_messages = [
        "Run ls -la to show the files in the current directory",
        "What's the content of /etc/hosts?",
        "Show me the system uptime"
    ]
    
    conversation_history = []
    
    for i, message in enumerate(test_messages):
        print(f"\n--- Test {i+1}: \"{message}\" ---\n")
        
        try:
            # Call the unified streaming agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=message,
                conversation_history=conversation_history,
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                max_tokens=1000,
                thinking_budget=None  # Disable thinking for tool use
            )
            
            print("\n")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_tool_use_id_tracking():
    """Test correct tool_use_id tracking during streaming."""
    print("\n=== Testing Tool Use ID Tracking ===\n")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Skipping test: ANTHROPIC_API_KEY not set in environment")
        return
    
    # This test specifically checks that tool_use_id is properly tracked in the conversation history
    print("This test verifies proper tool_use_id tracking in conversation history")
    print("It sends a message that should trigger tool use, then analyzes the conversation history\n")
    
    # Clear message that should trigger tool use with a simple command
    user_message = "Run the 'echo test' command"
    print(f"User message: \"{user_message}\"")
    
    try:
        # Call the streaming agent
        conversation_history = await unified_streaming_agent_loop(
            user_input=user_message,
            conversation_history=[],  # Start with empty history
            api_key=api_key,
            max_tokens=1000,
            thinking_budget=None  # Disable thinking for tool use
        )
        
        print("\nAnalyzing conversation history structure...")
        
        # Analyze the conversation history structure
        tool_use_entries = []
        tool_result_entries = []
        
        for i, msg in enumerate(conversation_history):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            print(f"Message {i+1}: role={role}")
            
            # Extract tool_use entries
            if role == "assistant" and isinstance(content, list):
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_id = block.get("id", "")
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        tool_use_entries.append({
                            "index": i,
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_input
                        })
                        print(f"  - Found tool_use: id={tool_id}, name={tool_name}")
            
            # Extract tool_result entries
            if role == "user" and isinstance(content, list):
                for block in content:
                    if block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id", "")
                        tool_result_entries.append({
                            "index": i,
                            "tool_use_id": tool_use_id
                        })
                        print(f"  - Found tool_result: tool_use_id={tool_use_id}")
        
        # Check for proper matching of tool_use_id
        if tool_use_entries and tool_result_entries:
            # Verify each tool_result has a matching tool_use
            matches = 0
            for result in tool_result_entries:
                result_id = result.get("tool_use_id", "")
                for use in tool_use_entries:
                    if use.get("id", "") == result_id:
                        matches += 1
                        print(f"\n✅ Found matching tool_use for tool_result with id={result_id}")
                        break
                else:
                    print(f"\n❌ No matching tool_use found for tool_result with tool_use_id={result_id}")
            
            # Summary
            if matches == len(tool_result_entries):
                print("\n✅ All tool_result entries have matching tool_use entries")
                print("✅ Tool use ID tracking is working correctly")
            else:
                print(f"\n❌ Only {matches} out of {len(tool_result_entries)} tool_result entries have matching tool_use entries")
                print("❌ Tool use ID tracking may have issues")
        else:
            print("\n❌ No tool use detected in conversation history")
            print("The test failed to trigger tool usage")
        
    except Exception as e:
        print(f"Error: {str(e)}")


async def main():
    """Main test function."""
    print("=== Enhanced Streaming Implementation Tests (Research-Based) ===")
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set in environment")
        print("Some tests will be skipped or limited.")
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
    
    # Select test to run
    print("\nSelect a test to run:")
    print("1. Test bash tool directly (parameter validation)")
    print("2. Test parameter extraction (research-based patterns)")
    print("3. Test full agent loop (complete streaming)")
    print("4. Test tool_use_id tracking (conversation structure)")
    print("5. Run all tests")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        await test_bash_tool_directly()
    elif choice == "2":
        await test_parameter_extraction()
    elif choice == "3":
        await test_full_agent_loop()
    elif choice == "4":
        await test_tool_use_id_tracking()
    elif choice == "5":
        await test_bash_tool_directly()
        await test_parameter_extraction()
        await test_full_agent_loop()
        await test_tool_use_id_tracking()
    else:
        print("Invalid choice. Please run again and select 1-5.")


if __name__ == "__main__":
    # Make the script executable
    if not os.access(__file__, os.X_OK):
        os.chmod(__file__, 0o755)
    
    asyncio.run(main())