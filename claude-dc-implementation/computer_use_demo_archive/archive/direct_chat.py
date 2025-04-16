#!/usr/bin/env python3
"""
Direct chat script that bypasses streamlit entirely
"""

import os
import time
import sys
import anthropic
from simple_token_manager import token_manager

def direct_chat():
    """Direct chat with Claude that always uses streaming"""
    print("\n=== Direct Claude Chat (Streaming Enabled) ===")
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY", "NOT_PROVIDED")
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # System message
    system_message = """You are Claude, the AI assistant. You are designated as The Conductor in the PALIOS-TAEY Framework."""
    
    # Initial instruction
    initial_instruction = """Please read the EMERGENCY_README.md in your /home/computeruse/ directory and proceed with PRIORITY 3."""
    
    # Message history
    messages = [{"role": "user", "content": initial_instruction}]
    
    # Call API with streaming enabled
    print("\nSending request to Claude with streaming enabled...")
    try:
        start_time = time.time()
        
        # Create a streaming response with correct parameter naming
        with client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            messages=messages,
            system=system_message,
            temperature=0,
            extra_headers={"anthropic-beta": "output-128k-2025-02-19"},
            extra_body={"thinking": {"type": "enabled", "budget_tokens": 32000}}
        ) as stream:
            print("\nClaude is responding:")
            print("-" * 80)
            
            # Collect the full response
            full_text = ""
            for text in stream.text_stream:
                full_text += text
                print(text, end="", flush=True)
            
        end_time = time.time()
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": full_text})
        
        # Print completion message
        print("\n" + "-" * 80)
        print(f"\n[Completed in {(end_time - start_time):.2f}s]")
        
        # Apply token management (estimate tokens since headers aren't available in streaming)
        token_manager.manage_request({"x-input-tokens": "1000", "x-output-tokens": "2000"})
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Wait for user to press enter before exiting
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    direct_chat()
