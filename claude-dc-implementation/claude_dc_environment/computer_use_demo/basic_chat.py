#!/usr/bin/env python3
"""
Basic chat script that works with any Anthropic SDK version
"""

import os
import time
from anthropic import Anthropic

def basic_chat():
    """Simple chat function with minimal parameters"""
    print("\n=== Basic Anthropic Chat ===")
    
    # Get API key
    api_key = input("Enter your Anthropic API key: ").strip()
    if not api_key:
        print("Error: API key is required")
        return
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Simple system message
    system_message = "You are Claude, the AI assistant."
    
    # Message history
    messages = []
    
    # Chat loop
    print("\nChat started! Type 'exit' to quit.\n")
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        # Call API with minimal parameters
        print("\nClaude is thinking...")
        try:
            start_time = time.time()
            
            # Use the most basic form of the API call
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=messages,
                system=system_message
            )
            end_time = time.time()
            
            # Display token usage
            print(f"Call completed in {(end_time - start_time):.2f}s")
            
            # Add assistant response to history
            assistant_message = {"role": "assistant", "content": response.content[0].text}
            messages.append(assistant_message)
            
            # Print response
            print(f"\nClaude: {response.content[0].text}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    print("\nChat ended.")

if __name__ == "__main__":
    basic_chat()
