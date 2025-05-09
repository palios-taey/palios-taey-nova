#!/usr/bin/env python3
"""
Simple Streamlit app for testing the continuity solution.
This app demonstrates how to integrate state persistence in a Streamlit app.
"""

import os
import sys
import json
import time
import streamlit as st
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import state management utilities
from restore_conversation_state import load_state, format_transition_prompt

# Constants
SIGNAL_FILE_DIR = Path("/tmp/claude_dc")
SIGNAL_FILE = SIGNAL_FILE_DIR / "extract_state"
STATE_FILE = Path("/tmp/conversation_state.json")

# Setup page config
st.set_page_config(
    page_title="Claude DC Continuity Test",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transition_prompt" not in st.session_state:
    st.session_state.transition_prompt = None
if "continue_from" not in st.session_state:
    # Check for continuation flag
    continue_from = os.environ.get('CONTINUE_FROM')
    st.session_state.continue_from = continue_from if continue_from else None

# Check for continuation
if st.session_state.continue_from and os.path.exists(st.session_state.continue_from):
    # Load saved state
    state = load_state(st.session_state.continue_from)
    if state:
        # Restore transition prompt to session
        transition_prompt = state.get('transition_prompt', {})
        st.session_state.transition_prompt = transition_prompt
        
        # Initialize messages if not already present
        if not st.session_state.messages:
            # In a real implementation, we would restore the full message history
            st.session_state.messages = [
                {"role": "system", "content": "Session restored from previous state."}
            ]
        
        # Display continuation notice
        st.success("Session restored from previous state")
        with st.expander("Session Context", expanded=False):
            st.markdown(format_transition_prompt(transition_prompt))

# Monitor for state extraction signal
def check_for_extraction_signal():
    """Check if a signal file exists to trigger state extraction"""
    if SIGNAL_FILE.exists():
        try:
            # Save current state
            state = {
                "history": st.session_state.get("messages", []),
                "transition_prompt": st.session_state.get("transition_prompt", {}),
                # Add other state elements as needed
            }
            
            # Make sure the directory exists
            SIGNAL_FILE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Write state to file
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
                
            # Remove signal file
            SIGNAL_FILE.unlink()
            
            # Display notification
            st.toast("State extracted successfully", icon="✅")
            return True
        except Exception as e:
            st.error(f"Failed to extract state: {e}")
            return False
    return False

# Check for signal on app startup
check_for_extraction_signal()

# Sidebar with controls
with st.sidebar:
    st.title("Continuity Test App")
    st.markdown("This app demonstrates state persistence for Claude DC.")
    
    # Add a button to manually extract state
    if st.button("Extract State Now"):
        # Create signal file to trigger extraction
        SIGNAL_FILE_DIR.mkdir(parents=True, exist_ok=True)
        SIGNAL_FILE.touch()
        
        # Wait a moment for the extraction to happen
        time.sleep(0.5)
        
        # Check if extraction was successful
        if check_for_extraction_signal():
            st.success(f"State saved to {STATE_FILE}")
        else:
            st.error("State extraction may not have completed")
    
    # Add controls for testing continuity
    st.divider()
    st.subheader("Testing Controls")
    
    # Simulate a conversation
    test_message = st.text_input("Test message")
    if st.button("Send Message"):
        if test_message:
            # Add message to history
            st.session_state.messages.append({"role": "user", "content": test_message})
            
            # Simulate a response
            response = f"You said: {test_message}"
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clear conversation
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.transition_prompt = None
        st.success("Conversation cleared")

# Main app area
st.title("Claude DC Continuity Test")

# Display conversation
st.subheader("Conversation")
for message in st.session_state.messages:
    role = message.get("role", "unknown")
    content = message.get("content", "")
    
    if role == "user":
        st.markdown(f"**User**: {content}")
    elif role == "assistant":
        st.markdown(f"**Claude**: {content}")
    elif role == "system":
        st.info(content)
    else:
        st.markdown(f"**{role}**: {content}")

# Display transition prompt if available
if st.session_state.transition_prompt:
    st.subheader("Active Transition Prompt")
    with st.expander("View Transition Prompt", expanded=False):
        st.markdown(format_transition_prompt(st.session_state.transition_prompt))

# Footer
st.divider()
st.markdown("*This is a test app for demonstrating the Claude DC continuity solution*")

# Continue checking for extraction signal
check_for_extraction_signal()