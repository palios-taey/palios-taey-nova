#!/usr/bin/env python3
"""
Test script for the buffer pattern in the unified streaming loop.

This script tests the buffer pattern's handling of partial function calls
during streaming, ensuring that they are only executed when complete.
"""

import os
import asyncio
import logging
import json
from typing import Dict, Any, List

from streaming.unified_streaming_loop import SimpleToolBuffer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_buffer")

def create_mock_delta(partial_json=None, type="input_json_delta", tool_use_id=None):
    """Create a mock delta object."""
    class MockDelta:
        pass
    
    delta = MockDelta()
    delta.type = type
    delta.partial_json = partial_json
    delta.tool_use_id = tool_use_id
    return delta

async def test_simple_json_command():
    """Test buffering a simple JSON bash command."""
    print("\n=> Testing simple JSON command buffering")
    
    # Create buffer
    buffer = SimpleToolBuffer()
    
    # Create mock deltas that simulate the streaming API
    deltas = [
        (1, create_mock_delta(partial_json='{"', tool_use_id="tool_1")),
        (1, create_mock_delta(partial_json='command', tool_use_id="tool_1")),
        (1, create_mock_delta(partial_json='": "ls -la', tool_use_id="tool_1")),
        (1, create_mock_delta(partial_json='"', tool_use_id="tool_1")),
        (1, create_mock_delta(partial_json='}', tool_use_id="tool_1")),
    ]
    
    # Process delta events
    for index, delta in deltas:
        result = buffer.process_content_block_delta(index, delta)
        if result:
            print(f"Buffered partial JSON: {result['buffer']}")
            print(f"Is complete: {result['is_complete']}\n")
    
    # Process stop event
    result = buffer.process_content_block_stop(1)
    
    # Check result
    if result and result["type"] == "complete_tool_call":
        print(f"Complete tool call detected!")
        print(f"Tool name: {result['tool_name']}")
        print(f"Tool parameters: {result['tool_params']}")
        print(f"Tool use ID: {result['tool_use_id']}")
        print(f"Is complete: {result['is_complete']}")
        
        # Also test parameter validation
        is_valid, message, fixed_params = buffer.validate_tool_parameters(
            result["tool_name"], 
            result["tool_params"]
        )
        print(f"Parameter validation: {message}")
    else:
        print(f"Error: Expected complete tool call, got {result}")

async def test_xml_function_call():
    """Test buffering an XML function call."""
    print("\n=> Testing XML function call buffering")
    
    # Create buffer
    buffer = SimpleToolBuffer()
    
    # Create mock deltas for XML function call
    xml_deltas = [
        (2, create_mock_delta(partial_json='<function_calls>', tool_use_id="tool_2")),
        (2, create_mock_delta(partial_json='<invoke name="dc_bash">', tool_use_id="tool_2")),
        (2, create_mock_delta(partial_json='<parameter name="command">echo "Hello"</parameter>', tool_use_id="tool_2")),
        (2, create_mock_delta(partial_json='</invoke></function_calls>', tool_use_id="tool_2")),
    ]
    
    # Process delta events
    for index, delta in xml_deltas:
        result = buffer.process_content_block_delta(index, delta)
        if result:
            print(f"Buffered partial XML: {result['buffer']}")
            print(f"Is complete: {result['is_complete']}\n")
    
    # Process stop event
    result = buffer.process_content_block_stop(2)
    
    # Check result
    if result and result["type"] == "complete_tool_call":
        print(f"Complete XML tool call detected!")
        print(f"Tool name: {result['tool_name']}")
        print(f"Tool parameters: {result['tool_params']}")
        print(f"Tool use ID: {result['tool_use_id']}")
        print(f"Format: {result['format']}")
        print(f"Is complete: {result['is_complete']}")
    else:
        print(f"Error: Expected complete tool call, got {result}")

async def test_invalid_json():
    """Test handling invalid JSON."""
    print("\n=> Testing invalid JSON handling")
    
    # Create buffer
    buffer = SimpleToolBuffer()
    
    # Create mock deltas for invalid JSON
    invalid_deltas = [
        (3, create_mock_delta(partial_json='{"command":', tool_use_id="tool_3")),
        (3, create_mock_delta(partial_json=' "ls -la"', tool_use_id="tool_3")),
        # Missing closing brace
    ]
    
    # Process delta events
    for index, delta in invalid_deltas:
        result = buffer.process_content_block_delta(index, delta)
        if result:
            print(f"Buffered partial JSON: {result['buffer']}")
            print(f"Is complete: {result['is_complete']}\n")
    
    # Process stop event
    result = buffer.process_content_block_stop(3)
    
    # Check result
    if result and result["type"] == "tool_call_error":
        print(f"Tool call error detected (expected)!")
        print(f"Error: {result['error']}")
        print(f"Buffer: {result['buffer']}")
        print(f"Is complete: {result['is_complete']}")
    else:
        print(f"Error: Expected tool call error, got {result}")

async def test_parameter_validation():
    """Test parameter validation and recovery."""
    print("\n=> Testing parameter validation and recovery")
    
    # Create buffer
    buffer = SimpleToolBuffer()
    
    # Test with missing command but alternative field
    params = {"bash": "ls -la"}
    is_valid, message, fixed_params = buffer.validate_tool_parameters("dc_bash", params)
    
    print(f"Validation result for alternative field: {is_valid}")
    print(f"Message: {message}")
    print(f"Fixed params: {fixed_params}")
    
    # Test with missing required parameter
    params = {"foo": "bar"}
    is_valid, message, fixed_params = buffer.validate_tool_parameters("dc_bash", params)
    
    print(f"Validation result for missing parameter: {is_valid}")
    print(f"Message: {message}")
    print(f"Fixed params: {fixed_params}")

async def main():
    """Run all tests."""
    print("===== Buffer Pattern Tests =====")
    
    await test_simple_json_command()
    await test_xml_function_call()
    await test_invalid_json()
    await test_parameter_validation()
    
    print("\n===== All Tests Complete =====")

if __name__ == "__main__":
    asyncio.run(main())