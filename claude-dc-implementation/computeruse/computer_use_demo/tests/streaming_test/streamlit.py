"""
Streamlit UI for Claude Computer Use

This module provides the web-based user interface for interacting with
the Claude Computer Use system. It handles rendering of outputs and
capturing of user inputs.
"""
import os
import sys
import time
import json
import logging
from typing import Dict, Any, List, Optional, Union

# Configure system paths
sys.path.append("/home/computeruse/computer_use_demo")

# Import streamlit for UI
import streamlit as st

# Import streaming client
from streaming.streaming_client import StreamingClient
from token_management.token_manager import TokenManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("computer_use.streamlit")

# Initialize token manager and streaming client
token_manager = TokenManager()
streaming_client = StreamingClient(token_manager=token_manager)

# Configure Streamlit page
st.set_page_config(
    page_title="Claude Computer Use",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "streaming_active" not in st.session_state:
        st.session_state.streaming_active = False
    
    if "current_stream" not in st.session_state:
        st.session_state.current_stream = None
    
    if "stream_placeholder" not in st.session_state:
        st.session_state.stream_placeholder = None

    # Token tracking
    if "token_usage" not in st.session_state:
        st.session_state.token_usage = {"input": 0, "output": 0}

def display_header():
    """Display the application header"""
    st.title("ud83dudda5ufe0f Claude Computer Use")
    st.markdown("*Interact with Claude in a virtual computer environment*")

def handle_user_input():
    """Process user input and generate Claude response"""
    user_input = st.chat_input("What would you like Claude to do?")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Create placeholder for streaming response
        st.session_state.stream_placeholder = st.empty()
        
        # Start streaming response
        start_streaming_response(user_input)

def start_streaming_response(user_input: str):
    """Start streaming response from Claude"""
    try:
        # Mark streaming as active
        st.session_state.streaming_active = True
        
        # Format messages for API
        messages = [{"role": msg["role"], "content": msg["content"]} 
                   for msg in st.session_state.messages]
        
        # Get streaming response
        stream = streaming_client.get_completion(
            messages=messages,
            max_tokens=4000
        )
        
        # Store stream reference
        st.session_state.current_stream = stream
        
        # Process streaming response
        process_streaming_response(stream)
    except Exception as e:
        logger.error(f"Error starting streaming response: {str(e)}")
        st.error(f"Error: {str(e)}")
        st.session_state.streaming_active = False

def process_streaming_response(stream):
    """Process streaming response from API"""
    full_response = ""
    placeholder = st.session_state.stream_placeholder
    
    try:
        for chunk in stream:
            # Process chunk with streaming client
            processed_chunk = streaming_client.process_streaming_chunk(chunk)
            
            # Update display with new content
            if processed_chunk:
                full_response += processed_chunk
                placeholder.markdown(full_response)
            
            # Update token usage
            if hasattr(chunk, "usage") and chunk.usage:
                update_token_usage(chunk.usage)
        
        # Add completed response to message history
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    except Exception as e:
        logger.error(f"Error processing streaming response: {str(e)}")
        st.error(f"Error: {str(e)}")
    finally:
        # Mark streaming as complete
        st.session_state.streaming_active = False
        st.session_state.current_stream = None

def update_token_usage(usage):
    """Update token usage statistics"""
    if usage.input_tokens:
        st.session_state.token_usage["input"] += usage.input_tokens
    if usage.output_tokens:
        st.session_state.token_usage["output"] += usage.output_tokens

def display_chat_history():
    """Display the chat history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def display_sidebar():
    """Display sidebar with token usage information"""
    with st.sidebar:
        st.header("System Information")
        
        # Token usage
        st.subheader("Token Usage")
        st.write(f"Input tokens: {st.session_state.token_usage["input"]:,}")
        st.write(f"Output tokens: {st.session_state.token_usage["output"]:,}")
        total = st.session_state.token_usage["input"] + st.session_state.token_usage["output"]
        st.write(f"Total tokens: {total:,}")
        
        # Show streaming status
        st.subheader("Streaming Status")
        status = "Active" if st.session_state.streaming_active else "Inactive"
        st.write(f"Streaming: {status}")
        
        # Add clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# Main application function
def main():
    """Main Streamlit application"""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display sidebar
    display_sidebar()
    
    # Display chat history
    display_chat_history()
    
    # Handle user input
    handle_user_input()

# Run the application
if __name__ == "__main__":
    main()
