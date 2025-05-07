#!/usr/bin/env python3
"""
Test script for the streaming implementation.

This script provides a simple way to test the streaming implementation
with different feature toggle settings.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
import argparse

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the streaming integration
from streaming_integration import (
    async_sampling_loop,
    get_feature_toggles,
    reload_feature_toggles,
    is_feature_enabled
)

async def test_streaming(api_key=None, model="claude-3-opus-20240229", use_streaming=True):
    """Run a simple test of the streaming implementation."""
    
    # Update feature toggles for the test
    toggles_path = Path(__file__).parent / "streaming" / "feature_toggles.json"
    if toggles_path.exists():
        with open(toggles_path, "r") as f:
            toggles = json.load(f)
        
        # Set streaming based on command-line option
        toggles["use_unified_streaming"] = use_streaming
        
        with open(toggles_path, "w") as f:
            json.dump(toggles, f, indent=2)
        
        # Reload toggles to pick up changes
        reload_feature_toggles()
    
    print("\n===== Claude DC Streaming Test =====")
    print(f"Unified Streaming: {'Enabled' if is_feature_enabled('use_unified_streaming') else 'Disabled'}")
    print(f"Streaming Bash: {'Enabled' if is_feature_enabled('use_streaming_bash') else 'Disabled'}")
    print(f"Streaming File: {'Enabled' if is_feature_enabled('use_streaming_file') else 'Disabled'}")
    print(f"Streaming Thinking: {'Enabled' if is_feature_enabled('use_streaming_thinking') else 'Disabled'}")
    print("\nEnter your queries below, or 'exit' to quit")
    
    # Set up API key
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nWarning: No API key provided. Please set ANTHROPIC_API_KEY environment variable.")
        return
    
    # Import the necessary modules
    from anthropic.types.beta import BetaTextBlockParam, BetaMessageParam
    # Fix relative imports
    sys.path.insert(0, parent_dir)
    # Now import with absolute paths
    from computer_use_demo.tools import TOOL_GROUPS_BY_VERSION, ToolVersion, ToolCollection
    
    # Define APIProvider class for compatibility
    from enum import Enum
    class APIProvider(str, Enum):
        ANTHROPIC = "anthropic"
        BEDROCK = "bedrock"
        VERTEX = "vertex"
    
    # Set up the basic parameters
    messages = []
    system_prompt = "You are Claude, an AI assistant. You have access to tools for executing bash commands and file operations."
    system = BetaTextBlockParam(
        type="text",
        text=system_prompt
    )
    
    # Define callbacks
    def output_callback(content_block):
        """Handle content blocks from Claude."""
        if content_block["type"] == "text":
            print(f"\nClaude: {content_block['text']}")
        elif content_block["type"] == "tool_use":
            print(f"\nClaude is using tool: {content_block['name']}")
    
    def tool_output_callback(result, tool_id):
        """Handle tool execution results."""
        if hasattr(result, 'output') and result.output:
            print(f"\nTool result: {result.output[:100]}{'...' if len(result.output) > 100 else ''}")
        elif hasattr(result, 'error') and result.error:
            print(f"\nTool error: {result.error}")
    
    def api_response_callback(request, response, error):
        """Handle API responses."""
        if error:
            print(f"\nAPI error: {str(error)}")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # Add user message
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        })
        
        # Run the sampling loop
        try:
            # For testing purposes, let's use the original loop for now
            from computer_use_demo.loop import sampling_loop
            
            messages = await sampling_loop(
                model=model,
                provider=APIProvider.ANTHROPIC,
                system_prompt_suffix="",
                messages=messages,
                output_callback=output_callback,
                tool_output_callback=tool_output_callback,
                api_response_callback=api_response_callback,
                api_key=api_key,
                max_tokens=4096,
                tool_version=ToolVersion.VERSION_1,
                thinking_budget=get_feature_toggles().get("max_thinking_tokens", 4000)
            )
        except Exception as e:
            print(f"\nError in sampling loop: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the streaming implementation")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--model", default="claude-3-opus-20240229", help="Model to use")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming for comparison")
    
    args = parser.parse_args()
    
    asyncio.run(test_streaming(
        api_key=args.api_key,
        model=args.model,
        use_streaming=not args.no_streaming
    ))