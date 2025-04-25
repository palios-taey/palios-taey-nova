#!/usr/bin/env python3
"""
Simple CLI application for the streaming agent loop.
Shows how to use the streaming API with a terminal interface.
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Ensure we can import from parent directory
parent_dir = str(Path(__file__).parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the streaming agent loop
from dc_streaming_agent_loop import dc_streaming_agent_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "streaming_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_streaming_cli")

# Create a spinner for showing activity
class Spinner:
    """Simple spinner for showing activity in the terminal."""
    
    def __init__(self):
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_char = 0
        self.is_spinning = False
        self.task = None
    
    async def spin(self):
        """Spin the spinner until stopped."""
        self.is_spinning = True
        while self.is_spinning:
            sys.stdout.write(f"\r{self.spinner_chars[self.current_char]} ")
            sys.stdout.flush()
            self.current_char = (self.current_char + 1) % len(self.spinner_chars)
            await asyncio.sleep(0.1)
    
    def start(self):
        """Start the spinner."""
        self.task = asyncio.create_task(self.spin())
    
    def stop(self):
        """Stop the spinner."""
        if self.task:
            self.is_spinning = False
            self.task.cancel()
            sys.stdout.write("\r \r")
            sys.stdout.flush()

# Main function for running the CLI
async def main():
    """Main entry point for the CLI application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Claude DC Streaming CLI")
    parser.add_argument("--model", type=str, default="claude-3-7-sonnet-20250219", help="Claude model to use")
    parser.add_argument("--max-tokens", type=int, default=16000, help="Maximum response tokens")
    parser.add_argument("--thinking", type=int, default=4000, help="Thinking token budget (0 to disable)")
    parser.add_argument("--real-tools", action="store_true", help="Use real tool adapters")
    parser.add_argument("--key", type=str, help="Anthropic API key (will use environment if not provided)")
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Anthropic API key not provided and ANTHROPIC_API_KEY not set in environment")
        return 1
    
    # Set up thinking budget (None to disable)
    thinking_budget = args.thinking if args.thinking > 0 else None
    
    # Create spinner for activity indication
    spinner = Spinner()
    
    # Define callbacks for UI
    def on_text(text):
        # Stop spinner when we receive text
        spinner.stop()
        # Print text
        sys.stdout.write(text)
        sys.stdout.flush()
    
    def on_tool_use(tool_name, tool_input):
        # Stop spinner
        spinner.stop()
        # Print tool use info
        print(f"\n\n[Using tool: {tool_name}]")
        print(f"[Tool input: {tool_input}]")
        # Start spinner again
        spinner.start()
    
    def on_tool_result(tool_name, tool_input, tool_result):
        # Stop spinner
        spinner.stop()
        # Print tool result
        print("\n[Tool result:]")
        if tool_result.error:
            print(f"Error: {tool_result.error}")
        else:
            if tool_result.output:
                print(tool_result.output)
            if tool_result.base64_image:
                print("[Image data available]")
    
    def on_tool_progress(tool_name, tool_input, message, progress):
        # Update spinner message (not implementing yet)
        pass
    
    def on_thinking(thinking_text):
        # Print thinking text if verbose
        if args.verbose:
            print(f"\n[Thinking: {thinking_text[:100]}...]")
    
    # Set up callbacks dictionary
    callbacks = {
        "on_text": on_text,
        "on_tool_use": on_tool_use,
        "on_tool_result": on_tool_result,
        "on_tool_progress": on_tool_progress,
        "on_thinking": on_thinking
    }
    
    # Initialize conversation history
    conversation_history = []
    
    # Welcome message
    print("\n=== Claude DC Streaming CLI ===")
    print(f"Model: {args.model}")
    print(f"Max tokens: {args.max_tokens}")
    print(f"Thinking budget: {thinking_budget or 'disabled'}")
    print(f"Real tools: {'enabled' if args.real_tools else 'disabled'}")
    print("\nType 'exit' to quit, or 'clear' to clear the conversation history.")
    print("Enter your message:")
    
    while True:
        # Get user input
        user_input = input("\n> ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        # Check for clear command
        if user_input.lower() == "clear":
            conversation_history = []
            print("Conversation history cleared.")
            continue
        
        # Start spinner
        spinner.start()
        
        try:
            # Run streaming agent loop
            conversation_history = await dc_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                api_key=api_key,
                model=args.model,
                max_tokens=args.max_tokens,
                thinking_budget=thinking_budget,
                use_real_adapters=args.real_tools,
                callbacks=callbacks
            )
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            spinner.stop()
            print("\n\nUser interrupted operation.")
        except Exception as e:
            # Handle any other errors
            spinner.stop()
            print(f"\n\nError: {str(e)}")
            logger.error(f"Error during streaming: {str(e)}", exc_info=True)
        finally:
            # Ensure spinner is stopped
            spinner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)