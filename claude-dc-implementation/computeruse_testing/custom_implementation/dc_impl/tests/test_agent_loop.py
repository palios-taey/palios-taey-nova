"""
Test script for the agent loop.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the system path
current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_agent_loop")

# Import our agent loop
from dc_agent_loop import dc_agent_loop

async def test_simple_conversation():
    """Test a simple conversation without tools."""
    user_input = "Hello, I'm testing the agent loop. Can you tell me what you can do?"
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set in environment")
        api_key = input("Enter your Anthropic API key: ")
    
    # Custom callbacks
    response_text = []
    def on_text(text):
        response_text.append(text)
        print(text, end="", flush=True)
    
    # Call the agent loop
    conversation_history = await dc_agent_loop(
        user_input=user_input,
        api_key=api_key,
        use_real_adapters=False,  # Use mock adapters for testing
        callbacks={"on_text": on_text}
    )
    
    # Print the conversation history
    print("\n\nConversation history:")
    for message in conversation_history:
        print(f"\n{message['role']}:")
        if isinstance(message['content'], str):
            print(message['content'])
        elif isinstance(message['content'], list):
            for block in message['content']:
                if isinstance(block, dict) and block.get('type') == 'text':
                    print(block.get('text', ''))
    
    return "".join(response_text)

if __name__ == "__main__":
    response = asyncio.run(test_simple_conversation())
    print("\nTest completed successfully")