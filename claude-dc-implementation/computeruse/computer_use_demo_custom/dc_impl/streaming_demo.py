#!/usr/bin/env python3
"""
Demo script for the unified streaming implementation.

This script provides an interactive demonstration of the unified streaming MVP:
1. Streaming responses - with incremental text output
2. Tool use during streaming - with real-time tool execution
3. Thinking capabilities - with proper integration
"""

import os
import sys
import asyncio
import argparse
import json
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the unified streaming implementation
from unified_streaming_loop import unified_streaming_agent_loop

async def run_demo(args):
    """Run the interactive demo."""
    print("\n===== Unified Streaming Demo =====")
    print("Features:")
    print("  - Streaming responses")
    print("  - Tool use during streaming")
    print("  - Thinking capabilities")
    print("\nEnter your queries below, or 'exit' to quit")
    
    # Set up API key
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nWarning: No API key provided. Please set ANTHROPIC_API_KEY environment variable or use --api-key.")
        api_key = input("Enter your Anthropic API key: ")
    
    # Initialize conversation
    conversation_history = []
    
    # Track thinking content
    thinking_content = []
    
    # Callback setup
    def on_thinking(text):
        thinking_content.append(text)
        if args.show_thinking:
            print(f"\n[Thinking: {text[:100]}...]", flush=True)
    
    # Configure callbacks
    callbacks = {}
    if args.show_thinking:
        callbacks["on_thinking"] = on_thinking
    
    # Main interaction loop
    while True:
        print("\n" + "-" * 40)
        user_input = input("> ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        # Reset thinking for this turn
        thinking_content.clear()
        
        try:
            # Configure streaming options
            streaming_options = {
                "user_input": user_input,
                "conversation_history": conversation_history,
                "api_key": api_key,
                "model": args.model,
                "max_tokens": args.max_tokens,
                "use_real_adapters": True,
                "callbacks": callbacks
            }
            
            # Enable thinking if requested
            if args.enable_thinking:
                streaming_options["thinking_budget"] = args.thinking_budget
            
            print("\n")  # Add space before response
            
            # Start timing
            import time
            start_time = time.time()
            
            # Call the unified streaming agent loop
            conversation_history = await unified_streaming_agent_loop(
                **streaming_options
            )
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            print("\n")  # Add space after response
            
            # Show statistics
            print(f"Response completed in {elapsed_time:.2f} seconds")
            if args.enable_thinking and thinking_content:
                print(f"Thinking: {len(thinking_content)} chunks, ~{sum(len(t.split()) for t in thinking_content)} words")
            
            # Show thinking details if requested
            if args.show_thinking_summary and thinking_content:
                print("\nThinking Summary:")
                combined_thinking = "\n".join(thinking_content)
                print(f"First 200 chars: {combined_thinking[:200]}...")
                print(f"Last 200 chars: ...{combined_thinking[-200:]}")
        
        except KeyboardInterrupt:
            print("\nOperation interrupted")
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    """Main entry point for the demo."""
    parser = argparse.ArgumentParser(description="Unified Streaming Demo")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env variable)")
    parser.add_argument("--model", default="claude-3-opus-20240229", help="Claude model to use")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Maximum tokens in response")
    parser.add_argument("--enable-thinking", action="store_true", help="Enable thinking capability")
    parser.add_argument("--thinking-budget", type=int, default=4000, help="Token budget for thinking")
    parser.add_argument("--show-thinking", action="store_true", help="Show thinking output in real-time")
    parser.add_argument("--show-thinking-summary", action="store_true", help="Show thinking summary after response")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_demo(args))
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")

if __name__ == "__main__":
    main()