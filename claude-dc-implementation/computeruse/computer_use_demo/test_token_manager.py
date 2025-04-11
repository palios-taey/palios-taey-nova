"""
Test script for token management with Anthropic API
Using secrets from the secrets file
"""

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

def test_token_management():
    """Test the token management system with standard API calls"""
    print("\n=== Token Management Test ===")
    
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
    
    # Get recommended settings
    settings = token_manager.get_recommended_settings()
    print(f"Using recommended settings: {settings}")
    
    # Initial system message
    system_message = """You are Claude, the AI assistant with token management capabilities."""
    
    # Make several test calls to demonstrate token management
    messages = []
    
    # Test different beta flags if requested
    test_beta = input("Would you like to test beta features? (y/n): ").strip().lower() == 'y'
    
    for i in range(5):
        print(f"\n--- Test Call {i+1} ---")
        
        # Add a new message
        user_message = f"This is test message {i+1}. Please respond briefly to conserve tokens."
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Make API call
            start_time = time.time()
            
            # Conditional use of beta features
            if test_beta:
                try:
                    # Try with betas parameter first
                    print("Attempting call with 'betas' parameter...")
                    response = client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=settings["max_tokens"],
                        messages=messages,
                        system=system_message,
                        betas=["output-128k-2025-02-19"]
                    )
                except Exception as e:
                    print(f"Error with 'betas' parameter: {e}")
                    print("Trying with extra_headers instead...")
                    # Fall back to extra_headers approach
                    response = client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=settings["max_tokens"],
                        messages=messages,
                        system=system_message,
                        extra_headers={
                            "anthropic-beta": "output-128k-2025-02-19"
                        }
                    )
            else:
                # Standard call without beta features
                response = client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=settings["max_tokens"],
                    messages=messages,
                    system=system_message
                )
                
            end_time = time.time()
            
            # Display token usage
            print(f"Call completed in {(end_time - start_time):.2f}s")
            print(f"Input tokens: {response.usage.input_tokens}")
            print(f"Output tokens: {response.usage.output_tokens}")
            
            # Extract and print response
            response_text = response.content[0].text
            print(f"Response: {response_text[:100]}..." if len(response_text) > 100 else f"Response: {response_text}")
            
            # Add to message history
            messages.append({"role": "assistant", "content": response_text})
            
            # Apply token management
            print("Applying token management...")
            token_manager.manage_request(response.model_dump())
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Show final stats
    print("\n=== Final Token Statistics ===")
    stats = token_manager.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_token_management()
