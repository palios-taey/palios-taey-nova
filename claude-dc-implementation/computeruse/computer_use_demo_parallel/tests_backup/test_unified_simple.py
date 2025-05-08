"""
Simple test script for the unified streaming implementation without Streamlit.
"""

import os
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_unified.log")
    ]
)
logger = logging.getLogger("test_unified")

async def test_unified():
    # Load API key
    api_key = None
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
            api_key = secrets["api_keys"]["anthropic"]
            logger.info(f"Loaded API key: {api_key[:10]}...")
    
    if not api_key:
        logger.error("API key not found")
        return False
    
    try:
        # Import our streaming implementation
        from streaming.unified_streaming_loop import unified_streaming_agent_loop
        
        # Define simple callbacks
        def on_text(text):
            print(text, end="", flush=True)
        
        def on_thinking(thinking):
            print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
        
        # Create callbacks dictionary
        callbacks = {
            "on_text": on_text,
            "on_thinking": on_thinking
        }
        
        # Set up test conversation
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Set user input
        user_input = "What are three key benefits of streaming in AI assistants?"
        
        logger.info(f"Starting test with input: {user_input}")
        print(f"\nTesting with: {user_input}")
        print("\nClaude: ", end="")
        
        # Call the unified streaming agent loop
        response = await unified_streaming_agent_loop(
            user_input=user_input,
            conversation_history=conversation,
            api_key=api_key,
            model="claude-3-7-sonnet-20250219",
            thinking_budget=4000,
            callbacks=callbacks
        )
        
        logger.info("Test completed successfully")
        print("\n\nTest completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error in unified test: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\n\nError: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_unified())