#!/usr/bin/env python3
"""
Minimal Streamlit UI for Claude streaming agent loop.
"""

import os
import sys
import asyncio
import json
import logging
import streamlit as st
from typing import Dict, Any, List

# Import the minimal agent loop
from minimal_agent_loop import initialize_session, agent_loop, ToolResult

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("minimal_streamlit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("minimal_streamlit")

# Page configuration
st.set_page_config(
    page_title="Claude Computer Use - Minimal",
    page_icon=":robot_face:",
    layout="wide",
)

# Function to initialize the session
async def get_session():
    """Get or create a session for the agent."""
    if "session" not in st.session_state:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("No API key found. Please set the ANTHROPIC_API_KEY environment variable.")
            return None
        
        try:
            st.session_state.session = await initialize_session(api_key)
            st.session_state.messages = []
        except Exception as e:
            st.error(f"Error initializing session: {str(e)}")
            return None
    
    return st.session_state.session

# Main UI function
async def main():
    """Main UI function."""
    st.title("Claude Computer Use - Minimal Implementation")
    
    # Add sidebar with information
    with st.sidebar:
        st.header("Available Tools")
        st.subheader("Computer Tool")
        st.markdown("""
        - **screenshot**: Takes a screenshot
        - **move_mouse**: Moves the mouse to coordinates
        - **left_button_press**: Clicks at coordinates
        - **type_text**: Types text
        """)
        
        st.subheader("Bash Tool")
        st.markdown("""
        - Execute read-only bash commands
        - Allowed: ls, pwd, cat, echo, date, whoami, ps, grep, find, head, tail
        """)
        
        st.header("Example Commands")
        st.markdown("""
        - Take a screenshot
        - Move the mouse to position (100, 200)
        - Click at position (100, 200)
        - Type "Hello World"
        - List the files in the current directory
        """)
    
    # Initialize session
    session = await get_session()
    if not session:
        st.stop()
    
    # Create two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display conversation history
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.write(message["content"])
            elif message["role"] == "tool":
                # Show tool results in a special format
                with st.chat_message("assistant"):
                    if "image" in message:
                        st.image(message["image"], caption=message.get("caption", "Screenshot"))
                    if "text" in message:
                        st.code(message["text"])
    
    # Tool output area in the second column
    with col2:
        st.subheader("Tool Execution Results")
        tool_container = st.container()
    
    # Input from user
    user_input = st.chat_input("Ask Claude a question...")
    
    if user_input:
        # Add user message to UI
        with st.chat_message("user"):
            st.write(user_input)
        
        # Add user message to history (for UI only)
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Create a placeholder for the assistant's response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            current_response = ""
            
            # Callback for streaming text output
            def text_callback(text):
                nonlocal current_response
                current_response += text
                response_placeholder.write(current_response)
            
            # Callback for thinking output (not used yet)
            def thinking_callback(thinking_text):
                with tool_container:
                    st.text("Thinking: " + thinking_text[:100] + "...")
            
            # Callback for tool use
            def tool_use_callback(tool_name, tool_input):
                with tool_container:
                    st.info(f"Using tool: {tool_name}")
                    st.json(tool_input)
            
            # Callback for tool results
            def tool_result_callback(result):
                with tool_container:
                    if result.error:
                        st.error(f"Tool error: {result.error}")
                    else:
                        if result.output:
                            st.success(f"Tool output: {result.output}")
                        
                        if result.base64_image:
                            st.image(
                                f"data:image/png;base64,{result.base64_image}",
                                caption="Screenshot Result"
                            )
                            
                            # Save to history for display in conversation
                            st.session_state.messages.append({
                                "role": "tool",
                                "image": f"data:image/png;base64,{result.base64_image}",
                                "caption": "Screenshot Result",
                                "text": result.output
                            })
            
            # Execute the agent loop
            try:
                await agent_loop(
                    session=session,
                    user_input=user_input,
                    text_callback=text_callback,
                    thinking_callback=thinking_callback,
                    tool_use_callback=tool_use_callback,
                    tool_result_callback=tool_result_callback
                )
                
                # Add assistant message to history (for UI only)
                if current_response.strip():  # Only if there's text content
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": current_response
                    })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                logger.error(f"Error in agent loop: {str(e)}", exc_info=True)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())