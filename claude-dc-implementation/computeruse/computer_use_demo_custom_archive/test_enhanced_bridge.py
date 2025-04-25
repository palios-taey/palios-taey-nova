#!/usr/bin/env python3
"""
Test script for the enhanced bridge implementation.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Test the enhanced bridge implementation."""
    print("\n=== Testing Enhanced Bridge Implementation ===\n")
    
    # Import the enhanced bridge
    try:
        from dc_bridge.enhanced_bridge import (
            execute_tool,
            get_metrics,
            get_feature_toggles,
            set_feature_toggle
        )
        
        # Test computer tool
        print("\nTesting computer tool (screenshot)...")
        result = await execute_tool("dc_computer", {"action": "screenshot"})
        print(f"Result: {result}")
        
        # Test bash tool
        print("\nTesting bash tool...")
        result = await execute_tool("dc_bash", {"command": "echo Hello from Enhanced Bridge"})
        print(f"Result: {result}")
        
        # Get feature toggles
        print("\nGetting feature toggles...")
        toggles = await get_feature_toggles()
        print(f"Feature toggles: {json.dumps(toggles, indent=2)}")
        
        # Get metrics
        print("\nGetting metrics...")
        metrics = await get_metrics()
        print("Metrics collected successfully")
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
