#!/usr/bin/env python3
"""
Integration test for the streaming implementation.

This script tests the integration between the streaming implementation
and the existing Claude DC environment using a phased approach.
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "logs" / "integration_test.log")
    ]
)
logger = logging.getLogger("integration_test")

# Feature toggle settings for phased testing
PHASE_SETTINGS = {
    "phase1": {
        "use_streaming_bash": True,
        "use_streaming_file": False,
        "use_streaming_screenshot": False,
        "use_unified_streaming": True,
        "use_streaming_thinking": False,
        "max_thinking_tokens": 4000,
        "log_level": "INFO"
    },
    "phase2": {
        "use_streaming_bash": True,
        "use_streaming_file": True,
        "use_streaming_screenshot": False,
        "use_unified_streaming": True,
        "use_streaming_thinking": False,
        "max_thinking_tokens": 4000,
        "log_level": "INFO"
    },
    "phase3": {
        "use_streaming_bash": True,
        "use_streaming_file": True,
        "use_streaming_screenshot": False,
        "use_unified_streaming": True,
        "use_streaming_thinking": True,
        "max_thinking_tokens": 4000,
        "log_level": "INFO"
    },
    "full": {
        "use_streaming_bash": True,
        "use_streaming_file": True,
        "use_streaming_screenshot": True,
        "use_unified_streaming": True,
        "use_streaming_thinking": True,
        "max_thinking_tokens": 4000,
        "log_level": "INFO"
    }
}

def update_feature_toggles(phase):
    """Update feature toggles with phase settings."""
    toggle_path = Path(__file__).parent / "feature_toggles.json"
    
    if phase in PHASE_SETTINGS:
        settings = PHASE_SETTINGS[phase]
    else:
        logger.warning(f"Unknown phase: {phase}. Using default (phase1).")
        settings = PHASE_SETTINGS["phase1"]
    
    # Write the settings to the feature toggles file
    with open(toggle_path, "w") as f:
        json.dump(settings, f, indent=2)
    
    logger.info(f"Updated feature toggles for phase: {phase}")
    logger.info(f"Settings: {json.dumps(settings, indent=2)}")
    
    return settings

async def run_integration_test(phase, api_key=None, model="claude-3-sonnet-20240229"):
    """Run the integration test with the specified phase settings."""
    
    # Update feature toggles for the phase
    settings = update_feature_toggles(phase)
    
    print(f"\n===== Integration Test - Phase: {phase} =====")
    print("Feature toggles:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    print("\nThis test will verify the integration of streaming capabilities.")
    print("Enter your message below, or 'exit' to quit.")
    
    # Test the streaming implementation directly
    try:
        from streaming.unified_streaming_loop import unified_streaming_agent_loop
        
        # Set up API key
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: API key is required. Please provide it or set ANTHROPIC_API_KEY.")
            return
        
        # Define simple message input for testing
        system = "You are Claude, an AI assistant. You should be helpful, harmless, and honest."
        messages = []
        
        # Define callbacks for output
        def output_callback(content_block):
            if content_block.get("type") == "text":
                print(f"\nClaude: {content_block.get('text')}")
            elif content_block.get("type") == "tool_use":
                print(f"\nClaude is using tool: {content_block.get('name')}")
        
        def tool_output_callback(result, tool_id):
            if hasattr(result, "output") and result.output:
                print(f"\nTool result: {result.output[:100]}{'...' if len(result.output) > 100 else ''}")
            elif hasattr(result, "error") and result.error:
                print(f"\nTool error: {result.error}")
        
        def api_response_callback(request, response, error):
            if error:
                print(f"\nAPI error: {str(error)}")
        
        # Pre-defined test messages
        test_messages = [
            "What is the current date?",
            "List the files in the current directory.",
            "Tell me about the streaming implementation."
        ]
        
        for i, user_input in enumerate(test_messages):
            print(f"\nTest {i+1}: {user_input}")
            
            # Reset messages for each test to keep them independent
            test_messages_copy = [{"role": "user", "content": user_input}]
            
            try:
                # Use the unified streaming agent loop directly
                result = await unified_streaming_agent_loop(
                    api_key=api_key,
                    model=model,
                    system=system,
                    messages=test_messages_copy,
                    output_callback=output_callback,
                    tool_output_callback=tool_output_callback,
                    api_response_callback=api_response_callback,
                    max_tokens=4096
                )
                
                print(f"\nTest {i+1} completed successfully!")
                print("\n" + "-" * 80)
                
            except Exception as e:
                print(f"\nError in Test {i+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                print("\n" + "-" * 80)
    
    except ImportError as e:
        print(f"ImportError: {str(e)}")
        print("Unable to import unified_streaming_agent_loop. Please ensure the module is available.")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test streaming integration in phases")
    parser.add_argument("--phase", default="phase1", choices=["phase1", "phase2", "phase3", "full"],
                        help="Integration phase to test")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--model", default="claude-3-sonnet-20240229", help="Model to use")
    
    args = parser.parse_args()
    
    asyncio.run(run_integration_test(
        phase=args.phase,
        api_key=args.api_key,
        model=args.model
    ))