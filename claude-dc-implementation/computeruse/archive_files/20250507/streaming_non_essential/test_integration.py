#!/usr/bin/env python3
"""
Test script for verifying the streaming integration with the existing system.

This script tests the interaction between the streaming implementation
and the original Claude DC implementation.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.dirname(__file__), "logs", "integration_test.log"),
    filemode="a"
)
logger = logging.getLogger("test_integration")

# Add the production directory to the path so we can import the original modules
sys.path.insert(0, str(Path(__file__).parents[1]))

# Add the streaming directory to the path
streaming_dir = Path(__file__).parent
sys.path.insert(0, str(streaming_dir))

def load_feature_toggles():
    """Load the feature toggle settings."""
    toggle_path = streaming_dir / "feature_toggles.json"
    try:
        with open(toggle_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading feature toggles: {str(e)}")
        return {}

def save_feature_toggles(toggles):
    """Save feature toggle settings."""
    toggle_path = streaming_dir / "feature_toggles.json"
    try:
        with open(toggle_path, "w") as f:
            json.dump(toggles, f, indent=2)
        logger.info(f"Saved feature toggles to {toggle_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving feature toggles: {str(e)}")
        return False

async def test_with_toggles(enabled_features):
    """Test with specific feature toggles enabled."""
    # Load current toggles
    original_toggles = load_feature_toggles()
    
    # Prepare new toggles with only specified features enabled
    new_toggles = original_toggles.copy()
    for feature in new_toggles:
        if feature.startswith("use_"):
            new_toggles[feature] = feature in enabled_features
    
    # Save new toggles
    if not save_feature_toggles(new_toggles):
        print(f"❌ Failed to save feature toggles. Aborting test.")
        return False
    
    print(f"\n--- Testing with enabled features: {', '.join(enabled_features)} ---")
    
    try:
        # Import the unified streaming loop
        from unified_streaming_loop import unified_streaming_agent_loop
        
        # Set up test parameters
        system_prompt = "You are Claude, an AI assistant. Be helpful and concise."
        messages = [{"role": "user", "content": "Tell me a short joke about programming."}]
        
        # Call the unified streaming loop
        print("\nClaude: ", end="", flush=True)
        result = await unified_streaming_agent_loop(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=300,
            model="claude-3-5-sonnet-20240620",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            stream_callback=lambda text: print(text, end="", flush=True)
        )
        
        # Add a newline after the streamed response
        print("\n")
        
        # Test was successful
        return True
    
    except Exception as e:
        logger.exception(f"Error during test with features {enabled_features}")
        print(f"\n❌ Test failed: {str(e)}")
        return False
    
    finally:
        # Restore original toggles
        save_feature_toggles(original_toggles)

async def test_with_bash_tool():
    """Test the integration with the bash tool."""
    try:
        # Import the unified streaming loop
        from unified_streaming_loop import unified_streaming_agent_loop
        
        # Set up test parameters with a bash tool command
        system_prompt = "You are Claude, an AI assistant. Be helpful and concise."
        messages = [{"role": "user", "content": "Please run 'ls -la' in the current directory and explain the output."}]
        
        # Enable the necessary features
        original_toggles = load_feature_toggles()
        test_toggles = original_toggles.copy()
        test_toggles["use_streaming_bash"] = True
        test_toggles["use_unified_streaming"] = True
        save_feature_toggles(test_toggles)
        
        # Call the unified streaming loop
        print("\nClaude (with bash tool): ", end="", flush=True)
        result = await unified_streaming_agent_loop(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=500,
            model="claude-3-5-sonnet-20240620",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            stream_callback=lambda text: print(text, end="", flush=True)
        )
        
        # Add a newline after the streamed response
        print("\n")
        
        # Test was successful
        return True
    
    except Exception as e:
        logger.exception("Error during bash tool test")
        print(f"\n❌ Bash tool test failed: {str(e)}")
        return False
    
    finally:
        # Restore original toggles
        save_feature_toggles(original_toggles)

async def test_with_thinking_tokens():
    """Test the integration with thinking tokens."""
    try:
        # Import the unified streaming loop
        from unified_streaming_loop import unified_streaming_agent_loop
        
        # Set up test parameters with a complex thinking question
        system_prompt = "You are Claude, an AI assistant. Be helpful and concise."
        messages = [{"role": "user", "content": "Solve this step-by-step: If 2x + 3y = 10 and 4x - y = 5, what are the values of x and y?"}]
        
        # Enable the necessary features
        original_toggles = load_feature_toggles()
        test_toggles = original_toggles.copy()
        test_toggles["use_streaming_thinking"] = True
        test_toggles["use_unified_streaming"] = True
        test_toggles["max_thinking_tokens"] = 2000
        save_feature_toggles(test_toggles)
        
        # Call the unified streaming loop
        print("\nClaude (with thinking tokens): ", end="", flush=True)
        result = await unified_streaming_agent_loop(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=500,
            thinking_budget=2000,
            model="claude-3-5-sonnet-20240620",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            stream_callback=lambda text: print(text, end="", flush=True)
        )
        
        # Add a newline after the streamed response
        print("\n")
        
        # Test was successful
        return True
    
    except Exception as e:
        logger.exception("Error during thinking tokens test")
        print(f"\n❌ Thinking tokens test failed: {str(e)}")
        return False
    
    finally:
        # Restore original toggles
        save_feature_toggles(original_toggles)

async def run_tests():
    """Run all integration tests."""
    # Make sure API key is set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set.")
        return 1
    
    # Run tests with different feature combinations
    tests = [
        ("Basic streaming", lambda: test_with_toggles(["use_unified_streaming"])),
        ("Bash tool integration", test_with_bash_tool),
        ("Thinking tokens integration", test_with_thinking_tokens),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n== Testing {test_name} ==")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.exception(f"Unexpected error in {test_name} test")
            print(f"❌ Unexpected error: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n=== Integration Test Summary ===")
    all_passed = True
    for test_name, success in results:
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{status}: {test_name}")
        all_passed = all_passed and success
    
    if all_passed:
        print("\n✅ All integration tests passed!")
        return 0
    else:
        print("\n❌ Some integration tests failed. See log for details.")
        return 1

if __name__ == "__main__":
    asyncio.run(run_tests())