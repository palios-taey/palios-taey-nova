#!/usr/bin/env python3
"""
XML function call streaming demonstration.

This script shows how to use XML-style function calls with Claude DC
to prevent the race condition during streaming.
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("xml_streaming_demo.log")
    ]
)
logger = logging.getLogger("xml_streaming_demo")

# Make sure streaming directory is in path
streaming_dir = str(Path(__file__).parent / "streaming")
if streaming_dir not in sys.path:
    sys.path.insert(0, streaming_dir)
logger.info(f"Added streaming directory to path: {streaming_dir}")

# Import necessary modules
try:
    from unified_streaming_loop import unified_streaming_agent_loop
    logger.info("Successfully imported unified_streaming_agent_loop")
except ImportError as e:
    logger.error(f"Error importing unified_streaming_agent_loop: {str(e)}")
    sys.exit(1)

# Get API key
def get_api_key():
    """Get the API key from secrets file or environment."""
    api_key = None
    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
    
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets.get("api_keys", {}).get("anthropic")
        except Exception as e:
            logger.error(f"Error loading API key from file: {str(e)}")
    
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
    if api_key:
        logger.info("API key loaded successfully")
    else:
        logger.warning("No API key found")
        
    return api_key

# Run the streaming agent loop with XML function calls
async def demo_xml_streaming():
    """Run the streaming agent loop with XML function calls."""
    print("\nXML Function Call Streaming Demo\n")
    print("Enter your query below, or 'exit' to quit\n")
    print("TIP: Ask Claude DC to use XML format for function calls\n")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        logger.error("No API key available. Cannot run demo.")
        print("Error: No API key available.")
        return
    
    # Initialize conversation history
    conversation_history = []
    
    # Configure callbacks
    def on_text(text):
        print(text, end="", flush=True)
    
    def on_tool_use(tool_name, tool_input):
        print(f"\n[Using tool: {tool_name}]", flush=True)
        print(f"[Tool input: {json.dumps(tool_input, indent=2)}]", flush=True)
    
    def on_tool_result(tool_name, tool_input, tool_result):
        if hasattr(tool_result, "output"):
            result = tool_result.output[:100] + "..." if len(tool_result.output) > 100 else tool_result.output
        elif hasattr(tool_result, "error"):
            result = f"ERROR: {tool_result.error}"
        else:
            result = "No result"
        print(f"\n[Tool result: {result}]", flush=True)
    
    def on_thinking(thinking):
        print(f"\n[Thinking: {thinking[:50]}...]", flush=True)
    
    def on_error(error, recoverable=False):
        print(f"\n[Error: {error}]", flush=True)
    
    # Set up callbacks
    callbacks = {
        "on_text": on_text,
        "on_thinking": on_thinking,
        "on_tool_use": on_tool_use,
        "on_tool_result": on_tool_result,
        "on_error": on_error
    }
    
    # Run interactive loop
    while True:
        user_input = input("> ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        try:
            # Add prompt to suggest using XML format
            if "xml" not in user_input.lower() and "function" not in user_input.lower():
                user_input = user_input + " (Please use XML format for function calls)"
            
            # Run the unified streaming agent loop
            conversation_history = await unified_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                api_key=api_key,
                model="claude-3-5-sonnet-20240229",
                max_tokens=4000,
                thinking_budget=None,  # Disable thinking for tool tests
                use_real_adapters=True,
                callbacks=callbacks
            )
            
            print("\n")
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(demo_xml_streaming())