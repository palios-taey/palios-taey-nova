#!/usr/bin/env python3
"""
Simple test script for the enhanced bridge module.
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Configure paths
sys.path.insert(0, str(Path(__file__).parent))

# Import the enhanced bridge
from enhanced_bridge import (
    execute_tool,
    get_metrics,
    set_feature_toggle,
    get_feature_toggles,
    clear_cache
)

async def test_basic_functionality():
    """Test basic functionality"""
    print("\n=== Testing Basic Functionality ===")
    
    # Test computer tool
    print("\nTesting computer tool (screenshot)...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Test bash tool
    print("\nTesting bash tool...")
    result = await execute_tool("dc_bash", {"command": "echo Hello from Enhanced Bridge"})
    print(f"Result: {result}")
    
    # Test feature toggles
    print("\nGetting feature toggles...")
    toggles = await get_feature_toggles()
    print(f"Feature toggles: {json.dumps(toggles, indent=2)}")
    
    # Set a toggle
    print("\nDisabling custom implementation...")
    await set_feature_toggle("use_custom_implementation", False)
    
    # Test with toggle disabled
    print("\nTesting with custom implementation disabled...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Re-enable toggle
    print("\nRe-enabling custom implementation...")
    await set_feature_toggle("use_custom_implementation", True)
    
    # Test metrics
    print("\nGetting metrics...")
    metrics = await get_metrics()
    print("Metrics collected successfully")

async def main():
    """Main entry point"""
    print("=== Enhanced Bridge Test ===")
    
    try:
        await test_basic_functionality()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())