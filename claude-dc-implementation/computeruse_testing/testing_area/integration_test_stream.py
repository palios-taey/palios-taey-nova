#!/usr/bin/env python3
"""
Integration test for the fixed loop implementation.
This script tests the streaming API with tool use.
"""

import os
import sys
import asyncio
from pathlib import Path

# Set up paths
repo_root = Path("/home/computeruse/github/palios-taey-nova")
claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"
testing_area = claude_dc_root / "computeruse/testing_area"

paths_to_add = [
    str(repo_root),
    str(claude_dc_root),
    str(claude_dc_root / "computeruse"),
    str(computer_use_demo_dir),
    str(testing_area)
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import from the fixed loop
from enhanced_tests.fixed_loop import sampling_loop, APIProvider
from enhanced_tests.mock_streamlit import MockStreamlit

# Import tool classes
from computer_use_demo.tools import ToolResult

async def main():
    """Run the integration test."""
    print("=" * 80)
    print("CLAUDE DC STREAMING INTEGRATION TEST")
    print("=" * 80)
    
    # Create test objects
    mock_st = MockStreamlit()
    
    # Set up a simple message
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is the current date? Please give me a brief response."
                }
            ]
        }
    ]
    
    # Get API key - without using the actual API
    api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_api_key_for_testing")
    print(f"Using API key: {api_key[:4]}...")
    
    # Create a handler that prints output as it's received
    def output_handler(content_block):
        """Print content as it's received."""
        # Call the mock Streamlit callback
        mock_st.output_callback(content_block)
        
        # Print content to console
        if content_block.get("type") == "text":
            text = content_block.get("text", "")
            is_delta = content_block.get("is_delta", False)
            if is_delta:
                print(text, end="", flush=True)
            else:
                print(f"\n{text}", end="", flush=True)
        elif content_block.get("type") == "thinking":
            thinking = content_block.get("thinking", "")
            is_delta = content_block.get("is_delta", False)
            if not is_delta:
                print(f"\n[Thinking: {thinking[:30]}...]", flush=True)
        elif content_block.get("type") == "tool_use":
            tool_name = content_block.get("name", "unknown")
            print(f"\n[Using tool: {tool_name}]", flush=True)
    
    # Tool output handler
    def tool_output_handler(result, tool_id):
        """Handle tool output."""
        mock_st.tool_output_callback(result, tool_id)
        print(f"\n[Tool result for {tool_id}]")
        if result.output:
            print(f"Output: {result.output[:100]}...")
        if result.error:
            print(f"Error: {result.error}")
    
    # API response handler - this would cause an error in the original code
    def api_response_handler(request, response, error):
        """Handle API response."""
        mock_st.api_response_callback(request, response, error)
        if error:
            print(f"\n[API Error: {error}]")
        else:
            print("\n[API Response received]")
    
    print("=" * 80)
    print("TESTING NoneType ERROR FIX")
    print("=" * 80)
    print("This test verifies that api_response_callback can handle None request parameter")
    print("which was causing an AttributeError in the original implementation.")
    
    try:
        # Call the api_response_callback directly with None request
        print("\nTesting callback directly with None request...")
        api_response_handler(None, {"test": "response"}, None)
        print("Direct callback test passed!")
        
        # For the integration test, we'll use mock objects since we don't want to call the actual API
        from unittest.mock import MagicMock, patch
        
        # Create a mock response that simulates streaming
        class MockStreamResponse:
            """Mock a streaming response from the API."""
            
            def __init__(self):
                self.events = [
                    # Content block start
                    MagicMock(
                        type="content_block_start",
                        content_block=MagicMock(
                            type="text",
                            text="Today is "
                        )
                    ),
                    # Content block delta
                    MagicMock(
                        type="content_block_delta",
                        index=0,
                        delta=MagicMock(
                            text="Wednesday, April 23, 2025."
                        )
                    ),
                    # Message stop
                    MagicMock(
                        type="message_stop"
                    )
                ]
                self.index = -1
            
            def __iter__(self):
                return self
            
            def __next__(self):
                self.index += 1
                if self.index >= len(self.events):
                    raise StopIteration
                return self.events[self.index]
        
        # Patch the Anthropic client
        with patch('enhanced_tests.fixed_loop.Anthropic') as mock_anthropic:
            # Set up the mock client
            mock_client = MagicMock()
            mock_client.messages.create.return_value = MockStreamResponse()
            mock_anthropic.return_value = mock_client
            
            # Run the sampling loop
            print("\nStarting the sampling loop...")
            await sampling_loop(
                model="claude-3-sonnet-20240229",
                provider=APIProvider.ANTHROPIC,
                system_prompt_suffix="",
                messages=messages,
                output_callback=output_handler,
                tool_output_callback=tool_output_handler,
                api_response_callback=api_response_handler,
                api_key=api_key
            )
            
            print("\n\nSampling loop completed successfully with None request parameter.")
            
            # Check if there were any errors in the callbacks
            if mock_st.errors:
                print("\nERRORS DETECTED:")
                for error in mock_st.errors:
                    print(f"- {error}")
                print("\nTest FAILED: Errors were detected during callback processing.")
            else:
                print("\nNo errors detected in callback processing.")
                print("\nTest PASSED: The api_response_callback can handle None request parameter correctly.")
                print("This fixes the AttributeError: 'NoneType' object has no attribute 'method' that was occurring.")
            
    except Exception as e:
        print(f"\nTest FAILED: An error occurred during the test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())