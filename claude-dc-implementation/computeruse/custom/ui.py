#!/usr/bin/env python3
"""
Streamlit UI for Claude Custom Agent
Provides a simple interface for interacting with the custom Claude agent.
"""

import os
import sys
import asyncio
import streamlit as st
from pathlib import Path
import base64
from PIL import Image
import io

# Add parent directory to path to allow importing agent_loop
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

# Import agent_loop module
from agent_loop import (
    agent_loop, 
    ToolResult, 
    execute_tool, 
    validate_tool_parameters
)

# Configure page settings
st.set_page_config(
    page_title="Claude Custom Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to convert asyncio calls to sync for Streamlit
def run_async(coroutine):
    """Run an async function in a synchronous context"""
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "tool_output" not in st.session_state:
        st.session_state.tool_output = None
    
    if "current_response" not in st.session_state:
        st.session_state.current_response = ""

def add_message(role, content, is_tool_output=False):
    """Add a message to the chat history"""
    if is_tool_output:
        st.session_state.messages.append({"role": role, "content": content, "is_tool_output": True})
    else:
        st.session_state.messages.append({"role": role, "content": content})

def handle_tool_output(tool_result):
    """Format tool output for display"""
    if tool_result is None:
        return None
    
    output = ""
    if hasattr(tool_result, "error") and tool_result.error:
        output = f"Error: {tool_result.error}"
    elif hasattr(tool_result, "output") and tool_result.output:
        output = tool_result.output
    
    # Handle base64 image if present
    image = None
    if hasattr(tool_result, "base64_image") and tool_result.base64_image:
        try:
            image_data = base64.b64decode(tool_result.base64_image)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            output += f"\nError displaying image: {str(e)}"
    
    return {"text": output, "image": image}

async def process_stream(conversation_history, stream_container, tool_container, config):
    """Process the streaming response from Claude"""
    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = st.session_state.get("api_key", "")
        if not api_key:
            stream_container.error("Please provide an API key in the sidebar settings.")
            return conversation_history
    
    # Get configuration options
    enable_streaming = config.get("enable_streaming", True)
    enable_thinking = config.get("enable_thinking", True)
    enable_prompt_caching = config.get("enable_prompt_caching", True)
    enable_extended_output = config.get("enable_extended_output", True)
    model = config.get("model", "claude-3-7-sonnet-20250219")
    max_tokens = config.get("max_tokens", 16000)
    thinking_budget = config.get("thinking_budget", 4000)
    
    try:
        # Create placeholders for streaming output
        response_placeholder = stream_container.empty()
        tool_placeholder = tool_container.empty()
        
        # Create a streaming callback handler
        def update_stream(chunk_text):
            """Update the streaming output"""
            st.session_state.current_response += chunk_text
            response_placeholder.markdown(st.session_state.current_response)
        
        # Create a tool execution callback handler
        def update_tool_output(tool_name, tool_input, tool_result):
            """Update the tool output display"""
            formatted_output = handle_tool_output(tool_result)
            if formatted_output:
                tool_output_md = f"### Tool: {tool_name}\n**Input:** ```json\n{tool_input}\n```\n\n**Output:**\n```\n{formatted_output['text']}\n```"
                tool_placeholder.markdown(tool_output_md)
                
                # Display image if available
                if formatted_output['image']:
                    tool_placeholder.image(formatted_output['image'])
                
                # Update session state
                st.session_state.tool_output = formatted_output
        
        # Custom callbacks for the agent loop
        callbacks = {
            "on_text": update_stream,
            "on_tool_use": lambda tool_name, tool_input: tool_placeholder.info(f"Executing tool: {tool_name}"),
            "on_tool_result": update_tool_output
        }
        
        # Reset the current response
        st.session_state.current_response = ""
        response_placeholder.markdown("_Thinking..._")
        
        # Call the agent loop
        user_message = conversation_history[-1]["content"]
        updated_history = await agent_loop(
            user_input=user_message,
            conversation_history=conversation_history[:-1],  # Exclude the latest message
            enable_streaming=enable_streaming,
            enable_thinking=enable_thinking,
            enable_prompt_caching=enable_prompt_caching,
            enable_extended_output=enable_extended_output,
            model=model,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget
        )
        
        # Add the response to the UI
        if st.session_state.current_response:
            add_message("assistant", st.session_state.current_response)
        
        # Return the updated conversation history
        return updated_history
        
    except Exception as e:
        stream_container.error(f"Error: {str(e)}")
        return conversation_history

def on_submit():
    """Handle form submission"""
    if st.session_state.user_input:
        user_message = st.session_state.user_input
        st.session_state.user_input = ""
        
        # Add user message to UI and conversation history
        add_message("user", user_message)
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Create containers for streaming output and tool display
        response_container = st.empty()
        tool_container = st.empty()
        
        # Get configuration options
        config = {
            "enable_streaming": st.session_state.get("enable_streaming", True),
            "enable_thinking": st.session_state.get("enable_thinking", True),
            "enable_prompt_caching": st.session_state.get("enable_prompt_caching", True),
            "enable_extended_output": st.session_state.get("enable_extended_output", True),
            "model": st.session_state.get("model", "claude-3-7-sonnet-20250219"),
            "max_tokens": st.session_state.get("max_tokens", 16000),
            "thinking_budget": st.session_state.get("thinking_budget", 4000)
        }
        
        # Process the response
        updated_history = run_async(
            process_stream(
                st.session_state.conversation_history, 
                response_container, 
                tool_container,
                config
            )
        )
        
        # Update conversation history
        st.session_state.conversation_history = updated_history

def create_ui():
    """Create the Streamlit UI"""
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar with settings
    with st.sidebar:
        st.title("Claude Custom Agent")
        st.subheader("Configuration")
        
        # API key input (optional - can also use environment variable)
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            st.session_state.api_key = st.text_input("Anthropic API Key", 
                                                    value=st.session_state.get("api_key", ""), 
                                                    type="password")
        
        # Model selection
        st.session_state.model = st.selectbox(
            "Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"],
            index=0
        )
        
        # Feature toggles
        st.session_state.enable_streaming = st.toggle("Enable Streaming", value=True)
        st.session_state.enable_thinking = st.toggle("Enable Thinking", value=True)
        st.session_state.enable_prompt_caching = st.toggle("Enable Prompt Caching", value=True)
        st.session_state.enable_extended_output = st.toggle("Enable Extended Output", value=True)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.session_state.max_tokens = st.slider("Max Tokens", 1000, 32000, 16000)
            st.session_state.thinking_budget = st.slider("Thinking Budget", 1024, 8000, 4000)
        
        # Clear conversation button
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.messages = []
            st.session_state.tool_output = None
            st.session_state.current_response = ""
            st.rerun()
    
    # Main chat interface
    st.title("Claude Custom Agent 🤖")
    st.caption("Minimal implementation with streaming, tool use, and thinking")
    
    # Create a container for the chat history
    chat_container = st.container()
    
    # Create a form for user input
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", key="user_input", height=100)
        submit_button = st.form_submit_button("Send", on_click=on_submit)
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            elif message["role"] == "assistant":
                if message.get("is_tool_output"):
                    with st.chat_message("assistant"):
                        st.info("Tool Output:")
                        st.write(message["content"])
                        if "image" in message and message["image"]:
                            st.image(message["image"])
                else:
                    st.chat_message("assistant").write(message["content"])

if __name__ == "__main__":
    create_ui()