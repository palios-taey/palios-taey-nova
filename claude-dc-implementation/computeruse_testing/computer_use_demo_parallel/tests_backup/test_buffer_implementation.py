#!/usr/bin/env python3
"""
Test the buffer implementation for handling tool calls during streaming.
This simulates streaming events to test our ToolCallBuffer class.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("buffer_test")

# Add the streaming directory to sys.path
streaming_dir = str(Path(__file__).parent)
sys.path.append(streaming_dir)

# Import the tool buffer
from streaming.tool_buffer import ToolCallBuffer

class MockDelta:
    """Mock delta object for testing."""
    
    def __init__(self, type_val, partial_json, tool_use_id=None):
        self.type = type_val
        self.partial_json = partial_json
        if tool_use_id:
            self.tool_use_id = tool_use_id

async def test_xml_buffer():
    """Test the buffer with XML function calls."""
    print("\n=== Testing XML Function Call Buffer ===\n")
    
    # Create a buffer
    buffer = ToolCallBuffer()
    
    # Test XML function call over multiple deltas
    xml_parts = [
        '<function_calls>',
        '<invoke name="dc_bash">',
        '<parameter name="command">',
        'ls -la',
        '</parameter>',
        '</invoke>',
        '</function_calls>'
    ]
    
    print("Simulating XML function call with parts:")
    
    # Process each part as a delta
    for i, part in enumerate(xml_parts):
        print(f"  Part {i+1}: {part}")
        delta = MockDelta("input_json_delta", part, "tool_123" if i == 0 else None)
        result = buffer.process_content_block_delta(index=1, delta=delta)
        
        # Check the result
        print(f"    Buffer state: {result['type']}, content length: {len(result.get('buffer', ''))}")
    
    # Process the content block stop event
    print("\nSimulating content_block_stop event")
    result = buffer.process_content_block_stop(index=1)
    
    # Check the result
    if result:
        print(f"Result type: {result['type']}")
        if result['type'] == 'complete_xml':
            print(f"Tool name: {result['tool_name']}")
            print(f"Tool params: {result['tool_params']}")
            print(f"Tool use ID: {result['tool_use_id']}")
            
            # Validate parameters
            is_valid, message, validated_params = buffer.validate_tool_parameters(
                result['tool_name'], result['tool_params']
            )
            print(f"Parameter validation: {is_valid} - {message}")
            print(f"Validated params: {validated_params}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print("No result from content_block_stop")
    
    print("\nXML buffer test completed!")

async def test_partial_xml_buffer():
    """Test the buffer with partial XML function calls."""
    print("\n=== Testing Partial XML Function Call Buffer ===\n")
    
    # Create a buffer
    buffer = ToolCallBuffer()
    
    # Test incomplete XML function call
    xml_parts = [
        '<function_calls>',
        '<invoke name="dc_bash">',
        '<parameter name="command">',
        'ls -la'
        # Missing closing tags
    ]
    
    print("Simulating incomplete XML function call:")
    
    # Process each part as a delta
    for i, part in enumerate(xml_parts):
        print(f"  Part {i+1}: {part}")
        delta = MockDelta("input_json_delta", part, "tool_456" if i == 0 else None)
        result = buffer.process_content_block_delta(index=2, delta=delta)
        
        # Check the result
        print(f"    Buffer state: {result['type']}, content length: {len(result.get('buffer', ''))}")
    
    # Process the content block stop event
    print("\nSimulating content_block_stop event")
    result = buffer.process_content_block_stop(index=2)
    
    # Check the result
    if result:
        print(f"Result type: {result['type']}")
        if result['type'] == 'partial_xml':
            print(f"Partial content: {result.get('buffer', '')}")
            print(f"Tool use ID: {result['tool_use_id']}")
        else:
            print(f"Unexpected result type: {result['type']}")
    else:
        print("No result from content_block_stop")
    
    print("\nPartial XML buffer test completed!")

async def test_json_buffer():
    """Test the buffer with JSON function calls."""
    print("\n=== Testing JSON Function Call Buffer ===\n")
    
    # Create a buffer
    buffer = ToolCallBuffer()
    
    # Test JSON function call over multiple deltas
    json_parts = [
        '{',
        '"tool": "dc_bash", ',
        '"parameters": {',
        '"command": "',
        'ls -la',
        '"',
        '}}'
    ]
    
    print("Simulating JSON function call with parts:")
    
    # Process each part as a delta
    for i, part in enumerate(json_parts):
        print(f"  Part {i+1}: {part}")
        delta = MockDelta("input_json_delta", part, "tool_789" if i == 0 else None)
        result = buffer.process_content_block_delta(index=3, delta=delta)
        
        # Check the result
        print(f"    Buffer state: {result['type']}, content length: {len(result.get('buffer', ''))}")
    
    # Process the content block stop event
    print("\nSimulating content_block_stop event")
    result = buffer.process_content_block_stop(index=3)
    
    # Check the result
    if result:
        print(f"Result type: {result['type']}")
        if result['type'] == 'complete_json':
            print(f"Tool name: {result['tool_name']}")
            print(f"Tool params: {result['tool_params']}")
            print(f"Tool use ID: {result['tool_use_id']}")
            
            # Validate parameters
            is_valid, message, validated_params = buffer.validate_tool_parameters(
                result['tool_name'], result['tool_params']
            )
            print(f"Parameter validation: {is_valid} - {message}")
            print(f"Validated params: {validated_params}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print("No result from content_block_stop")
    
    print("\nJSON buffer test completed!")

async def main():
    """Run all tests."""
    # Test XML function calls
    await test_xml_buffer()
    
    # Test partial XML function calls
    await test_partial_xml_buffer()
    
    # Test JSON function calls
    await test_json_buffer()
    
    print("\nAll buffer tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())