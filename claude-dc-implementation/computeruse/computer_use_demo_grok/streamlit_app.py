"""
Streamlit UI for Claude DC with streaming support.
This implements the UI for Claude DC using Streamlit.
"""
import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
import threading

import streamlit as st
import nest_asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("claude_dc.log")
    ]
)
logger = logging.getLogger("streamlit_ui")

# Apply nest_asyncio to run asyncio in Streamlit
nest_asyncio.apply()

# Import agent loop for conversation
try:
    from loop import agent_loop, chat_with_claude, AVAILABLE_TOOLS
    from anthropic import AsyncAnthropic
    import anthropic
    logger.info(f"Using Anthropic SDK version: {anthropic.__version__}")
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Run: pip install anthropic==0.50.0 streamlit==1.31.0 nest_asyncio==1.5.8")
    sys.exit(1)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "thinking" not in st.session_state:
    st.session_state.thinking = None

if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

if "api_client" not in st.session_state:
    # Create client with beta flags in header
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        st.session_state.api_client = AsyncAnthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
        )
    else:
        st.error("ANTHROPIC_API_KEY environment variable not set!")

# Set up UI
st.title("Claude DC - Streaming Implementation")
st.caption("GROK Implementation with streaming and tool use")

# Configuration sidebar
with st.sidebar:
    st.header("Settings")
    
    # Model selection
    model = st.selectbox(
        "Model",
        ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620"],
        index=0
    )
    
    # Max tokens
    max_tokens = st.slider("Max Tokens", min_value=1000, max_value=64000, value=4000, step=1000)
    
    # Temperature
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    # Thinking parameter
    thinking_enabled = st.checkbox("Enable Thinking", value=True)
    thinking_budget = st.slider("Thinking Budget (tokens)", min_value=256, max_value=8192, value=1024, step=256,
                               disabled=not thinking_enabled)
    
    # Show thinking toggle
    show_thinking = st.checkbox("Show Thinking", value=False)
    
    st.divider()
    
    # Save/Load conversation
    st.header("Conversation")
    
    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.session_state.thinking = None
        st.rerun()
    
    # Save conversation
    if st.button("Save Conversation"):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"conversation_{timestamp}.json"
        try:
            with open(filename, "w") as f:
                json.dump(st.session_state.conversation_history, f, indent=2)
            st.success(f"Conversation saved to {filename}")
        except Exception as e:
            st.error(f"Error saving conversation: {e}")
    
    # Show conversation history
    conversation_json = st.toggle("Show Conversation JSON", value=False)
    if conversation_json:
        st.json(st.session_state.conversation_history)

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Display thinking if enabled
if show_thinking and st.session_state.thinking:
    with st.expander("Claude's Thinking Process", expanded=True):
        st.write(st.session_state.thinking)

# Create chat input
prompt = st.chat_input("Message Claude...")

# Handle user input
if prompt:
    # Add user message to UI and history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_history.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Set up thinking parameter if enabled
    thinking = None
    if thinking_enabled:
        thinking = {"type": "enabled", "budget_tokens": thinking_budget}
    
    # Create placeholder for streaming response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Create container for tool use outputs
        tool_container = st.container()
        
        # Start streaming with placeholder
        current_response_text = ""
        
        # Set streaming active flag
        st.session_state.streaming_active = True
        
        # Define stream handler function
        async def stream_handler(event):
            # Use the properly scoped variable
            nonlocal current_response_text
            
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                current_response_text += event.delta.text
                message_placeholder.markdown(current_response_text)
            
            elif event.type == "content_block_stop" and event.content_block.type == "tool_use":
                # Display tool use in the UI
                with tool_container:
                    st.info(f"Using tool: {event.content_block.tool_use.get('name', 'unknown')}")
                    st.json(event.content_block.tool_use)
            
            elif event.type == "message_delta" and event.delta.thinking:
                # Store thinking content
                st.session_state.thinking = event.delta.thinking
                # Update thinking display if enabled
                if show_thinking:
                    with st.sidebar:
                        with st.expander("Claude's Thinking Process", expanded=True):
                            st.write(event.delta.thinking)
        
        # Run agent loop in async function
        async def run_agent():
            try:
                response = await agent_loop(
                    client=st.session_state.api_client,
                    messages=st.session_state.conversation_history,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking=thinking,
                    stream_handler=stream_handler,
                    tools=AVAILABLE_TOOLS,
                    save_conversation=True
                )
                
                # Extract text content from response
                text_content = ""
                for block in response["content"]:
                    if block["type"] == "text" and block["text"]:
                        text_content += block["text"]
                
                # Add assistant response to history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": text_content
                })
                
                # Add to UI message history
                st.session_state.messages.append({"role": "assistant", "content": text_content})
                
                # Set streaming flag to False
                st.session_state.streaming_active = False
                
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                message_placeholder.error(f"Error: {str(e)}")
                st.session_state.streaming_active = False
        
        # Run in asyncio
        asyncio.run(run_agent())

# Add a footer with version info
st.divider()
st.caption(f"Claude DC GROK Implementation | Anthropic SDK v{anthropic.__version__} | Streamlit v{st.__version__}")