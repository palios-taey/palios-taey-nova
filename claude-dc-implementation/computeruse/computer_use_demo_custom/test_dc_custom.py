"""
Test script for DC Custom Implementation.
"""

import asyncio
from dc_bridge.bridge import execute_tool

async def test_dc_custom():
    """Test the DC Custom Implementation"""
    print("Testing DC Custom Implementation")
    
    # Test computer tool
    print("Testing computer tool...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Test bash tool
    print("Testing bash tool...")
    result = await execute_tool("dc_bash", {"command": "echo Hello from DC Custom"})
    print(f"Result: {result}")
    
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(test_dc_custom())
