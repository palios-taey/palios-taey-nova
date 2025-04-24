#!/usr/bin/env python3
"""
Test script for enhanced bridge metrics and feature toggles.
"""

import asyncio
import json
import sys
from pathlib import Path

# Configure paths
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    # Import the enhanced bridge
    from enhanced_bridge import (
        execute_tool,
        get_metrics,
        get_feature_toggles,
        set_feature_toggle
    )
    
    # Get current feature toggles
    print("\nCurrent feature toggles:")
    toggles = await get_feature_toggles()
    print(json.dumps(toggles, indent=2))
    
    # Make some tool calls
    print("\nMaking tool calls to generate metrics...")
    await execute_tool("dc_computer", {"action": "screenshot"})
    await execute_tool("dc_bash", {"command": "echo Test command"})
    
    # Try an invalid tool to generate error metrics
    try:
        await execute_tool("invalid_tool", {})
    except:
        print("Caught error from invalid tool (expected)")
    
    # Get metrics
    print("\nMetrics:")
    metrics = await get_metrics()
    
    # Only print selected metrics to avoid JSON serialization issues
    print("\nUptime:", metrics.get("uptime"))
    print("Total calls:", metrics.get("total_calls"))
    print("Total errors:", metrics.get("total_errors"))
    print("Success rate:", metrics.get("success_rate"))
    print("Overall average time:", metrics.get("overall_avg_time"))
    
    print("\nTool stats:")
    for tool_name, stats in metrics.get("tool_stats", {}).items():
        print(f"  {tool_name}:")
        print(f"    Calls: {stats.get('calls')}")
        print(f"    Avg time: {stats.get('avg_time')}")
    
    # Test feature toggle
    print("\nTesting feature toggle...")
    original_state = toggles.get("use_caching")
    
    print(f"Changing use_caching from {original_state} to {not original_state}")
    result = await set_feature_toggle("use_caching", not original_state)
    print("Toggle result:", result.get("message"))
    
    # Verify change
    new_toggles = await get_feature_toggles()
    print(f"New use_caching value: {new_toggles.get('use_caching')}")
    
    # Restore original state
    await set_feature_toggle("use_caching", original_state)
    print(f"Restored use_caching to {original_state}")

if __name__ == "__main__":
    asyncio.run(main())