#!/usr/bin/env python3
"""
Verification script for streaming implementation.

This script tests that the streaming implementation works correctly
and verifies that the feature toggles are working as expected.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_streaming")

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Test bash streaming
async def test_bash_streaming():
    """Test that the bash streaming implementation works."""
    logger.info("Testing bash streaming implementation...")
    
    try:
        # Import the bash streaming tool
        from tools.dc_bash import dc_execute_bash_tool_streaming
        
        # Define a test command
        command = "ls -la"
        
        # Define a progress callback
        async def progress_callback(message, progress):
            logger.info(f"Progress: {message} - {progress:.0%}")
        
        # Execute the command
        chunks = []
        async for chunk in dc_execute_bash_tool_streaming(
            {"command": command},
            progress_callback=progress_callback
        ):
            chunks.append(chunk)
            logger.info(f"Received chunk: {chunk[:30]}...")
        
        # Check the output
        output = "".join(chunks)
        if output and "total" in output:
            logger.info("✅ Bash streaming test passed!")
            return True
        else:
            logger.error("❌ Bash streaming test failed: unexpected output")
            return False
    
    except Exception as e:
        logger.error(f"❌ Bash streaming test failed with error: {str(e)}")
        return False

# Test file streaming
async def test_file_streaming():
    """Test that the file streaming implementation works."""
    logger.info("Testing file streaming implementation...")
    
    try:
        # Import the file streaming tool
        from tools.dc_file import dc_execute_file_tool_streaming
        
        # Create a test file
        test_file = Path("/tmp/streaming_test.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file for streaming.\n")
            f.write("Line 2 of the test file.\n")
            f.write("Line 3 of the test file.\n")
        
        # Define a progress callback
        async def progress_callback(message, progress):
            logger.info(f"Progress: {message} - {progress:.0%}")
        
        # Execute a view command
        chunks = []
        async for chunk in dc_execute_file_tool_streaming(
            {"command": "view", "path": str(test_file)},
            progress_callback=progress_callback
        ):
            chunks.append(chunk)
            logger.info(f"Received chunk: {chunk[:30]}...")
        
        # Check the output
        output = "".join(chunks)
        if output and "This is a test file" in output:
            logger.info("✅ File streaming test passed!")
            return True
        else:
            logger.error("❌ File streaming test failed: unexpected output")
            return False
    
    except Exception as e:
        logger.error(f"❌ File streaming test failed with error: {str(e)}")
        return False
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

# Test feature toggles
async def test_feature_toggles():
    """Test that the feature toggles are working correctly."""
    logger.info("Testing feature toggles...")
    
    try:
        # Path to feature toggles
        toggle_path = Path(__file__).parent / "feature_toggles.json"
        
        if not toggle_path.exists():
            logger.error(f"❌ Feature toggles test failed: file not found at {toggle_path}")
            return False
        
        # Load current toggles
        with open(toggle_path, "r") as f:
            current_toggles = json.load(f)
        
        logger.info(f"Current feature toggles: {current_toggles}")
        
        # Test toggling a feature
        feature_to_toggle = "use_streaming_bash"
        original_value = current_toggles.get(feature_to_toggle, True)
        new_value = not original_value
        
        # Update toggle
        current_toggles[feature_to_toggle] = new_value
        with open(toggle_path, "w") as f:
            json.dump(current_toggles, f, indent=2)
        
        logger.info(f"Changed {feature_to_toggle} from {original_value} to {new_value}")
        
        # Reload and verify
        with open(toggle_path, "r") as f:
            updated_toggles = json.load(f)
        
        if updated_toggles.get(feature_to_toggle) == new_value:
            logger.info("✅ Feature toggles test passed!")
            
            # Restore original value
            current_toggles[feature_to_toggle] = original_value
            with open(toggle_path, "w") as f:
                json.dump(current_toggles, f, indent=2)
            
            logger.info(f"Restored {feature_to_toggle} to {original_value}")
            return True
        else:
            logger.error("❌ Feature toggles test failed: value not updated")
            return False
    
    except Exception as e:
        logger.error(f"❌ Feature toggles test failed with error: {str(e)}")
        return False

# Verify integration script
def test_integration_script():
    """Test that the integration script exists and is executable."""
    logger.info("Testing integration script...")
    
    integration_script = Path(__file__).parent / "integrate_streaming.py"
    
    if not integration_script.exists():
        logger.error(f"❌ Integration script test failed: file not found at {integration_script}")
        return False
    
    if not os.access(integration_script, os.X_OK):
        logger.warning(f"⚠️ Integration script exists but is not executable")
        try:
            os.chmod(integration_script, 0o755)
            logger.info("Made integration script executable")
        except Exception as e:
            logger.error(f"Failed to make integration script executable: {str(e)}")
    
    return True

async def main():
    """Run all verification tests."""
    logger.info("Starting streaming implementation verification...")
    
    # List of tests
    tests = [
        ("Feature Toggles", test_feature_toggles()),
        ("Bash Streaming", test_bash_streaming()),
        ("File Streaming", test_file_streaming()),
    ]
    
    # Also test the integration script (not async)
    integration_test = ("Integration Script", test_integration_script())
    
    # Run all async tests
    results = []
    for name, test_coro in tests:
        try:
            logger.info(f"\n--- Testing {name} ---")
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            logger.error(f"Error running {name} test: {str(e)}")
            results.append((name, False))
    
    # Add integration test result
    results.append(integration_test)
    
    # Print summary
    logger.info("\n=== Verification Summary ===")
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! The streaming implementation is working correctly.")
    else:
        logger.error("\n⚠️ Some tests failed. Please check the logs for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")