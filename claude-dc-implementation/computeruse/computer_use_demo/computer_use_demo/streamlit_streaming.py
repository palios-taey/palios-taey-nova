"""
Streamlit UI with streaming capabilities for Claude DC.

This entry point provides a Streamlit UI that uses the streaming implementation
without modifying the existing code.
"""

import os
import sys
import re
import json
import time
import logging
import asyncio
import streamlit as st
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("streamlit_streaming.log")
    ]
)
logger = logging.getLogger("streamlit_streaming")

# Import streaming implementation
try:
    from streaming.unified_streaming_loop import unified_streaming_agent_loop
    from streaming.tools.dc_adapters import (
        dc_validate_computer_parameters,
        dc_validate_bash_parameters
    )
    
    # Import feature toggles
    from streaming.feature_toggles import get_feature_toggles, is_feature_enabled
    
    STREAMING_AVAILABLE = True
    logger.info("Streaming implementation loaded successfully")
except Exception as e:
    logger.error(f"Error loading streaming implementation: {str(e)}")
    STREAMING_AVAILABLE = False

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thinking" not in st.session_state:
    st.session_state.thinking = ""

if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = STREAMING_AVAILABLE

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

# Set page config
st.set_page_config(
    page_title="Claude DC with Streaming",
    page_icon="🤖",
    layout="wide",
)

# Sidebar
with st.sidebar:
    st.title("Claude DC")
    st.subheader("with Streaming")
    
    # Streaming status
    if STREAMING_AVAILABLE:
        st.success("✅ Streaming Available")
        streaming_toggle = st.checkbox("Enable Streaming", value=st.session_state.streaming_active)
        if streaming_toggle != st.session_state.streaming_active:
            st.session_state.streaming_active = streaming_toggle
            st.experimental_rerun()
    else:
        st.error("❌ Streaming Not Available")
    
    # Feature toggles (if streaming is available)
    if STREAMING_AVAILABLE:
        st.subheader("Feature Toggles")
        try:
            toggles = get_feature_toggles()
            
            # Display toggles
            for key, value in toggles.items():
                if isinstance(value, bool):
                    st.write(f"{key}: {'Enabled' if value else 'Disabled'}")
        except Exception as e:
            st.error(f"Error loading feature toggles: {str(e)}")
    
    # Info section
    st.subheader("About")
    st.info(
        "This is Claude DC with streaming capabilities. "
        "You can chat with Claude and see responses in real-time."
    )

# Main content
st.title("Claude DC")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Chat with Claude DC...")

# Process the user input
if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response area
    with st.chat_message("assistant"):
        if not STREAMING_AVAILABLE or not st.session_state.streaming_active:
            # Non-streaming response
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Import original implementation for non-streaming mode
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from loop import sampling_loop
                
                # Get response
                response = asyncio.run(sampling_loop(prompt, st.session_state.messages))
                
                # Update placeholder with response
                message_placeholder.markdown(response)
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                logger.error(f"Error in non-streaming mode: {str(e)}")
                message_placeholder.markdown(f"Error: {str(e)}")
        else:
            # Streaming response setup
            st.session_state.current_response = ""
            message_placeholder = st.empty()
            thinking_placeholder = st.empty()
            
            try:
                def update_thinking(thinking):
                    if is_feature_enabled("use_streaming_thinking"):
                        st.session_state.thinking = thinking
                        thinking_placeholder.markdown(f"**Thinking:** {thinking}")
                
                def process_stream(content_delta, is_thinking=False):
                    if is_thinking:
                        update_thinking(content_delta)
                    else:
                        # Use session state to store the response
                        st.session_state.current_response += content_delta
                        message_placeholder.markdown(st.session_state.current_response)
                
                # Use hardcoded API parameters for simplicity
                logger.info(f"Using model: claude-3-7-sonnet-20250219")
                
                # Get API key from correct secrets file
                try:
                    api_key = None
                    secrets_path = "/home/computeruse/secrets/palios-taey-secrets.json"
                    if os.path.exists(secrets_path):
                        with open(secrets_path, "r") as f:
                            secrets = json.load(f)
                            api_key = secrets["api_keys"]["anthropic"]
                            logger.info(f"Loaded API key from {secrets_path}")
                    
                    if not api_key:
                        raise ValueError("API key not found")
                    
                    # Import direct module reference to avoid any confusion
                    import sys
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from streaming.unified_streaming_loop import unified_streaming_agent_loop
                    
                    # Enhanced logging for process_stream function with improved stability
                    def log_process_stream(content_delta, is_thinking=False):
                        try:
                            if is_thinking:
                                logger.info(f"Thinking token received: {content_delta[:20]}...")
                                update_thinking(content_delta)
                            else:
                                content_snippet = content_delta[:20].replace('\n', ' ') if content_delta else ""
                                logger.info(f"Content token received: {content_snippet}...")
                                
                                # Update session state in a safer way
                                if not isinstance(st.session_state.current_response, str):
                                    st.session_state.current_response = ""
                                st.session_state.current_response += content_delta
                                
                                # Try to update UI safely with debouncing
                                try:
                                    # Only update UI every few tokens to improve performance
                                    if len(content_delta) > 5 or content_delta.endswith(".") or content_delta.endswith("\n"):
                                        message_placeholder.markdown(st.session_state.current_response)
                                except Exception as ui_err:
                                    logger.error(f"Error updating UI: {str(ui_err)}")
                                    # If that fails, try a simpler approach
                                    try:
                                        message_placeholder.text(st.session_state.current_response[:100] + "...")
                                    except:
                                        # Last resort - just log it
                                        logger.info("Failed to update UI, continuing to collect response")
                        except Exception as e:
                            logger.error(f"Error in log_process_stream: {str(e)}", exc_info=True)
                    
                    # Use unified streaming loop with parameters that work in test
                    logger.info("Calling unified_streaming_agent_loop")
                    _ = asyncio.run(unified_streaming_agent_loop(
                        user_input=prompt,
                        conversation_history=st.session_state.messages,
                        api_key=api_key,
                        model="claude-3-7-sonnet-20250219",
                        thinking_budget=4000,
                        callbacks={
                            "on_text": log_process_stream,
                            "on_thinking": update_thinking
                        }
                    ))
                    logger.info(f"Streaming completed successfully")
                    
                    # Get the actual streamed response from session state
                    final_response = st.session_state.current_response
                    logger.info(f"Final response from session state (length: {len(final_response) if isinstance(final_response, str) else 0})")
                    
                except Exception as e:
                    logger.error(f"Error in streaming mode: {str(e)}", exc_info=True)
                    message_placeholder.markdown(f"Error: {str(e)}")
                    # Use default response on error
                    final_response = "I encountered an error while processing your request."
                
                # Ensure final response is displayed
                message_placeholder.markdown(final_response)
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                
                # Clear thinking area
                thinking_placeholder.empty()
                st.session_state.thinking = ""
            
            except Exception as e:
                logger.error(f"Error in streaming mode: {str(e)}")
                message_placeholder.markdown(f"Error: {str(e)}")
                
                # Clear thinking area
                thinking_placeholder.empty()
                st.session_state.thinking = ""