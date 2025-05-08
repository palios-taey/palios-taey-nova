"""
Simple demo script to showcase the buffer pattern implementation.

This script simulates streaming events with a partial tool call to demonstrate
how the buffer pattern prevents premature execution of incomplete function calls.
"""

import asyncio
import logging
from streaming.buffer_pattern import ToolCallBuffer
from types import SimpleNamespace

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("buffer_demo")

async def simulate_streaming_events():
    """Simulate streaming events with a tool call that's sent in chunks."""
    # Initialize the buffer
    buffer = ToolCallBuffer()
    
    # Create demo events for a dc_bash command
    # These simulate how Claude DC might send partial JSON chunks during streaming
    events = [
        # First chunk with opening brace
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='{"',
                tool_use_id="tool_1"
            )
        ),
        
        # Second chunk with partial command parameter
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='command": "ls',
                tool_use_id="tool_1"
            )
        ),
        
        # Third chunk completing the command
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json=' -la"}',
                tool_use_id="tool_1"
            )
        ),
        
        # Content block stop event
        SimpleNamespace(
            type="content_block_stop",
            index=0
        )
    ]
    
    # Process each event
    for event in events:
        print(f"\n--- Processing event: {event.type} ---")
        
        if event.type == "content_block_delta":
            print(f"Partial JSON: '{event.delta.partial_json}'")
            result = buffer.process_content_block_delta(event.index, event.delta)
            if result:
                print(f"Buffer now contains: '{result['buffer']}'")
                print(f"Is complete: {result['is_complete']}")
        
        elif event.type == "content_block_stop":
            result = buffer.process_content_block_stop(event.index)
            
            if result and result["type"] == "complete_tool_call":
                print("COMPLETE TOOL CALL DETECTED!")
                print(f"Tool name: {result['tool_name']}")
                print(f"Tool parameters: {result['tool_params']}")
                print(f"Is complete: {result['is_complete']}")
                
                # Validate parameters
                is_valid, message, params = buffer.validate_tool_parameters(
                    result["tool_name"], 
                    result["tool_params"]
                )
                print(f"Parameter validation: {message}")
                
                # NOW is the safe time to execute the tool!
                print("\nSafely executing tool with complete parameters...")
                print(f"$ {params.get('command')}")
            
            elif result and result["type"] == "tool_call_error":
                print(f"ERROR: {result['error']}")

async def main():
    """Main demo function."""
    print("\n====== Buffer Pattern Demo ======\n")
    print("This demo shows how the buffer pattern prevents race conditions")
    print("by accumulating partial function calls before execution.")
    
    await simulate_streaming_events()
    
    print("\n\n====== Demo with XML Function Call ======\n")
    
    # Initialize a new buffer for XML demo
    buffer = ToolCallBuffer()
    
    # Create XML in chunks
    xml_events = [
        # First chunk with opening tag
        SimpleNamespace(
            type="content_block_delta",
            index=1,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='<function_calls><invoke name="dc_bash">',
                tool_use_id="tool_2"
            )
        ),
        
        # Second chunk with parameter
        SimpleNamespace(
            type="content_block_delta",
            index=1,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='<parameter name="command">echo "Hello World"</parameter>',
                tool_use_id="tool_2"
            )
        ),
        
        # Third chunk completing XML
        SimpleNamespace(
            type="content_block_delta",
            index=1,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='</invoke></function_calls>',
                tool_use_id="tool_2"
            )
        ),
        
        # Content block stop event
        SimpleNamespace(
            type="content_block_stop",
            index=1
        )
    ]
    
    # Process XML events
    for event in xml_events:
        print(f"\n--- Processing event: {event.type} ---")
        
        if event.type == "content_block_delta":
            print(f"Partial XML: '{event.delta.partial_json}'")
            result = buffer.process_content_block_delta(event.index, event.delta)
            if result:
                print(f"Buffer now contains: '{result['buffer']}'")
        
        elif event.type == "content_block_stop":
            result = buffer.process_content_block_stop(event.index)
            
            if result and result["type"] == "complete_tool_call":
                print("COMPLETE XML FUNCTION CALL DETECTED!")
                print(f"Tool name: {result['tool_name']}")
                print(f"Tool parameters: {result['tool_params']}")
                
                # NOW is the safe time to execute the tool!
                print("\nSafely executing tool with complete parameters...")
                print(f"$ {result['tool_params'].get('command')}")
    
    print("\n\nBuffer pattern successfully prevented race conditions!")

if __name__ == "__main__":
    asyncio.run(main())