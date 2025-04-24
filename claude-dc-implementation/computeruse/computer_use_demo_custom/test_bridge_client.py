#!/usr/bin/env python3
"""
Test script for the bridge client.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Test the bridge client."""
    print("\n=== Testing Bridge Client ===\n")
    
    # Import the bridge client
    try:
        from dc_bridge.bridge_client import (
            execute_computer_action,
            execute_bash_command,
            get_bridge_metrics,
            get_bridge_toggles,
            set_bridge_toggle
        )
        
        # Test computer action
        print("\nTesting computer action (screenshot)...")
        result = await execute_computer_action("screenshot")
        print(f"Result: {result}")
        
        # Test bash command
        print("\nTesting bash command...")
        result = await execute_bash_command("echo Hello from Bridge Client")
        print(f"Result: {result}")
        
        # Test with parameters
        print("\nTesting computer action with parameters...")
        result = await execute_computer_action("move_mouse", coordinates=[100, 200])
        print(f"Result: {result}")
        
        # Get feature toggles
        print("\nGetting feature toggles...")
        toggles = await get_bridge_toggles()
        print(f"Feature toggles: {json.dumps(toggles, indent=2)}")
        
        # Test toggle changes
        print("\nTesting toggle changes...")
        original_value = toggles.get("use_caching", True)
        result = await set_bridge_toggle("use_caching", not original_value)
        print(f"Toggle result: {result}")
        
        toggles = await get_bridge_toggles()
        print(f"Updated toggles: {json.dumps(toggles, indent=2)}")
        
        # Reset toggle
        await set_bridge_toggle("use_caching", original_value)
        
        # Get metrics
        print("\nGetting metrics...")
        metrics = await get_bridge_metrics()
        print("Metrics collected successfully")
        
        # Print summary of metrics
        calls = metrics.get("total_calls", 0)
        errors = metrics.get("total_errors", 0)
        success_rate = metrics.get("success_rate", 0)
        print(f"Total calls: {calls}")
        print(f"Total errors: {errors}")
        print(f"Success rate: {success_rate:.2f}")
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())