"""
Minimal test script for the streaming implementation.
This doesn't use Streamlit and provides a simple command-line interface.
"""

import os
import asyncio
import json

# Make sure we can find the modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    # Import our streaming implementation
    from streaming.unified_streaming_loop import unified_streaming_agent_loop
    
    # Define simple callbacks
    def on_text(text):
        print(text, end="", flush=True)
    
    def on_thinking(thinking):
        print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
    
    # Load API key from environment or secrets file
    api_key = None
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            api_key = secrets["api_keys"]["anthropic"]
    
    # Define callbacks
    callbacks = {
        "on_text": on_text,
        "on_thinking": on_thinking
    }
    
    # Initialize conversation history
    conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]
    
    # Get user input
    user_input = input("\nYou: ")
    
    print("\nClaude: ", end="", flush=True)
    
    # Call the streaming implementation
    response = await unified_streaming_agent_loop(
        user_input=user_input,
        conversation_history=conversation_history,
        model="claude-3-7-sonnet-20250219",
        thinking_budget=4000,
        callbacks=callbacks
    )
    
    print("\n\nConversation updated!")

if __name__ == "__main__":
    asyncio.run(main())