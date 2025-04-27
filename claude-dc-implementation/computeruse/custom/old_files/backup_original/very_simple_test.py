#!/usr/bin/env python3
"""
Very simple test script for the enhanced bridge module.
"""

import asyncio
import sys
from pathlib import Path

# Configure paths
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    # Import the enhanced bridge
    from enhanced_bridge import execute_tool
    
    # Test computer tool
    print("\nTesting computer tool (screenshot)...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Test bash tool
    print("\nTesting bash tool...")
    result = await execute_tool("dc_bash", {"command": "echo Hello from Enhanced Bridge"})
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())