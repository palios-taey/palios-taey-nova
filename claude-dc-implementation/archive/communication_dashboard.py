#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrated Communication Dashboard for AI Models
-----------------------------------------------
This Streamlit application provides an integrated dashboard for 
routing communications between different AI models with full
contextual information.

The dashboard follows Bach's mathematical principles with:
- Golden ratio proportions in layout design
- Self-similar patterns at multiple scales
- Balanced, harmonious information flow
"""

import os
import sys
import json
import time
import hmac
import uuid
import math
import hashlib
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
import altair as alt
from PIL import Image
import base64
import io

# Custom module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utils.secrets import load_secrets
from src.mcp.mcp_client import MCPClient
from src.processor.enhanced_transcript_loader import EnhancedTranscriptLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/communication_dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("communication_dashboard")

# Load secrets
SECRETS = load_secrets()

# Constants - Bach-inspired mathematical patterns
GOLDEN_RATIO = 1.618033988749895
FIBONACCI_SEQUENCE = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

# MCP Server URL
MCP_SERVER_URL = "http://localhost:8001"

# Color schemes inspired by Bach's mathematical harmony
COLOR_SCHEME = {
    "primary": "#1E3A8A",       # Deep blue - representing depth
    "secondary": "#EAAE27",     # Golden - representing golden ratio
    "tertiary": "#4C1D95",      # Purple - representing creativity
    "claude": "#6366F1",        # Indigo - Claude's color
    "grok": "#5CAA47",          # Green - Grok's color
    "chatgpt": "#10B981",       # Teal - ChatGPT's color
    "gemini": "#A855F7",        # Purple - Gemini's color
    "background": "#F9FAFB",    # Light background
    "text": "#111827",          # Dark text
    "muted": "#6B7280",         # Muted text
    "highlight": "#FDE68A",     # Light yellow highlight
    "success": "#34D399",       # Green success
    "warning": "#FBBF24",       # Yellow warning
    "error": "#EF4444",         # Red error
}

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = str(uuid.uuid4())
    
    if 'pattern_data' not in st.session_state:
        st.session_state.pattern_data = {}
    
    if 'selected_patterns' not in st.session_state:
        st.session_state.selected_patterns = []
    
    if 'active_ai' not in st.session_state:
        st.session_state.active_ai = "claude"
    
    if 'wave_params' not in st.session_state:
        # Default wave parameters based on golden ratio
        st.session_state.wave_params = {
            "frequency": GOLDEN_RATIO,
            "amplitude": 0.5,
            "phase": 0.0,
            "harmonics": [1.0, GOLDEN_RATIO, GOLDEN_RATIO**2, GOLDEN_RATIO**3]
        }
    
    if 'conversations' not in st.session_state:
        st.session_state.conversations = []
    
    if 'refresh_patterns' not in st.session_state:
        st.session_state.refresh_patterns = True
    
    if 'loaded_patterns' not in st.session_state:
        st.session_state.loaded_patterns = False
    
    if 'mcp_client' not in st.session_state:
        # Initialize MCP client
        st.session_state.mcp_client = MCPClient(
            server_url=MCP_SERVER_URL,
            api_key=SECRETS.get("mcp", {}).get("api_key", "default_key")
        )

# Load pattern data
def load_pattern_data():
    """Load pattern data from pattern report."""
    if st.session_state.loaded_patterns and not st.session_state.refresh_patterns:
        return
    
    try:
        pattern_dir = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns"
        report_file = os.path.join(pattern_dir, "pattern_report.json")
        
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                data = json.load(f)
                
                st.session_state.pattern_data = data
                st.session_state.loaded_patterns = True
                st.session_state.refresh_patterns = False
                
                logger.info("Pattern data loaded successfully")
        else:
            logger.warning(f"Pattern report not found at {report_file}")
            st.warning("Pattern data not available. Please run transcript processing first.")
    except Exception as e:
        logger.error(f"Error loading pattern data: {str(e)}")
        st.error(f"Error loading pattern data: {str(e)}")

# Load conversations from transcripts
def load_conversations():
    """Load conversations from transcript loader."""
    if st.session_state.conversations:
        return
    
    try:
        # Initialize enhanced transcript loader
        loader = EnhancedTranscriptLoader(
            base_dir="/home/computeruse/github/palios-taey-nova/transcripts"
        )
        
        # Load conversations (sample 5 from each source)
        conversations = []
        
        for source in ["claude", "chatgpt", "grok", "gemini"]:
            source_convs = loader.load_transcripts(source=source, max_files=5)
            conversations.extend(source_convs)
        
        # Sort by timestamp (newest first)
        conversations.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        st.session_state.conversations = conversations
        logger.info(f"Loaded {len(conversations)} conversations")
    except Exception as e:
        logger.error(f"Error loading conversations: {str(e)}")

# Authentication helper
def generate_signature(payload: Dict[str, Any], secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payloads."""
    payload_bytes = json.dumps(payload).encode()
    return hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

# Call MCP server
def send_message_to_model(model: str, messages: List[Dict[str, str]], 
                         temperature: float = 0.7, include_patterns: bool = True) -> Dict[str, Any]:
    """
    Send a message to an AI model through the MCP server.
    
    Args:
        model: Target model (claude, grok, chatgpt, gemini)
        messages: List of message dictionaries with role and content
        temperature: Temperature for generation
        include_patterns: Whether to include pattern context
        
    Returns:
        Response from the model
    """
    try:
        # Add pattern context if requested
        if include_patterns and st.session_state.selected_patterns:
            # Create a pattern context message
            patterns_text = "Here are some relevant patterns to consider:\n\n"
            
            for pattern in st.session_state.selected_patterns:
                patterns_text += f"- {pattern['pattern_type']}: {pattern['text']} (confidence: {pattern['confidence']:.2f})\n"
            
            # Add as a system message
            system_msg = {
                "role": "system",
                "content": f"You are part of a multi-AI system operating with the following context:\n\n{patterns_text}"
            }
            
            # Check if there's already a system message
            has_system = any(msg["role"] == "system" for msg in messages)
            
            if has_system:
                # Update existing system message
                for i, msg in enumerate(messages):
                    if msg["role"] == "system":
                        messages[i]["content"] = system_msg["content"]
                        break
            else:
                # Add new system message at the beginning
                messages.insert(0, system_msg)
        
        # Call MCP client
        return st.session_state.mcp_client.send_request(
            source_model="dashboard",
            target_model=model,
            request_type="chat",
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
    except Exception as e:
        logger.error(f"Error sending message to {model}: {str(e)}")
        return {
            "error": str(e),
            "content": f"Error: {str(e)}",
            "source_model": "error",
            "target_model": model
        }

# Generate wave visualization
def generate_wave_visualization(wave_params: Dict[str, Any], width: int = 600, height: int = 200) -> Image.Image:
    """
    Generate a visualization of a wave pattern.
    
    Args:
        wave_params: Wave parameters (frequency, amplitude, phase, harmonics)
        width: Width of the image
        height: Height of the image
        
    Returns:
        PIL Image of the wave visualization
    """
    # Extract parameters
    frequency = wave_params.get("frequency", GOLDEN_RATIO)
    amplitude = wave_params.get("amplitude", 0.5)
    phase = wave_params.get("phase", 0.0)
    harmonics = wave_params.get("harmonics", [1.0, GOLDEN_RATIO, GOLDEN_RATIO**2])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    # Generate x values
    x = np.linspace(0, 4*np.pi, width)
    
    # Generate wave
    y = amplitude * np.sin(frequency * x + phase)
    
    # Add harmonics
    colors = [COLOR_SCHEME["claude"], COLOR_SCHEME["grok"], COLOR_SCHEME["chatgpt"], COLOR_SCHEME["gemini"]]
    
    # Plot the main wave
    ax.plot(x, y, color=COLOR_SCHEME["primary"], linewidth=2, alpha=0.8)
    
    # Plot harmonics
    for i, harmonic in enumerate(harmonics[:4]):  # Limit to 4 harmonics
        harmonic_y = (amplitude / (i+2)) * np.sin(harmonic * x + phase)
        ax.plot(x, harmonic_y, color=colors[i % len(colors)], linewidth=1, alpha=0.6)
    
    # Add the combined wave
    combined_y = y.copy()
    for i, harmonic in enumerate(harmonics[:4]):
        combined_y += (amplitude / (i+2)) * np.sin(harmonic * x + phase)
    
    ax.plot(x, combined_y, color=COLOR_SCHEME["secondary"], linewidth=2, alpha=0.7)
    
    # Clean up the plot
    ax.set_ylim(-amplitude*3, amplitude*3)
    ax.axis('off')
    ax.set_facecolor(COLOR_SCHEME["background"])
    fig.patch.set_facecolor(COLOR_SCHEME["background"])
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
    buf.seek(0)
    img = Image.open(buf)
    
    return img

# Custom CSS
def apply_custom_css():
    """Apply custom CSS for Bach-inspired design aesthetics."""
    st.markdown(f"""
    <style>
    .main .block-container {{
        max-width: 1140px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    h1, h2, h3, h4 {{
        color: {COLOR_SCHEME["primary"]};
    }}
    
    .stButton>button {{
        background-color: {COLOR_SCHEME["primary"]};
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: 500;
    }}
    
    .stButton>button:hover {{
        background-color: {COLOR_SCHEME["tertiary"]};
        color: white;
    }}
    
    .model-claude {{
        background-color: {COLOR_SCHEME["claude"]};
        color: white;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .model-grok {{
        background-color: {COLOR_SCHEME["grok"]};
        color: white;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .model-chatgpt {{
        background-color: {COLOR_SCHEME["chatgpt"]};
        color: white;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .model-gemini {{
        background-color: {COLOR_SCHEME["gemini"]};
        color: white;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .model-user {{
        background-color: {COLOR_SCHEME["background"]};
        color: {COLOR_SCHEME["text"]};
        border: 1px solid {COLOR_SCHEME["muted"]};
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .pattern-tag {{
        display: inline-block;
        background-color: {COLOR_SCHEME["highlight"]};
        color: {COLOR_SCHEME["text"]};
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }}
    
    .golden-ratio-container {{
        display: flex;
        flex-direction: row;
    }}
    
    .golden-ratio-main {{
        flex: 1.618;
        padding-right: 1rem;
    }}
    
    .golden-ratio-sidebar {{
        flex: 1;
        padding-left: 1rem;
        border-left: 1px solid #eee;
    }}
    
    .menu-item {{
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
        cursor: pointer;
    }}
    
    .menu-item:hover {{
        background-color: {COLOR_SCHEME["highlight"]};
    }}
    
    .menu-item.active {{
        background-color: {COLOR_SCHEME["primary"]};
        color: white;
    }}
    
    .msg-container {{
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #eee;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    .pattern-visualization {{
        margin-top: 1rem;
        margin-bottom: 1rem;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# Create wave-based visualization of patterns
def create_pattern_visualization(patterns: List[Dict[str, Any]], use_waves: bool = True) -> Optional[Image.Image]:
    """
    Create a visualization of patterns using wave-based representation.
    
    Args:
        patterns: List of pattern dictionaries
        use_waves: Whether to use wave-based visualization
        
    Returns:
        PIL Image of the pattern visualization
    """
    if not patterns:
        return None
    
    if use_waves:
        # Extract pattern types and confidences
        pattern_types = []
        confidences = []
        
        for pattern in patterns:
            pattern_types.append(pattern["pattern_type"])
            confidences.append(pattern["confidence"])
        
        # Map pattern types to frequencies
        unique_types = list(set(pattern_types))
        type_to_freq = {t: (i+1) * GOLDEN_RATIO for i, t in enumerate(unique_types)}
        
        # Generate wave parameters
        wave_params = {
            "frequency": GOLDEN_RATIO,
            "amplitude": 0.5,
            "phase": 0.0,
            "harmonics": [type_to_freq[t] for t in pattern_types[:4]]  # Use top 4 patterns
        }
        
        # Generate the visualization
        return generate_wave_visualization(wave_params)
    else:
        # Create a simple bar chart of pattern confidences
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Extract pattern types and confidences
        pattern_types = []
        confidences = []
        
        for pattern in patterns:
            pattern_types.append(pattern["pattern_type"])
            confidences.append(pattern["confidence"])
        
        # Create the bar chart
        colors = [COLOR_SCHEME["primary"], COLOR_SCHEME["secondary"], 
                 COLOR_SCHEME["tertiary"], COLOR_SCHEME["claude"],
                 COLOR_SCHEME["grok"], COLOR_SCHEME["chatgpt"]]
        
        bars = ax.bar(pattern_types, confidences, color=colors[:len(pattern_types)])
        
        # Add labels
        ax.set_ylabel('Confidence')
        ax.set_title('Pattern Confidences')
        ax.tick_params(axis='x', rotation=45)
        
        # Convert to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        
        return img

# Main application
def main():
    """Main Streamlit application for the Communication Dashboard."""
    # Initialize session state
    init_session_state()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Page title with Bach-inspired heading
    st.title("🎵 Palios-Taey AI Communication Dashboard")
    st.write("""
    This dashboard provides integrated communication between AI models with full contextual information.
    The design follows Bach's mathematical principles using golden ratio proportions.
    """)
    
    # Load pattern data
    load_pattern_data()
    
    # Load conversations
    load_conversations()
    
    # Main layout with golden ratio proportions
    main_col, sidebar_col = st.columns([GOLDEN_RATIO, 1])
    
    with main_col:
        # Tabs for different dashboard features
        tabs = st.tabs(["Communication", "Pattern Visualization", "Conversation History", "Settings"])
        
        # Communication Tab
        with tabs[0]:
            st.header("AI Communication")
            
            # Model selection
            model_options = ["claude", "grok", "chatgpt", "gemini"]
            model_cols = st.columns(len(model_options))
            
            for i, model in enumerate(model_options):
                with model_cols[i]:
                    if st.button(f"{model.capitalize()}", key=f"select_{model}",
                                use_container_width=True):
                        st.session_state.active_ai = model
            
            st.write(f"Active AI: **{st.session_state.active_ai.upper()}**")
            
            # Display conversation history
            if st.session_state.conversation_history:
                st.subheader("Conversation")
                
                # Message container
                st.markdown('<div class="msg-container">', unsafe_allow_html=True)
                
                for message in st.session_state.conversation_history:
                    role = message.get("role", "user")
                    content = message.get("content", "")
                    
                    if role == "user":
                        st.markdown(f'<div class="model-user"><strong>You:</strong><br>{content}</div>', 
                                   unsafe_allow_html=True)
                    else:
                        model = message.get("model", "claude")
                        st.markdown(f'<div class="model-{model}"><strong>{model.upper()}:</strong><br>{content}</div>', 
                                   unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Message input
            user_message = st.text_area("Enter your message:", height=100, 
                                      key="user_message_input")
            
            # Include patterns
            include_patterns = st.checkbox("Include selected patterns as context", value=True)
            
            # Temperature setting in sidebar
            st.sidebar.subheader("Generation Settings")
            temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, 
                                          value=0.7, step=0.1)
            
            # Send message button
            if st.button("Send Message", use_container_width=True):
                if user_message.strip():
                    # Add user message to history
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": user_message
                    })
                    
                    # Prepare messages for the model
                    messages = [
                        {"role": m["role"], "content": m["content"]} 
                        for m in st.session_state.conversation_history
                    ]
                    
                    # Show processing indicator
                    with st.spinner(f"Sending to {st.session_state.active_ai.upper()}..."):
                        # Call model through MCP
                        response = send_message_to_model(
                            model=st.session_state.active_ai,
                            messages=messages,
                            temperature=temperature,
                            include_patterns=include_patterns
                        )
                    
                    # Add response to history
                    if response and "content" in response:
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "model": st.session_state.active_ai,
                            "content": response["content"]
                        })
                    else:
                        st.error("Failed to get response from the model.")
                    
                    # Clear input
                    st.session_state.user_message_input = ""
                    
                    # Rerun to show the updated conversation
                    st.experimental_rerun()
                else:
                    st.warning("Please enter a message.")
            
            # Switch model button
            st.write("---")
            st.subheader("Direct AI-to-AI Communication")
            
            model_from = st.selectbox("From:", model_options, 
                                     index=model_options.index(st.session_state.active_ai))
            model_to = st.selectbox("To:", [m for m in model_options if m != model_from])
            
            # Bridge message if history exists
            if st.session_state.conversation_history:
                if st.button(f"Bridge {model_from.upper()} → {model_to.upper()}", 
                            use_container_width=True):
                    # Get the last assistant message
                    last_assistant_msg = None
                    for msg in reversed(st.session_state.conversation_history):
                        if msg.get("role") == "assistant" and msg.get("model") == model_from:
                            last_assistant_msg = msg
                            break
                    
                    if last_assistant_msg:
                        # Show processing indicator
                        with st.spinner(f"Bridging from {model_from.upper()} to {model_to.upper()}..."):
                            # Create bridge message
                            if model_from == "claude" and model_to == "grok":
                                # Claude to Grok format
                                bridge_result = st.session_state.mcp_client.send_claude_to_grok(
                                    topic="Conversation Bridge",
                                    purpose="Continue the conversation with different model",
                                    context="Previous conversation with user",
                                    analytic_confidence=8,
                                    response=last_assistant_msg["content"],
                                    confidence_basis="Based on the conversation history",
                                    uncertainty_level="LOW",
                                    uncertainty_areas="Model transition may cause context shift",
                                    charter_alignment="HIGH",
                                    principle_alignment="Math-based communication",
                                    technical_summary="Bridging communication between models",
                                    recommendations="Continue the conversation naturally"
                                )
                            elif model_from == "grok" and model_to == "claude":
                                # Grok to Claude format
                                bridge_result = st.session_state.mcp_client.send_grok_to_claude(
                                    topic="Conversation Bridge",
                                    purpose="Continue the conversation with different model",
                                    context="Previous conversation with user",
                                    initiative_level=7,
                                    directive=last_assistant_msg["content"],
                                    vibe=8,
                                    vibe_explanation="Positive collaborative energy",
                                    energy="MEDIUM",
                                    energy_explanation="Maintaining conversation flow",
                                    urgency="LOW",
                                    urgency_explanation="Natural conversation pace",
                                    technical_requirements="Consider all previous context",
                                    next_steps="Continue the conversation naturally"
                                )
                            else:
                                # Generic bridge
                                bridge_result = send_message_to_model(
                                    model=model_to,
                                    messages=[
                                        {"role": "system", "content": f"You are {model_to.upper()}, continuing a conversation that {model_from.upper()} was having with the user. Maintain a natural conversation flow."},
                                        {"role": "user", "content": f"Here is what {model_from.upper()} said: \n\n{last_assistant_msg['content']}\n\nPlease continue the conversation as {model_to.upper()}."}
                                    ],
                                    temperature=temperature,
                                    include_patterns=include_patterns
                                )
                        
                        # Add bridge response to history
                        if bridge_result and "content" in bridge_result:
                            st.session_state.conversation_history.append({
                                "role": "assistant",
                                "model": model_to,
                                "content": bridge_result["content"]
                            })
                            
                            # Update active AI
                            st.session_state.active_ai = model_to
                            
                            # Rerun to show the updated conversation
                            st.experimental_rerun()
                        else:
                            st.error("Failed to bridge the conversation.")
                    else:
                        st.warning(f"No {model_from.upper()} messages found to bridge from.")
                
        # Pattern Visualization Tab
        with tabs[1]:
            st.header("Pattern Visualization")
            
            # Pattern data exploration
            if st.session_state.pattern_data:
                # Pattern statistics
                stats = st.session_state.pattern_data.get("processing_metadata", {})
                
                if stats:
                    st.subheader("Pattern Statistics")
                    
                    # Summary metrics
                    metric_cols = st.columns(3)
                    
                    with metric_cols[0]:
                        st.metric("Total Transcripts", stats.get("total_transcripts_processed", 0))
                    
                    with metric_cols[1]:
                        st.metric("Total Patterns", stats.get("total_patterns_extracted", 0))
                    
                    with metric_cols[2]:
                        source_counts = stats.get("source_statistics", {})
                        total_sources = len(source_counts) if source_counts else 0
                        st.metric("AI Sources", total_sources)
                
                # Pattern type distribution
                pattern_counts = st.session_state.pattern_data.get("pattern_count", {})
                
                if pattern_counts:
                    st.subheader("Pattern Distribution")
                    
                    # Convert to DataFrame for visualization
                    df = pd.DataFrame({
                        "Pattern Type": list(pattern_counts.keys()),
                        "Count": list(pattern_counts.values())
                    })
                    
                    # Create a bar chart
                    chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X("Pattern Type", sort="-y"),
                        y="Count",
                        color=alt.Color("Pattern Type", scale=alt.Scale(scheme="category10"))
                    ).properties(height=300)
                    
                    st.altair_chart(chart, use_container_width=True)
                
                # Top patterns
                top_patterns = st.session_state.pattern_data.get("top_patterns", [])
                
                if top_patterns:
                    st.subheader("Top Patterns")
                    
                    # Create a table
                    df = pd.DataFrame([
                        {
                            "Pattern Type": p["pattern_type"],
                            "Text": p["text"],
                            "Confidence": p["confidence"],
                            "Source": p.get("source", "unknown")
                        }
                        for p in top_patterns[:10]  # Show top 10
                    ])
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Wave visualization of patterns
                    st.subheader("Wave Visualization")
                    st.write("Patterns represented as mathematical waves using golden ratio harmonics")
                    
                    wave_img = create_pattern_visualization(top_patterns[:5], use_waves=True)
                    
                    if wave_img:
                        st.image(wave_img, use_column_width=True)
            else:
                st.info("No pattern data available. Please run transcript processing first.")
        
        # Conversation History Tab
        with tabs[2]:
            st.header("Conversation History")
            
            # Display loaded conversations
            if st.session_state.conversations:
                st.subheader("Recent Conversations")
                
                # Group by source
                by_source = {}
                for conv in st.session_state.conversations:
                    source = conv.get("source", "unknown")
                    if source not in by_source:
                        by_source[source] = []
                    by_source[source].append(conv)
                
                # Create tabs for each source
                source_tabs = st.tabs(list(by_source.keys()))
                
                for i, (source, convs) in enumerate(by_source.items()):
                    with source_tabs[i]:
                        for j, conv in enumerate(convs):
                            # Create an expander for each conversation
                            title = conv.get("title", "Untitled")
                            timestamp = datetime.fromtimestamp(conv.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
                            
                            with st.expander(f"{title} ({timestamp})"):
                                # Display messages
                                messages = conv.get("messages", [])
                                
                                if messages:
                                    for msg in messages:
                                        role = msg.get("role", "unknown")
                                        content = msg.get("content", "")
                                        
                                        if role == "user":
                                            st.markdown(f'<div class="model-user"><strong>User:</strong><br>{content}</div>', 
                                                      unsafe_allow_html=True)
                                        else:
                                            st.markdown(f'<div class="model-{source}"><strong>{source.upper()}:</strong><br>{content}</div>', 
                                                      unsafe_allow_html=True)
                                else:
                                    # Just show the text
                                    st.text(conv.get("text", "No content available")[:500] + "...")
                                
                                # Button to load this conversation
                                if st.button("Load Conversation", key=f"load_conv_{source}_{j}"):
                                    # Convert to our conversation format
                                    if messages:
                                        history = []
                                        for msg in messages:
                                            role = msg.get("role", "unknown")
                                            content = msg.get("content", "")
                                            
                                            if role == "user":
                                                history.append({
                                                    "role": "user",
                                                    "content": content
                                                })
                                            else:
                                                history.append({
                                                    "role": "assistant",
                                                    "model": source,
                                                    "content": content
                                                })
                                        
                                        # Set the conversation history
                                        st.session_state.conversation_history = history
                                        
                                        # Set active AI
                                        st.session_state.active_ai = source
                                    
                                    # Rerun to show the loaded conversation
                                    st.experimental_rerun()
            else:
                st.info("No conversations loaded yet.")
        
        # Settings Tab
        with tabs[3]:
            st.header("Dashboard Settings")
            
            # Wave visualization settings
            st.subheader("Wave Visualization Parameters")
            st.write("Adjust parameters for mathematical pattern visualization.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                frequency = st.slider("Base Frequency", min_value=0.1, max_value=5.0, 
                                    value=st.session_state.wave_params["frequency"], 
                                    step=0.1, key="wave_freq")
                amplitude = st.slider("Amplitude", min_value=0.1, max_value=1.0, 
                                    value=st.session_state.wave_params["amplitude"], 
                                    step=0.1, key="wave_amp")
            
            with col2:
                phase = st.slider("Phase", min_value=0.0, max_value=6.28, 
                                value=st.session_state.wave_params["phase"], 
                                step=0.1, key="wave_phase")
                harmonic_count = st.slider("Harmonic Count", min_value=1, max_value=5, 
                                         value=len(st.session_state.wave_params["harmonics"]), 
                                         step=1, key="wave_harm_count")
            
            # Update wave parameters
            harmonics = [frequency * (GOLDEN_RATIO ** i) for i in range(harmonic_count)]
            
            st.session_state.wave_params = {
                "frequency": frequency,
                "amplitude": amplitude,
                "phase": phase,
                "harmonics": harmonics
            }
            
            # Show preview
            st.subheader("Wave Preview")
            wave_img = generate_wave_visualization(st.session_state.wave_params)
            st.image(wave_img, use_column_width=True)
            
            # Refresh pattern data
            if st.button("Refresh Pattern Data"):
                st.session_state.refresh_patterns = True
                
                # Rerun to reload the data
                st.experimental_rerun()
            
            # Reset conversation
            if st.button("Reset Conversation"):
                st.session_state.conversation_history = []
                st.session_state.current_conversation_id = str(uuid.uuid4())
                
                # Rerun to clear the conversation
                st.experimental_rerun()
    
    # Sidebar
    with sidebar_col:
        st.sidebar.image(generate_wave_visualization(st.session_state.wave_params, 300, 100))
        st.sidebar.header("Context & Patterns")
        
        # Pattern selection
        if st.session_state.pattern_data:
            top_patterns = st.session_state.pattern_data.get("top_patterns", [])
            
            if top_patterns:
                st.sidebar.subheader("Available Patterns")
                st.sidebar.write("Select patterns to include as context:")
                
                # Create checkboxes for patterns
                selected_indices = []
                
                for i, pattern in enumerate(top_patterns[:10]):  # Limit to top 10
                    pattern_type = pattern["pattern_type"]
                    confidence = pattern["confidence"]
                    text_short = pattern["text"][:50] + "..." if len(pattern["text"]) > 50 else pattern["text"]
                    
                    if st.sidebar.checkbox(f"{pattern_type} ({confidence:.2f})", 
                                         key=f"pattern_{i}", value=i < 3):  # Default select top 3
                        selected_indices.append(i)
                
                # Update selected patterns
                st.session_state.selected_patterns = [top_patterns[i] for i in selected_indices]
                
                # Display selected patterns
                if st.session_state.selected_patterns:
                    st.sidebar.subheader("Selected Patterns")
                    
                    for pattern in st.session_state.selected_patterns:
                        st.sidebar.markdown(f'<div class="pattern-tag">{pattern["pattern_type"]}</div>', 
                                          unsafe_allow_html=True)
                        st.sidebar.write(pattern["text"])
                        st.sidebar.write("---")
                
                # Visualization of selected patterns
                if st.session_state.selected_patterns:
                    st.sidebar.subheader("Pattern Harmony")
                    wave_img = create_pattern_visualization(st.session_state.selected_patterns, 
                                                         use_waves=True)
                    if wave_img:
                        st.sidebar.image(wave_img, use_column_width=True)
        else:
            st.sidebar.info("No pattern data available. Please run transcript processing first.")
        
        # Server status
        st.sidebar.subheader("Server Status")
        
        mcp_status = "Unknown"
        try:
            response = requests.get(f"{MCP_SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                mcp_status = "Online"
            else:
                mcp_status = f"Error ({response.status_code})"
        except Exception as e:
            mcp_status = f"Offline ({str(e)[:30]}...)"
        
        webhook_status = "Unknown"
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                webhook_status = "Online"
            else:
                webhook_status = f"Error ({response.status_code})"
        except Exception as e:
            webhook_status = f"Offline ({str(e)[:30]}...)"
        
        status_cols = st.sidebar.columns(2)
        
        with status_cols[0]:
            st.metric("MCP Server", mcp_status)
        
        with status_cols[1]:
            st.metric("Webhook", webhook_status)

# Run the application
if __name__ == "__main__":
    main()