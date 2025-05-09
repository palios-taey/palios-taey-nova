#!/usr/bin/env python3
"""
Minimal standalone implementation for Claude DC.
This is a complete, self-contained script that runs a basic Claude interface.
"""

import os
import sys
import asyncio
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minimal_claude_dc")

# Ensure required packages are installed
def ensure_packages():
    """Install required packages if not already installed."""
    try:
        import anthropic
        import streamlit
        logger.info("Required packages are already installed")
    except ImportError:
        logger.info("Installing required packages...")
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "anthropic==0.49.0", "streamlit==1.44.0"
        ])
        logger.info("Packages installed successfully")

# Basic Claude UI using Streamlit
def create_claude_ui():
    """Create a basic UI for Claude using Streamlit."""
    import streamlit as st
    
    # Set page config
    st.set_page_config(
        page_title="Minimal Claude DC",
        page_icon="🤖",
        layout="wide"
    )
    
    # Set up session state for conversation
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display title
    st.title("Minimal Claude DC")
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Handle user input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to conversation
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate response from Claude
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response from Claude
                    response = get_claude_response(user_input, st.session_state.messages)
                    st.write(response)
                    
                    # Add assistant response to conversation
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Function to get response from Claude
def get_claude_response(user_input, conversation_history):
    """Get a response from Claude API."""
    try:
        import anthropic
        
        # Get API key
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "ERROR: ANTHROPIC_API_KEY environment variable not set"
        
        # Initialize client
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        # Prepare messages
        messages = []
        for message in conversation_history:
            if message["role"] == "user":
                messages.append({"role": "user", "content": message["content"]})
            elif message["role"] == "assistant":
                messages.append({"role": "assistant", "content": message["content"]})
        
        # Use asyncio to run the API call
        async def get_response():
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=messages,
                system="You are Claude, an AI assistant.",
                temperature=0.7
            )
            return response.content[0].text
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response_text = loop.run_until_complete(get_response())
        loop.close()
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error getting response from Claude: {e}")
        return f"I encountered an error: {str(e)}"

# Main function
def main():
    """Main function."""
    logger.info("Starting Minimal Claude DC...")
    
    # Ensure required packages are installed
    ensure_packages()
    
    # Import and run Streamlit
    try:
        import streamlit.web.cli as stcli
        import sys
        
        # Get the path to this script
        script_path = Path(__file__).absolute()
        
        # Run Streamlit with this script
        sys.argv = [
            "streamlit", "run", 
            str(script_path),
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        logger.info(f"Running Streamlit with: {' '.join(sys.argv)}")
        stcli.main()
        
    except Exception as e:
        logger.error(f"Error running Streamlit: {e}")
        return 1
    
    return 0

# Entry point for Streamlit (when this script is run directly by Streamlit)
if __name__ == "__main__":
    # Check if being run by Streamlit
    if os.environ.get("STREAMLIT_RUNTIME", ""):
        create_claude_ui()
    else:
        # Being run directly, so start Streamlit
        sys.exit(main())