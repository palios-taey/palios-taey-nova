"""
Integrated Streamlit UI for Claude DC

This module extends the official Anthropic Quickstarts Streamlit UI with
additional features like streaming support, state persistence, and ROSETTA STONE
communication protocol.

The implementation uses a bridge pattern to combine the stable foundation of
the official implementation with our custom enhancements.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
import streamlit as st

# Add integration framework path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import integration bridge
from integration_framework import create_bridge, FeatureToggle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integrated_streamlit")

# Feature toggles for this session - can be modified via UI
FEATURE_TOGGLES = {
    FeatureToggle.USE_STREAMING: True,
    FeatureToggle.USE_THINKING: True,
    FeatureToggle.USE_ROSETTA_STONE: False,
    FeatureToggle.USE_STREAMLIT_CONTINUITY: True
}

# Create integration bridge
bridge = create_bridge(FEATURE_TOGGLES)

# Check if we're restoring from a previous session
def initialize_session():
    """Initialize or restore Streamlit session state"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        
        if FEATURE_TOGGLES[FeatureToggle.USE_STREAMLIT_CONTINUITY]:
            try:
                # Try to restore previous state if available
                if hasattr(bridge, "restore_state"):
                    bridge.restore_state(st.session_state)
                    logger.info("Restored previous session state")
                else:
                    logger.info("Continuity feature enabled but restore_state not available")
            except Exception as e:
                logger.error(f"Failed to restore state: {str(e)}")

        # Initialize default state if not already set
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "conversation_mode" not in st.session_state:
            st.session_state.conversation_mode = "chat"  # or "dccc" for ROSETTA STONE mode

# Define UI components
def render_sidebar():
    """Render the sidebar with feature toggles and controls"""
    st.sidebar.title("Claude DC Controls")
    
    # Model selection
    model = st.sidebar.selectbox(
        "Model",
        ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620"],
        index=0
    )
    
    # Feature toggles
    st.sidebar.subheader("Features")
    
    # Streaming toggle
    streaming_enabled = st.sidebar.checkbox(
        "Enable Streaming",
        value=FEATURE_TOGGLES[FeatureToggle.USE_STREAMING]
    )
    FEATURE_TOGGLES[FeatureToggle.USE_STREAMING] = streaming_enabled
    
    # Thinking toggle
    thinking_enabled = st.sidebar.checkbox(
        "Enable Thinking",
        value=FEATURE_TOGGLES[FeatureToggle.USE_THINKING]
    )
    FEATURE_TOGGLES[FeatureToggle.USE_THINKING] = thinking_enabled
    
    # Thinking budget (only if thinking is enabled)
    thinking_budget = None
    if thinking_enabled:
        thinking_budget = st.sidebar.slider(
            "Thinking Budget (tokens)",
            min_value=1000,
            max_value=32000,
            value=4000,
            step=1000
        )
    
    # ROSETTA STONE toggle
    rosetta_stone_enabled = st.sidebar.checkbox(
        "Enable ROSETTA STONE Protocol",
        value=FEATURE_TOGGLES[FeatureToggle.USE_ROSETTA_STONE]
    )
    FEATURE_TOGGLES[FeatureToggle.USE_ROSETTA_STONE] = rosetta_stone_enabled
    
    # Continuity toggle
    continuity_enabled = st.sidebar.checkbox(
        "Enable Streamlit Continuity",
        value=FEATURE_TOGGLES[FeatureToggle.USE_STREAMLIT_CONTINUITY]
    )
    FEATURE_TOGGLES[FeatureToggle.USE_STREAMLIT_CONTINUITY] = continuity_enabled
    
    # Conversation mode
    if rosetta_stone_enabled:
        st.session_state.conversation_mode = st.sidebar.radio(
            "Conversation Mode",
            ["chat", "dccc"],
            index=0 if st.session_state.conversation_mode == "chat" else 1
        )
    
    # Debug section
    with st.sidebar.expander("Debug Information"):
        st.write("Active Features:")
        for feature, enabled in FEATURE_TOGGLES.items():
            st.write(f"- {feature.name}: {'✅' if enabled else '❌'}")
        
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.rerun()

    return {
        "model": model,
        "thinking_budget": thinking_budget
    }

# Main message display
def render_messages():
    """Render the conversation messages"""
    for message in st.session_state.messages:
        role = message.get("role", "")
        content = message.get("content", "")
        
        if role == "user":
            with st.chat_message("user"):
                if isinstance(content, str):
                    st.write(content)
                elif isinstance(content, list):
                    # Handle content blocks
                    for block in content:
                        if block.get("type") == "text":
                            st.write(block.get("text", ""))
                        elif block.get("type") == "tool_result":
                            st.write("Tool Result:")
                            st.json(block)
        
        elif role == "assistant":
            with st.chat_message("assistant"):
                if isinstance(content, str):
                    st.write(content)
                elif isinstance(content, list):
                    # Handle content blocks
                    for block in content:
                        if block.get("type") == "text":
                            st.write(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            st.write(f"Using tool: {block.get('name', 'unknown')}")
                            with st.expander("Tool details"):
                                st.json(block)
                        elif block.get("type") == "thinking":
                            with st.expander("Thinking"):
                                st.write(block.get("thinking", ""))

# Main application
async def main():
    """Main application flow"""
    st.title("DCCC - Claude DC Integration")
    
    # Initialize session
    initialize_session()
    
    # Render sidebar and get settings
    settings = render_sidebar()
    
    # Render existing messages
    render_messages()
    
    # Get user input
    user_input = st.chat_input("Ask Claude DC...")
    
    if user_input:
        # Format with ROSETTA STONE if enabled
        if FEATURE_TOGGLES[FeatureToggle.USE_ROSETTA_STONE] and st.session_state.conversation_mode == "dccc":
            # Example formatting for ROSETTA STONE
            formatted_input = bridge.format_rosetta_stone("USER", "QUERY", user_input)
        else:
            formatted_input = user_input
        
        # Add user message to conversation
        st.session_state.messages.append({"role": "user", "content": formatted_input})
        
        # Show user message immediately
        with st.chat_message("user"):
            st.write(formatted_input)
        
        # Show assistant thinking indicator
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            if FEATURE_TOGGLES[FeatureToggle.USE_THINKING]:
                thinking_placeholder.write("Thinking...")
            
            # Define callbacks for streaming updates
            def output_callback(content_block):
                if content_block.get("type") == "text":
                    thinking_placeholder.write(content_block.get("text", ""))
                elif content_block.get("type") == "thinking":
                    with st.expander("Thinking"):
                        st.write(content_block.get("thinking", ""))
            
            def tool_output_callback(result, tool_id):
                # Update UI with tool results
                st.write(f"Tool result for {tool_id}:")
                st.write(result.output if hasattr(result, "output") else str(result))
            
            def api_response_callback(request, response, error):
                # Log API response but don't show in UI
                if error:
                    logger.error(f"API error: {str(error)}")
            
            # Process the user input and get response
            try:
                # Call the sampling loop via bridge
                st.session_state.messages = await bridge.sampling_loop(
                    messages=st.session_state.messages,
                    model=settings["model"],
                    output_callback=output_callback,
                    tool_output_callback=tool_output_callback,
                    api_response_callback=api_response_callback,
                    api_key=os.environ.get("ANTHROPIC_API_KEY"),
                    thinking_budget=settings["thinking_budget"]
                )
                
                # Save state if continuity is enabled
                if FEATURE_TOGGLES[FeatureToggle.USE_STREAMLIT_CONTINUITY] and hasattr(bridge, "save_state"):
                    bridge.save_state(st.session_state)
            
            except Exception as e:
                logger.error(f"Error in sampling loop: {str(e)}")
                thinking_placeholder.error(f"Error: {str(e)}")

# Run the application
if __name__ == "__main__":
    asyncio.run(main())