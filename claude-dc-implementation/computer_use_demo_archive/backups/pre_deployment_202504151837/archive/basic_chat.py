"""
Basic chat script that works with any Anthropic SDK version.
Includes basic functionality with support for token management.
"""

import os
import json
import time
import sys
from anthropic import Anthropic
from simple_token_manager import token_manager

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
    """Simple chat function with token management"""
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
    
    # Get recommended settings from token manager
    settings = token_manager.get_recommended_settings()
    
    # Simple system message
    system_message = """You are Claude, the AI assistant. You have access to a computer environment and can use tools to interact with it. You are designated as The Conductor in the PALIOS-TAEY Framework."""
    
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
        
        # Call API with token management
        print("\nClaude is thinking...")
        try:
            start_time = time.time()
            
            # Use settings from token manager
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=settings["max_tokens"],
                messages=messages,
                system=system_message
            )
            end_time = time.time()
            
            # Display token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            print(f"Call completed in {(end_time - start_time):.2f}s")
            print(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}")
            
            # Add assistant response to history
            assistant_message = {"role": "assistant", "content": response.content[0].text}
            messages.append(assistant_message)
            
            # Print response
            print(f"\nClaude: {response.content[0].text}")
            
            # Apply token management
            token_manager.manage_request(response.model_dump())
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            # Display the full traceback for debugging
            import traceback
            traceback.print_exc()
    
    # Show token usage statistics
    print("\n=== Token Usage Statistics ===")
    stats = token_manager.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\nChat ended.")

if __name__ == "__main__":
    basic_chat()
