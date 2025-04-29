"""
Streamlit UI for Claude Computer Use with streaming capability.
This provides a simple interface for interacting with the agent loop.
"""

import os
import sys
import asyncio
import streamlit as st
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("streamlit_app.log")
    ]
)
logger = logging.getLogger("streamlit_ui")

# Add the current directory to path for importing the agent_loop module
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

try:
    # Import the agent_loop module
    from loop import agent_loop, DEFAULT_SYSTEM_PROMPT
except ImportError as e:
    st.error(f"Error importing agent_loop module: {e}")
    logger.error(f"Error importing agent_loop module: {e}")
    sys.exit(1)

try:
    # Try to import nest_asyncio for running async code in Streamlit
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    st.error("nest_asyncio not installed. Please install with: pip install nest_asyncio")
    sys.exit(1)

# Function to run async code in Streamlit
def run_async(coroutine):
    """Run an async function in a synchronous context"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    # Initialize conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize Claude history
    if "claude_history" not in st.session_state:
        st.session_state.claude_history = []
    
    # Initialize current response
    if "current_response" not in st.session_state:
        st.session_state.current_response = ""
    
    # Initialize tool state
    if "current_tool" not in st.session_state:
        st.session_state.current_tool = None
    
    # Initialize API key
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    # Initialize configuration
    if "model" not in st.session_state:
        st.session_state.model = "claude-3-7-sonnet-20250219"
    
    if "enable_thinking" not in st.session_state:
        st.session_state.enable_thinking = True
    
    if "enable_prompt_caching" not in st.session_state:
        st.session_state.enable_prompt_caching = True
    
    if "enable_extended_output" not in st.session_state:
        st.session_state.enable_extended_output = True
    
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 16000
    
    if "thinking_budget" not in st.session_state:
        st.session_state.thinking_budget = 4000
    
    # Initialize debug mode
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

def create_sidebar():
    """Create the sidebar with configuration options"""
    with st.sidebar:
        st.title("Claude Computer Use")
        st.subheader("Configuration")
        
        # API key input
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            st.session_state.api_key = st.text_input(
                "Anthropic API Key", 
                value=st.session_state.api_key,
                type="password"
            )
        
        # Model selection
        st.session_state.model = st.selectbox(
            "Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"],
            index=0
        )
        
        # Feature toggles
        st.session_state.enable_thinking = st.toggle("Enable Thinking", value=True)
        st.session_state.enable_prompt_caching = st.toggle("Enable Prompt Caching", value=True)
        st.session_state.enable_extended_output = st.toggle("Enable Extended Output", value=True)
        st.session_state.debug_mode = st.toggle("Debug Mode", value=False)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.session_state.max_tokens = st.slider("Max Tokens", 1000, 32000, 16000)
            if st.session_state.enable_thinking:
                st.session_state.thinking_budget = st.slider("Thinking Budget", 1024, 8000, 4000)
        
        # Clear conversation button
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.claude_history = []
            st.session_state.current_response = ""
            st.session_state.current_tool = None
            st.rerun()

def handle_output_event(event, response_container):
    """Handle an output event from the agent loop"""
    
    # Debug output
    if st.session_state.debug_mode:
        with response_container:
            st.text(f"DEBUG: {event}")
    
    # Handle different event types
    if event.get("type") == "text_delta":
        st.session_state.current_response += event.get("text", "")
        with response_container:
            st.markdown(st.session_state.current_response)
    
    elif event.get("type") == "content_start":
        # Content block is starting
        st.session_state.current_response = ""
        with response_container:
            st.empty()
    
    elif event.get("type") == "tool_use_start":
        tool_name = event.get("name", "")
        tool_id = event.get("id", "")
        st.session_state.current_tool = {
            "name": tool_name,
            "id": tool_id,
            "input": {},
            "output": "Preparing tool execution..."
        }
        with response_container:
            st.info(f"Using tool: {tool_name}")
    
    elif event.get("type") == "tool_input_delta":
        if st.session_state.current_tool:
            # Accumulate tool input
            # (Just for UI display - actual accumulation happens in the agent loop)
            input_delta = event.get("input_delta", "")
            with response_container:
                st.info(f"Building tool input: {input_delta}")
    
    elif event.get("type") == "tool_executing":
        if st.session_state.current_tool:
            tool_name = event.get("name", "")
            tool_input = event.get("input", {})
            st.session_state.current_tool["input"] = tool_input
            with response_container:
                st.info(f"Executing tool: {tool_name}\nInput: {json.dumps(tool_input, indent=2)}")
    
    elif event.get("type") == "tool_progress":
        if st.session_state.current_tool:
            progress_msg = event.get("message", "")
            st.session_state.current_tool["output"] = progress_msg
            with response_container:
                st.info(f"Tool progress: {progress_msg}")
    
    elif event.get("type") == "tool_result":
        if st.session_state.current_tool:
            result = event.get("result", "")
            st.session_state.current_tool["output"] = result
            with response_container:
                st.success(f"Tool result: {result}")
    
    elif event.get("type") == "error":
        with response_container:
            st.error(f"Error: {event.get('message', 'Unknown error')}")
    
    elif event.get("type") == "message_stop":
        # Final cleanup
        with response_container:
            if not st.session_state.current_response:
                st.info("Message complete (no text response)")

async def process_user_message(user_input, response_container):
    """Process a user message and handle the response"""
    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY", st.session_state.api_key)
    if not api_key:
        with response_container:
            st.error("Please provide an API key in the sidebar settings.")
        return
    
    # Show thinking indicator
    with response_container:
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("_Thinking..._")
    
    # Reset current response
    st.session_state.current_response = ""
    st.session_state.current_tool = None
    
    # Configure callbacks
    def handle_output(event):
        handle_output_event(event, response_container)
    
    def handle_tool_output(tool_input, tool_id):
        # This could be enhanced to show tool output in a different way
        pass
    
    # Get thinking budget if enabled
    thinking_budget = None
    if st.session_state.enable_thinking:
        thinking_budget = st.session_state.thinking_budget
    
    # Create user message
    user_message = {"role": "user", "content": user_input}
    
    # Add to Claude's history
    claude_history = list(st.session_state.claude_history)
    claude_history.append(user_message)
    
    try:
        # Run the agent loop
        updated_history = await agent_loop(
            model=st.session_state.model,
            messages=claude_history,
            output_callback=handle_output,
            tool_output_callback=handle_tool_output,
            max_tokens=st.session_state.max_tokens,
            thinking_budget=thinking_budget,
            api_key=api_key,
            enable_prompt_caching=st.session_state.enable_prompt_caching,
            enable_extended_output=st.session_state.enable_extended_output,
            debug=st.session_state.debug_mode
        )
        
        # Remove thinking indicator
        thinking_placeholder.empty()
        
        # Update Claude history
        st.session_state.claude_history = updated_history
        
        # Add assistant response to chat
        if st.session_state.current_response:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": st.session_state.current_response
            })
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        with response_container:
            st.error(f"Error: {e}")

def main():
    """Main Streamlit application"""
    # Set page config
    st.set_page_config(
        page_title="Claude Computer Use",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    create_sidebar()
    
    # Create main layout
    st.title("Claude Computer Use 🤖")
    st.caption("Streaming implementation with tool use & thinking")
    
    # Create message container
    message_container = st.container()
    
    # Display chat messages
    with message_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
    
    # Create input area
    user_input = st.chat_input("Your message to Claude:")
    
    # Process user input
    if user_input:
        # Add user message to chat
        with message_container:
            with st.chat_message("user"):
                st.write(user_input)
        
        # Add to conversation history for UI display
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Create response container
        response_container = st.empty()
        
        # Process message
        run_async(process_user_message(user_input, response_container))

if __name__ == "__main__":
    main()