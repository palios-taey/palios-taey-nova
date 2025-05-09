#!/usr/bin/env python3
"""
Test script for the enhanced bridge module.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from json_helper import json_serialize

# Configure paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the enhanced bridge
try:
    from enhanced_bridge import (
        execute_tool, 
        get_metrics, 
        set_feature_toggle, 
        get_feature_toggles,
        clear_cache
    )
    print("Successfully imported enhanced bridge")
except ImportError as e:
    print(f"Error importing enhanced bridge: {e}")
    sys.exit(1)

async def test_basic_tool_execution():
    """Test basic tool execution"""
    print("\n=== Testing Basic Tool Execution ===")
    
    # Test computer tool
    print("\nTesting computer tool (screenshot)...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Test computer tool with mouse movement
    print("\nTesting computer tool (move_mouse)...")
    result = await execute_tool("dc_computer", {"action": "move_mouse", "coordinates": [100, 200]})
    print(f"Result: {result}")
    
    # Test bash tool
    print("\nTesting bash tool...")
    result = await execute_tool("dc_bash", {"command": "echo Hello from Enhanced Bridge"})
    print(f"Result: {result}")

async def test_feature_toggles():
    """Test feature toggles"""
    print("\n=== Testing Feature Toggles ===")
    
    # Get current toggles
    print("\nGetting current feature toggles...")
    toggles = await get_feature_toggles()
    print(f"Current toggles: {json.dumps(toggles, indent=2)}")
    
    # Test disabling custom implementation
    print("\nDisabling custom implementation...")
    result = await set_feature_toggle("use_custom_implementation", False)
    print(f"Result: {result}")
    
    # Test with custom implementation disabled
    print("\nTesting tool with custom implementation disabled...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Re-enable custom implementation
    print("\nRe-enabling custom implementation...")
    result = await set_feature_toggle("use_custom_implementation", True)
    print(f"Result: {result}")
    
    # Verify toggles
    print("\nVerifying toggles were updated...")
    toggles = await get_feature_toggles()
    print(f"Updated toggles: {json.dumps(toggles, indent=2)}")

async def test_metrics_collection():
    """Test metrics collection"""
    print("\n=== Testing Metrics Collection ===")
    
    # Generate some activity
    print("\nGenerating tool activity...")
    for i in range(5):
        await execute_tool("dc_computer", {"action": "screenshot"})
        await execute_tool("dc_bash", {"command": f"echo Test {i}"})
        await execute_tool("dc_computer", {"action": "move_mouse", "coordinates": [i*100, i*100]})
    
    # Test invalid tool to generate an error
    print("\nTesting invalid tool to generate error metric...")
    await execute_tool("invalid_tool", {})
    
    # Get metrics
    print("\nGetting metrics...")
    metrics = await get_metrics()
    print(f"Metrics: {json_serialize(metrics)}")

async def test_caching():
    """Test result caching"""
    print("\n=== Testing Result Caching ===")
    
    # Clear cache
    print("\nClearing cache...")
    result = await clear_cache()
    print(f"Result: {result}")
    
    # Test first call (cache miss)
    print("\nTesting first call (cache miss)...")
    start = time.time()
    result1 = await execute_tool("dc_computer", {"action": "screenshot"})
    duration1 = time.time() - start
    print(f"Result: {result1}")
    print(f"Duration: {duration1:.6f} seconds")
    
    # Test second call (cache hit)
    print("\nTesting second call (cache hit)...")
    start = time.time()
    result2 = await execute_tool("dc_computer", {"action": "screenshot"})
    duration2 = time.time() - start
    print(f"Result: {result2}")
    print(f"Duration: {duration2:.6f} seconds")
    
    # Compare durations
    print(f"\nCache performance: {duration1 / duration2:.2f}x faster with cache")
    
    # Disable caching
    print("\nDisabling caching...")
    await set_feature_toggle("use_caching", False)
    
    # Test with caching disabled
    print("\nTesting with caching disabled...")
    start = time.time()
    result3 = await execute_tool("dc_computer", {"action": "screenshot"})
    duration3 = time.time() - start
    print(f"Result: {result3}")
    print(f"Duration: {duration3:.6f} seconds")
    
    # Re-enable caching
    print("\nRe-enabling caching...")
    await set_feature_toggle("use_caching", True)

async def run_tests():
    """Run all tests"""
    print("Starting Enhanced Bridge Tests")
    print("=============================")
    
    try:
        await test_basic_tool_execution()
        await test_feature_toggles()
        await test_metrics_collection()
        await test_caching()
        
        print("\n=== All Tests Completed Successfully ===")
    except Exception as e:
        print(f"\nTest error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())