#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Communication Dashboard Application
---------------------------------
Streamlit-based dashboard for the integrated communication system that routes
messages to the most appropriate AI with full contextual information.
"""

import os
import json
import logging
import time
from datetime import datetime
import streamlit as st
from typing import Dict, List, Any, Optional

# Local imports
from src.processor.transcript_processor_enhanced import TranscriptProcessor
from src.dashboard.bach_router import BachRouter
from src.dashboard.dashboard_mcp_connector import DashboardMCPConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard_app")

# Constants
AI_SYSTEMS = ["claude", "chatgpt", "grok", "gemini"]
DEFAULT_MAX_TOKENS = 1000

# Initialization
@st.cache_resource
def initialize_components():
    """Initialize dashboard components."""
    processor = TranscriptProcessor()
    router = BachRouter()
    connector = DashboardMCPConnector()
    
    return {
        "processor": processor,
        "router": router,
        "connector": connector
    }

def initialize_session_state():
    """Initialize session state variables."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "patterns" not in st.session_state:
        st.session_state.patterns = {}
        
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {
            "preferred_ai": "auto",
            "response_length": "standard",
            "pattern_visibility": "minimal"
        }
        
    if "system_health" not in st.session_state:
        st.session_state.system_health = {
            "status": "unknown",
            "models": {}
        }
        
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

def display_header():
    """Display dashboard header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🌊 Communication Dashboard")
        st.write("Powered by Bach-inspired mathematical routing")
    
    with col2:
        st.write("")
        st.write("")
        server_status = st.session_state.system_health.get("status", "unknown")
        # Check for various positive status values
        is_online = server_status in ["ok", "healthy", "online", "running"]
        st.write(f"Server Status: {'🟢 Online' if is_online else '🔴 Offline'}")

def display_sidebar():
    """Display sidebar with settings and preferences."""
    st.sidebar.title("Settings")
    
    # User preferences
    st.sidebar.header("Preferences")
    
    # AI preference
    ai_preference = st.sidebar.radio(
        "AI Routing Mode:",
        ["auto", "claude", "chatgpt", "grok", "gemini"],
        index=0
    )
    
    if ai_preference != st.session_state.user_preferences["preferred_ai"]:
        st.session_state.user_preferences["preferred_ai"] = ai_preference
    
    # Response length
    response_length = st.sidebar.select_slider(
        "Response Length:",
        options=["concise", "standard", "detailed"],
        value=st.session_state.user_preferences["response_length"]
    )
    
    if response_length != st.session_state.user_preferences["response_length"]:
        st.session_state.user_preferences["response_length"] = response_length
    
    # Pattern visibility
    pattern_visibility = st.sidebar.select_slider(
        "Pattern Visibility:",
        options=["none", "minimal", "detailed"],
        value=st.session_state.user_preferences["pattern_visibility"]
    )
    
    if pattern_visibility != st.session_state.user_preferences["pattern_visibility"]:
        st.session_state.user_preferences["pattern_visibility"] = pattern_visibility
    
    # Debug mode
    debug_mode = st.sidebar.checkbox("Debug Mode", value=st.session_state.debug_mode)
    if debug_mode != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_mode
    
    # System health
    st.sidebar.header("System Health")

    status_color = {
        "online": "✅",
        "offline": "❌",
        "unknown": "⚠️"
    }

    for ai in AI_SYSTEMS:
        status_bool = st.session_state.system_health.get("models", {}).get(ai, False)
        status = "online" if status_bool else "offline"
        st.sidebar.write(f"{status_color[status]} {ai.capitalize()}: {status.capitalize()}")

    # Clear conversation
    if st.sidebar.button("Clear Conversation"):
        st.session_state.conversation_history = []
        st.session_state.patterns = {}
        st.experimental_rerun()

def display_conversation():
    """Display the conversation history."""
    for message in st.session_state.conversation_history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        if role == "user":
            st.chat_message("user").write(content)
        elif role == "assistant":
            # Use a default avatar if the AI-specific one can't be loaded
            try:
                ai_system = message.get("ai_system", "claude")
                with st.chat_message("assistant", avatar=ai_system):
                    st.write(content)
            except:
                # Fallback without avatar if there's an error
                with st.chat_message("assistant"):
                    st.write(content)
                
            # Show patterns if in debug mode
            if st.session_state.debug_mode and "patterns" in message:
                with st.expander("Patterns"):
                    pattern_count = sum(len(patterns) for patterns in message["patterns"].values())
                    st.write(f"Total patterns: {pattern_count}")
                    
                    for pattern_type, patterns in message["patterns"].items():
                        if patterns:
                            st.write(f"**{pattern_type}** ({len(patterns)})")
                            for pattern in patterns[:3]:  # Show top 3
                                st.write(f"- {pattern.get('text')} ({pattern.get('confidence', 0):.2f})")
            
            # Show routing info if in debug mode
            if st.session_state.debug_mode and "routing_info" in message:
                with st.expander("Routing Info"):
                    match_scores = message["routing_info"].get("match_scores", {})
                    st.write("Match scores:")
                    for ai, score in match_scores.items():
                        st.write(f"- {ai}: {score:.2f}")

def process_message(components, message):
    """
    Process a user message through the router and selected AI.
    
    Args:
        components: Dashboard components (processor, router, connector)
        message: User message
    """
    # Don't process empty messages
    if not message.strip():
        return
    
    try:
        # Extract patterns from the message
        message_patterns = components["processor"].process_transcript({"text": message, "source": "user"})
        
        # Create context
        context = {
            "conversation_history": st.session_state.conversation_history,
            "patterns": message_patterns,
            "user_preferences": st.session_state.user_preferences
        }
        
        # Route message
        selected_ai = st.session_state.user_preferences["preferred_ai"]
        routing_info = {}
        
        if selected_ai == "auto":
            # Use router to select the best AI
            selected_ai, confidence, routing_info = components["router"].route_message(message, context)
        
        # Log the selected AI
        logger.info(f"Selected AI: {selected_ai} for message: {message[:50]}...")
        
        # Update context with routing info
        context["routing_info"] = routing_info
        
        # Determine token limit based on response length preference
        token_map = {
            "concise": 600,
            "standard": 1000,
            "detailed": 1600
        }
        max_tokens = token_map.get(st.session_state.user_preferences["response_length"], DEFAULT_MAX_TOKENS)
        
        # Create user message
        user_message = {"role": "user", "content": message}
        
        # Add to conversation history
        st.session_state.conversation_history.append(user_message)
        
        # Create a placeholder for the assistant message
        message_placeholder = st.empty()
        message_placeholder.write("🔄 Thinking...")
            
        # Send to selected AI through MCP
        response = components["connector"].send_message(
            message=message,
            target_model=selected_ai,
            context=context,
            max_tokens=max_tokens
        )
        
        # Extract response content
        assistant_content = "Error: Unable to get response"
        if "error" in response:
            assistant_content = f"⚠️ Error: {response['error']}"
        else:
            if "content" in response and response["content"]:
                assistant_content = response["content"]
            elif "choices" in response and response["choices"] and "message" in response["choices"][0]:
                assistant_content = response["choices"][0]["message"].get("content", "")
            elif isinstance(response, str):
                assistant_content = response
            else:
                assistant_content = str(response)
        
        # Update placeholder with response
        message_placeholder.write(assistant_content)
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
            "ai_system": selected_ai,
            "timestamp": time.time(),
            "patterns": message_patterns,
            "routing_info": routing_info
        }
        
        # Add to conversation history
        st.session_state.conversation_history.append(assistant_message)
        
        # Update stored patterns
        for pattern_type, patterns in message_patterns.items():
            if pattern_type not in st.session_state.patterns:
                st.session_state.patterns[pattern_type] = []
            st.session_state.patterns[pattern_type].extend(patterns)
            
        # Return the response
        return assistant_message
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

def display_pattern_visualization():
    """Display visualization of detected patterns."""
    if not st.session_state.patterns:
        return
    
    # Only display if pattern visibility is detailed
    if st.session_state.user_preferences["pattern_visibility"] != "detailed":
        return
    
    st.header("Pattern Analysis")
    
    # Count patterns by type
    pattern_counts = {k: len(v) for k, v in st.session_state.patterns.items()}
    
    # Display as bar chart
    st.bar_chart(pattern_counts)
    
    # Show top patterns
    st.subheader("Top Patterns")
    
    # Flatten and sort patterns by confidence
    all_patterns = []
    for pattern_type, patterns in st.session_state.patterns.items():
        for pattern in patterns:
            pattern["type"] = pattern_type
            all_patterns.append(pattern)
    
    # Sort by confidence
    all_patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
    
    # Display top 5
    for i, pattern in enumerate(all_patterns[:5]):
        st.write(f"{i+1}. **{pattern.get('type')}**: {pattern.get('text')} ({pattern.get('confidence', 0):.2f})")

def main():
    """Main dashboard function."""
    # Initialize
    components = initialize_components()
    initialize_session_state()
    
    # Update system health
    st.session_state.system_health = components["connector"].check_server_health()
    
    # Display UI components
    display_header()
    display_sidebar()
    
    # Patterns visualization (if detailed mode)
    if st.session_state.user_preferences["pattern_visibility"] == "detailed":
        display_pattern_visualization()
    
    # Display conversation history
    display_conversation()
    
    # Message input
    user_message = st.chat_input("Type your message here...")
    if user_message:
        process_message(components, user_message)

if __name__ == "__main__":
    main()
