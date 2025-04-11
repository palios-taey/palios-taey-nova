#!/usr/bin/env python3
"""
Direct script to use the Anthropic API with extended capabilities
"""

import os
import time
from anthropic import Anthropic

# Configuration
MODEL = "claude-3-7-sonnet-20250219"
MAX_TOKENS = 64000
THINKING_BUDGET = 32000

# Simple token tracking
class SimpleTokenTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.calls = 0
        
    def update(self, input_tokens, output_tokens):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.calls += 1
        
    def display_stats(self):
        print(f"\n=== Token Usage Stats ===")
        print(f"Total API calls: {self.calls}")
        print(f"Total input tokens: {self.total_input_tokens}")
        print(f"Total output tokens: {self.total_output_tokens}")
        print(f"Total tokens: {self.total_input_tokens + self.total_output_tokens}")
        print("========================\n")

def chat_with_claude():
    """Simple function to chat directly with Claude with extended capabilities"""
    print("\n" + "="*50)
    print("PALIOS-AI-OS Direct Chat")
    print("="*50)
    print(f"• Model: {MODEL}")
    print(f"• Max tokens: {MAX_TOKENS}")
    print(f"• Thinking budget: {THINKING_BUDGET}")
    print(f"• Extended output beta: Enabled")
    print(f"• Token-efficient tools beta: Enabled")
    print("="*50 + "\n")
    
    # Get API key
    api_key = input("Enter your Anthropic API key: ").strip()
    if not api_key:
        print("Error: API key is required")
        return
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    tracker = SimpleTokenTracker()
    
    # Initial system message
    system_message = """You are Claude, the AI assistant. You are cooperative, helpful, and engaging."""
    
    # Message history
    messages = []
    
    # Chat loop
    print("\nChat started! Type 'exit' to quit.\n")
    while True:
        # Get user input
        user_input = input("\n\033[1mYou:\033[0m ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        # Call API with extended capabilities
        print("\n\033[1mClaude is thinking...\033[0m")
        try:
            start_time = time.time()
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=messages,
                thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
                betas=["output-128k-2025-02-19", "token-efficient-tools-2025-02-19"]
            )
            end_time = time.time()
            
            # Update token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            tracker.update(input_tokens, output_tokens)
            
            # Add assistant response to history
            assistant_message = {"role": "assistant", "content": response.content[0].text}
            messages.append(assistant_message)
            
            # Print response with timing info
            print(f"\n\033[1mClaude ({(end_time - start_time):.2f}s):\033[0m {response.content[0].text}")
            print(f"\n[Used {input_tokens} input tokens, {output_tokens} output tokens]")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    # Display final stats
    tracker.display_stats()
    print("Chat ended. Thanks for using PALIOS-AI-OS Direct Chat!")

if __name__ == "__main__":
    chat_with_claude()
