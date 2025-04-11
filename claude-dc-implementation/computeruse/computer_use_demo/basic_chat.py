#!/usr/bin/env python3
"""
Basic chat script that works with any Anthropic SDK version
Using secrets from the secrets file
"""

import os
import json
import time
from anthropic import Anthropic

def load_secrets():
    """Load API keys from the secrets file"""
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    try:
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
        return secrets
    except Exception as e:
        print(f"Error loading secrets file: {e}")
        return None

def basic_chat():
    """Simple chat function with minimal parameters using secrets"""
    print("\n=== Basic Anthropic Chat ===")
    
    # Load secrets
    secrets = load_secrets()
    if not secrets or "api_keys" not in secrets or "anthropic" not in secrets["api_keys"]:
        print("Error: Couldn't load Anthropic API key from secrets file")
        api_key = input("Enter your Anthropic API key manually: ").strip()
        if not api_key:
            print("Error: API key is required")
            return
    else:
        api_key = secrets["api_keys"]["anthropic"]
        print("Successfully loaded API key from secrets file")
    
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
