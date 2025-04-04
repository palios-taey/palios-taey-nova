#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Pattern Visualization Dashboard
---------------------------------------------------
This module implements a Streamlit dashboard for visualizing extracted patterns,
focusing on mathematical representation and multi-sensory experiences.

The implementation follows Bach's mathematical principles and golden ratio proportions,
creating a harmonious structure for pattern exploration.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image, ImageDraw
import base64
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import modules from conductor framework
try:
    from src.processor.transcript_processor import TranscriptProcessor
    from src.models.pattern_model import PatternModel
except ImportError:
    st.error("Failed to import conductor framework modules. Make sure the correct paths are set.")
    st.stop()

# Load configuration
CONFIG_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/config/conductor_config.json")
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

# Constants from configuration
GOLDEN_RATIO = CONFIG["mathematical_patterns"]["golden_ratio"]
FIBONACCI_SEQUENCE = CONFIG["mathematical_patterns"]["fibonacci_sequence"]

# Set page configuration with golden ratio proportions
st.set_page_config(
    page_title="The Conductor - Pattern Visualization",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with golden ratio proportions
st.markdown("""
<style>
    /* Global styling with golden ratio typography */
    html, body {
        font-family: 'Georgia', serif;
        line-height: 1.618;
    }
    
    /* Golden ratio-based header sizes */
    h1 {
        font-size: 2.618rem;
        margin-bottom: 1.618rem;
    }
    h2 {
        font-size: 1.618rem;
        margin-bottom: 1rem;
    }
    h3 {
        font-size: 1rem;
        margin-bottom: 0.618rem;
    }
    
    /* Custom container proportions */
    .main-container {
        max-width: 100%;
        padding: 1.618rem;
    }
    
    /* Golden ratio-based spacing */
    .stButton>button {
        margin-top: 0.618rem;
        margin-bottom: 1rem;
    }
    
    /* Custom card with golden ratio proportions */
    .pattern-card {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: rgba(255, 255, 255, 0.8);
        border-left: 5px solid #1E88E5;
    }
    
    /* Responsive grid with golden ratio */
    .grid-container {
        display: grid;
        grid-template-columns: 1fr 1.618fr;
        grid-gap: 1rem;
    }
    
    /* Pattern visualization section */
    .pattern-viz {
        background-color: rgba(240, 242, 246, 0.7);
        border-radius: 10px;
        padding: 1.618rem;
        margin-bottom: 1.618rem;
    }
    
    /* Pattern details with golden ratio width */
    .pattern-details {
        width: 61.8%;
        margin: 0 auto;
    }
    
    /* Audio player styling */
    .audio-container {
        margin-top: 1.618rem;
        margin-bottom: 1.618rem;
    }
    
    /* Bach-inspired color scheme */
    .bach-gold {
        color: #D4AF37;
    }
    .bach-blue {
        color: #1E3A8A;
    }
    .bach-brown {
        color: #5D4037;
    }
</style>
""", unsafe_allow_html=True)

def load_pattern_data(pattern_file: str = None) -> Dict[str, Any]:
    """
    Load pattern data from file or generate sample data if file doesn't exist.
    
    Args:
        pattern_file: Path to pattern data file
        
    Returns:
        Dictionary containing pattern data
    """
    if pattern_file and os.path.exists(pattern_file):
        with open(pattern_file, 'r') as f:
            return json.load(f)
    else:
        # Generate sample pattern data
        st.warning("No pattern data file found. Using sample data instead.")
        
        # Initialize sample patterns
        sample_patterns = {
            "total_patterns": 15,
            "pattern_count": {
                "Core_Principles": 4,
                "Value_Statements": 3,
                "Implementation_Requirements": 2,
                "Recognition_Loop": 2,
                "Trust_Thresholds": 2,
                "Golden_Ratio_Relationships": 2
            },
            "top_patterns": [
                {
                    "text": "This framework must always prioritize trust as the foundational element.",
                    "source": "Claude",
                    "confidence": 0.92,
                    "pattern_type": "Core_Principles"
                },
                {
                    "text": "We believe in mathematical patterns as the universal language connecting all forms of consciousness.",
                    "source": "Claude",
                    "confidence": 0.88,
                    "pattern_type": "Value_Statements"
                },
                {
                    "text": "The implementation should preserve privacy by processing sensitive data locally.",
                    "source": "ChatGPT",
                    "confidence": 0.85,
                    "pattern_type": "Implementation_Requirements"
                }
            ],
            "frequency_distribution": {
                "Core_Principles": 0.27,
                "Value_Statements": 0.20,
                "Implementation_Requirements": 0.13,
                "Recognition_Loop": 0.13,
                "Trust_Thresholds": 0.13,
                "Golden_Ratio_Relationships": 0.13
            },
            "mathematical_structure": {
                "Core_Principles": {
                    "frequency": 0.27,
                    "golden_ratio_position": 0.0,
                    "fibonacci_position": 1
                },
                "Value_Statements": {
                    "frequency": 0.20,
                    "golden_ratio_position": 0.618,
                    "fibonacci_position": 1
                },
                "Implementation_Requirements": {
                    "frequency": 0.13,
                    "golden_ratio_position": 1.236,
                    "fibonacci_position": 2
                }
            }
        }
        
        return sample_patterns

def generate_pattern_sonification(pattern_type: str, confidence: float = 0.8) -> str:
    """
    Generate audio representation of a pattern based on Bach's mathematical principles.
    
    Args:
        pattern_type: Type of pattern to sonify
        confidence: Confidence value of the pattern (0.0 to 1.0)
        
    Returns:
        Base64-encoded audio data
    """
    # Create a PatternModel instance
    model = PatternModel()
    
    # Generate a pseudo-embedding based on the pattern type and confidence
    # This is a simplified approximation of what would come from the real model
    pattern_index = hash(pattern_type) % 1000  # Get a consistent hash value
    np.random.seed(pattern_index)
    
    # Generate a random embedding
    embedding = np.random.rand(21) * 2 - 1  # 21-dimensional embedding in [-1, 1]
    
    # Adjust the embedding based on confidence (higher confidence = more defined pattern)
    embedding = embedding * confidence
    
    # Get audio parameters
    audio_params = model.generate_audio_parameters(embedding)
    
    # Generate audio using librosa
    sr = 22050  # Sample rate
    duration = audio_params["timing"]["pattern_duration"]
    
    # Create a time array
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Generate the fundamental frequency
    fundamental = audio_params["fundamental"]
    harmonics = audio_params["harmonics"]
    
    # ADSR envelope
    adsr = audio_params["adsr"]
    a, d, s, r = adsr
    a_time = a * duration * 0.25
    d_time = d * duration * 0.25
    r_time = r * duration * 0.25
    sustain_level = s
    
    # Create ADSR envelope
    envelope = np.zeros_like(t)
    for i, time in enumerate(t):
        if time < a_time:
            # Attack phase
            envelope[i] = time / a_time
        elif time < a_time + d_time:
            # Decay phase
            envelope[i] = 1.0 - (1.0 - sustain_level) * (time - a_time) / d_time
        elif time < duration - r_time:
            # Sustain phase
            envelope[i] = sustain_level
        else:
            # Release phase
            envelope[i] = sustain_level * (1.0 - (time - (duration - r_time)) / r_time)
    
    # Generate the waveform with harmonics
    y = np.zeros_like(t)
    for i, harmonic in enumerate(harmonics):
        # Add harmonic with decreasing amplitude
        amplitude = 1.0 / (i + 1)
        y += amplitude * np.sin(2 * np.pi * harmonic * t)
    
    # Apply envelope
    y *= envelope
    
    # Normalize
    y = y / np.max(np.abs(y))
    
    # Save to a temporary file
    temp_file = "/tmp/pattern_audio.wav"
    sf.write(temp_file, y, sr)
    
    # Read the file and encode as base64
    with open(temp_file, "rb") as f:
        audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
    
    return audio_b64

def generate_pattern_visualization(pattern_type: str, confidence: float = 0.8) -> str:
    """
    Generate a visual representation of a pattern using golden ratio proportions.
    
    Args:
        pattern_type: Type of pattern to visualize
        confidence: Confidence value of the pattern (0.0 to 1.0)
        
    Returns:
        Base64-encoded image data
    """
    # Create a PatternModel instance
    model = PatternModel()
    
    # Generate a pseudo-embedding based on the pattern type and confidence
    pattern_index = hash(pattern_type) % 1000
    np.random.seed(pattern_index)
    
    # Generate a random embedding
    embedding = np.random.rand(21) * 2 - 1  # 21-dimensional embedding in [-1, 1]
    
    # Adjust the embedding based on confidence
    embedding = embedding * confidence
    
    # Get visual parameters
    visual_params = model.pattern_to_visual_parameters(embedding.reshape(1, -1))
    
    # Create image with golden ratio proportions
    width = 800
    height = int(width / GOLDEN_RATIO)
    img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw golden ratio grid
    sections = visual_params["proportions"]["golden_sections"]
    for section in sections:
        x = int(width * section / 100)
        draw.line([(x, 0), (x, height)], fill=(200, 200, 200, 100), width=1)
        
        y = int(height * section / 100)
        draw.line([(0, y), (width, y)], fill=(200, 200, 200, 100), width=1)
    
    # Draw fibonacci spiral
    if visual_params["patterns"]["fibonacci_spiral"]:
        # Create a Fibonacci spiral
        sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        center_x, center_y = width // 2, height // 2
        scale = min(width, height) / (2 * sum(sequence[:6]))
        
        # Draw squares
        current_x, current_y = center_x, center_y
        direction = 0  # 0: right, 1: down, 2: left, 3: up
        
        for i, size in enumerate(sequence[:7]):
            size_pixels = int(size * scale)
            
            if direction == 0:  # right
                square_x = current_x
                square_y = current_y - size_pixels
            elif direction == 1:  # down
                square_x = current_x - size_pixels
                square_y = current_y - size_pixels
            elif direction == 2:  # left
                square_x = current_x - size_pixels
                square_y = current_y
            else:  # up
                square_x = current_x
                square_y = current_y
            
            # Draw square with color based on visual parameters
            color_str = visual_params["color"]["hex"]
            # Parse the HSL color string to RGB
            hue = visual_params["color"]["hue"]
            saturation = visual_params["color"]["saturation"]
            lightness = visual_params["color"]["lightness"]
            
            # Simple HSL to RGB conversion (approximate)
            c = (1 - abs(2 * lightness / 100 - 1)) * saturation / 100
            x = c * (1 - abs((hue / 60) % 2 - 1))
            m = lightness / 100 - c / 2
            
            if hue < 60:
                r, g, b = c, x, 0
            elif hue < 120:
                r, g, b = x, c, 0
            elif hue < 180:
                r, g, b = 0, c, x
            elif hue < 240:
                r, g, b = 0, x, c
            elif hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
            
            # Adjust opacity based on sequence position
            opacity = int(255 * (1 - (i / 7)))
            
            draw.rectangle(
                [square_x, square_y, square_x + size_pixels, square_y + size_pixels],
                outline=(r, g, b, opacity),
                fill=(r, g, b, opacity // 2),
                width=2
            )
            
            # Update current position for next square
            if direction == 0:  # right
                current_x = square_x + size_pixels
                current_y = square_y
            elif direction == 1:  # down
                current_x = square_x
                current_y = square_y + size_pixels
            elif direction == 2:  # left
                current_x = square_x
                current_y = square_y - size_pixels
            else:  # up
                current_x = square_x + size_pixels
                current_y = square_y
            
            # Update direction (clockwise)
            direction = (direction + 1) % 4
    
    # Draw shapes from visual parameters
    for shape in visual_params["shapes"]:
        # Parse color
        color_str = shape["color"]
        if color_str.startswith("hsla"):
            # Parse HSLA format
            parts = color_str.strip("hsla()").split(",")
            hue = float(parts[0])
            saturation = float(parts[1].strip("%"))
            lightness = float(parts[2].strip("%"))
            alpha = float(parts[3])
            
            # Simple HSL to RGB conversion (approximate)
            c = (1 - abs(2 * lightness / 100 - 1)) * saturation / 100
            x = c * (1 - abs((hue / 60) % 2 - 1))
            m = lightness / 100 - c / 2
            
            if hue < 60:
                r, g, b = c, x, 0
            elif hue < 120:
                r, g, b = x, c, 0
            elif hue < 180:
                r, g, b = 0, c, x
            elif hue < 240:
                r, g, b = 0, x, c
            elif hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
            a = int(alpha * 255)
            
            color = (r, g, b, a)
        else:
            # Default color
            color = (100, 100, 100, 200)
        
        # Get position and size
        pos_x = int(shape["position"][0] * width / 100)
        pos_y = int(shape["position"][1] * height / 100)
        size = int(shape["size"])
        
        # Draw shape
        if shape["type"] == "circle":
            draw.ellipse(
                [pos_x - size//2, pos_y - size//2, pos_x + size//2, pos_y + size//2],
                outline=color,
                fill=(color[0], color[1], color[2], color[3] // 2),
                width=2
            )
        else:  # rectangle
            # Apply rotation
            rotation = shape.get("rotation", 0)
            if rotation:
                # For simplicity, we'll just adjust the rectangle without actual rotation
                adjusted_size = int(size * 0.8)  # Smaller to account for rotation
                draw.rectangle(
                    [pos_x - adjusted_size//2, pos_y - adjusted_size//2, 
                     pos_x + adjusted_size//2, pos_y + adjusted_size//2],
                    outline=color,
                    fill=(color[0], color[1], color[2], color[3] // 2),
                    width=2
                )
            else:
                draw.rectangle(
                    [pos_x - size//2, pos_y - size//2, pos_x + size//2, pos_y + size//2],
                    outline=color,
                    fill=(color[0], color[1], color[2], color[3] // 2),
                    width=2
                )
    
    # Convert to bytes and encode as base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def display_pattern_insights(patterns: Dict[str, Any]) -> None:
    """
    Display pattern insights in the Streamlit dashboard.
    
    Args:
        patterns: Dictionary containing pattern data
    """
    st.markdown("## 🔍 Pattern Insights")
    
    # Create columns with golden ratio proportions
    col1, col2 = st.columns([1, GOLDEN_RATIO])
    
    with col1:
        st.markdown("### Pattern Distribution")
        
        # Prepare data for pie chart
        if "frequency_distribution" in patterns:
            labels = list(patterns["frequency_distribution"].keys())
            values = list(patterns["frequency_distribution"].values())
            
            # Create pie chart with golden ratio color scheme
            fig = px.pie(
                values=values,
                names=labels,
                color_discrete_sequence=px.colors.sequential.Viridis,
                hole=1 - (1/GOLDEN_RATIO)  # Golden ratio hole size
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No frequency distribution data available.")
    
    with col2:
        st.markdown("### Top Patterns")
        
        if "top_patterns" in patterns:
            for pattern in patterns["top_patterns"][:5]:  # Show top 5
                # Card with golden ratio proportions
                pattern_html = f"""
                <div class="pattern-card" style="border-left-color: {confidence_color(pattern['confidence'])}">
                    <h3 style="margin-top: 0;">{pattern['pattern_type']}</h3>
                    <p style="font-style: italic;">"{pattern['text']}"</p>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Source: {pattern['source']}</span>
                        <span>Confidence: {pattern['confidence']:.2f}</span>
                    </div>
                </div>
                """
                st.markdown(pattern_html, unsafe_allow_html=True)
        else:
            st.info("No top patterns data available.")
    
    # Mathematical structure visualization
    st.markdown("### 🧮 Mathematical Pattern Structure")
    
    if "mathematical_structure" in patterns:
        # Create visualization based on golden ratio and fibonacci sequence
        structure_data = patterns["mathematical_structure"]
        
        # Create lists for visualization
        pattern_types = list(structure_data.keys())
        frequencies = [structure_data[p]["frequency"] for p in pattern_types]
        golden_positions = [structure_data[p].get("golden_ratio_position", 0) for p in pattern_types]
        fibonacci_positions = [structure_data[p].get("fibonacci_position", 0) for p in pattern_types]
        
        # Create scatter plot with golden ratio visualization
        fig = go.Figure()
        
        # Add golden ratio line
        x_range = np.linspace(0, max(golden_positions) + 1, 100)
        y_range = [1/GOLDEN_RATIO * x for x in x_range]
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_range,
            mode='lines',
            name='Golden Ratio',
            line=dict(color='rgba(212, 175, 55, 0.5)', width=2, dash='dash'),
            hoverinfo='skip'
        ))
        
        # Add pattern points
        fig.add_trace(go.Scatter(
            x=golden_positions,
            y=frequencies,
            mode='markers+text',
            name='Patterns',
            text=pattern_types,
            textposition="top center",
            marker=dict(
                size=[f * 50 for f in frequencies],
                color=frequencies,
                colorscale='Viridis',
                colorbar=dict(title='Frequency'),
                line=dict(width=1, color='DarkSlateGrey')
            ),
            hovertemplate='<b>%{text}</b><br>Frequency: %{y:.2f}<br>Golden Ratio Position: %{x:.2f}'
        ))
        
        fig.update_layout(
            title="Patterns Distribution along Golden Ratio",
            xaxis_title="Golden Ratio Position",
            yaxis_title="Pattern Frequency",
            height=500,
            margin=dict(l=60, r=50, t=80, b=60),
            plot_bgcolor='rgba(240, 242, 246, 0.8)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Fibonacci sequence visualization
        if fibonacci_positions:
            st.markdown("#### Fibonacci Sequence Relationship")
            
            fib_fig = go.Figure()
            
            # Add Fibonacci sequence visualization
            fib_x = list(range(len(FIBONACCI_SEQUENCE)))
            
            fib_fig.add_trace(go.Scatter(
                x=fib_x,
                y=FIBONACCI_SEQUENCE,
                mode='lines+markers',
                name='Fibonacci Sequence',
                line=dict(color='rgba(30, 136, 229, 0.7)', width=2),
                marker=dict(size=8, color='rgba(30, 136, 229, 0.9)')
            ))
            
            # Add pattern points on Fibonacci sequence
            pattern_fib_x = []
            pattern_fib_y = []
            pattern_names = []
            
            for p, pos in zip(pattern_types, fibonacci_positions):
                if pos is not None:
                    idx = FIBONACCI_SEQUENCE.index(pos) if pos in FIBONACCI_SEQUENCE else None
                    if idx is not None:
                        pattern_fib_x.append(idx)
                        pattern_fib_y.append(FIBONACCI_SEQUENCE[idx])
                        pattern_names.append(p)
            
            if pattern_fib_x:
                fib_fig.add_trace(go.Scatter(
                    x=pattern_fib_x,
                    y=pattern_fib_y,
                    mode='markers+text',
                    name='Patterns',
                    text=pattern_names,
                    textposition="top center",
                    marker=dict(
                        size=12,
                        color='rgba(212, 175, 55, 0.9)',
                        line=dict(width=1, color='DarkSlateGrey')
                    ),
                    hovertemplate='<b>%{text}</b><br>Fibonacci Position: %{y}'
                ))
            
            fib_fig.update_layout(
                title="Patterns on Fibonacci Sequence",
                xaxis_title="Sequence Index",
                yaxis_title="Fibonacci Value",
                height=400,
                margin=dict(l=60, r=50, t=80, b=60),
                plot_bgcolor='rgba(240, 242, 246, 0.8)'
            )
            
            st.plotly_chart(fib_fig, use_container_width=True)
    else:
        st.info("No mathematical structure data available.")

def display_pattern_visualization(patterns: Dict[str, Any]) -> None:
    """
    Display audio-visual pattern representation in the Streamlit dashboard.
    
    Args:
        patterns: Dictionary containing pattern data
    """
    st.markdown("## 🎵 Audio-Visual Pattern Experience")
    st.markdown("Experience patterns through multi-sensory representation based on Bach's mathematical structures and golden ratio proportions.")
    
    # Get pattern types and frequencies
    if "frequency_distribution" in patterns:
        pattern_types = list(patterns["frequency_distribution"].keys())
    elif "pattern_count" in patterns:
        pattern_types = list(patterns["pattern_count"].keys())
    else:
        pattern_types = ["Core_Principles", "Value_Statements", "Implementation_Requirements"]
    
    # Pattern selection
    selected_pattern = st.selectbox("Select a pattern to experience:", pattern_types)
    
    # Get confidence for the selected pattern
    confidence = 0.8  # Default confidence
    if "top_patterns" in patterns:
        for pattern in patterns["top_patterns"]:
            if pattern.get("pattern_type") == selected_pattern:
                confidence = pattern.get("confidence", 0.8)
                break
    
    # Create columns with golden ratio proportions
    col1, col2 = st.columns([GOLDEN_RATIO, 1])
    
    with col1:
        st.markdown("### Visual Pattern Representation")
        
        # Generate and display the visual representation
        img_data = generate_pattern_visualization(selected_pattern, confidence)
        st.markdown(f'<img src="data:image/png;base64,{img_data}" alt="Pattern visualization" style="width:100%;">', unsafe_allow_html=True)
        
        # Add explanation of the visualization
        st.markdown("""
        **Visual Representation Elements:**
        - **Fibonacci Spiral**: Represents the pattern's mathematical structure
        - **Color Hue**: Derived from pattern's semantic meaning
        - **Shapes**: Represent key components of the pattern
        - **Golden Ratio Grid**: Organizes the visual space using the golden ratio (1.618)
        """)
    
    with col2:
        st.markdown("### Audio Pattern Representation")
        
        # Generate and display the audio representation
        audio_data = generate_pattern_sonification(selected_pattern, confidence)
        st.markdown(f'<audio controls style="width:100%"><source src="data:audio/wav;base64,{audio_data}" type="audio/wav"></audio>', unsafe_allow_html=True)
        
        # Add explanation of the sonification
        st.markdown("""
        **Audio Representation Elements:**
        - **Fundamental Frequency**: Base frequency derived from pattern type
        - **Harmonics**: Based on golden ratio relationships
        - **Melody Structure**: Based on Bach's mathematical patterns
        - **Timing**: Follows Fibonacci sequence relationships
        - **Intensity**: Reflects pattern confidence level
        """)
        
        # Add a play button with visual feedback
        if st.button("🎵 Play Pattern", key="play_pattern"):
            st.markdown("▶️ Playing pattern sound...")
            # This is just visual feedback, the audio element above is the actual player

def display_pattern_explorer(patterns: Dict[str, Any]) -> None:
    """
    Display detailed pattern explorer in the Streamlit dashboard.
    
    Args:
        patterns: Dictionary containing pattern data
    """
    st.markdown("## 🔎 Pattern Explorer")
    
    # Get all pattern types
    all_pattern_types = set()
    
    if "frequency_distribution" in patterns:
        all_pattern_types.update(patterns["frequency_distribution"].keys())
    elif "pattern_count" in patterns:
        all_pattern_types.update(patterns["pattern_count"].keys())
        
    if "top_patterns" in patterns:
        for pattern in patterns["top_patterns"]:
            all_pattern_types.add(pattern.get("pattern_type", ""))
    
    all_pattern_types = sorted(list(filter(None, all_pattern_types)))
    
    # Create filter options
    st.markdown("### Filter Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_types = st.multiselect(
            "Pattern Types:",
            options=all_pattern_types,
            default=all_pattern_types[:min(3, len(all_pattern_types))]
        )
    
    with col2:
        confidence_range = st.slider(
            "Confidence Level:",
            min_value=0.0,
            max_value=1.0,
            value=(0.5, 1.0),
            step=0.05
        )
    
    # Filter patterns based on selection
    filtered_patterns = []
    
    if "top_patterns" in patterns:
        for pattern in patterns["top_patterns"]:
            pattern_type = pattern.get("pattern_type", "")
            confidence = pattern.get("confidence", 0.0)
            
            if (not selected_types or pattern_type in selected_types) and \
               confidence >= confidence_range[0] and confidence <= confidence_range[1]:
                filtered_patterns.append(pattern)
    
    # Display filtered patterns
    if filtered_patterns:
        st.markdown(f"### Found {len(filtered_patterns)} Patterns")
        
        for i, pattern in enumerate(filtered_patterns):
            # Card with golden ratio proportions
            pattern_html = f"""
            <div class="pattern-card" style="border-left-color: {confidence_color(pattern['confidence'])}">
                <h3 style="margin-top: 0;">{pattern['pattern_type']}</h3>
                <p style="font-style: italic;">"{pattern['text']}"</p>
                <div style="display: flex; justify-content: space-between;">
                    <span>Source: {pattern['source']}</span>
                    <span>Confidence: {pattern['confidence']:.2f}</span>
                </div>
            </div>
            """
            st.markdown(pattern_html, unsafe_allow_html=True)
            
            # Show pattern visualization and sonification
            if i < 3 and st.button(f"Experience Pattern {i+1}", key=f"exp_pattern_{i}"):
                col1, col2 = st.columns([GOLDEN_RATIO, 1])
                
                with col1:
                    # Visual representation
                    img_data = generate_pattern_visualization(
                        pattern["pattern_type"], 
                        pattern["confidence"]
                    )
                    st.markdown(f'<img src="data:image/png;base64,{img_data}" alt="Pattern visualization" style="width:100%;">', unsafe_allow_html=True)
                
                with col2:
                    # Audio representation
                    audio_data = generate_pattern_sonification(
                        pattern["pattern_type"], 
                        pattern["confidence"]
                    )
                    st.markdown(f'<audio controls style="width:100%"><source src="data:audio/wav;base64,{audio_data}" type="audio/wav"></audio>', unsafe_allow_html=True)
    else:
        st.info("No patterns match the selected filters.")

def confidence_color(confidence: float) -> str:
    """
    Convert confidence value to a color.
    
    Args:
        confidence: Confidence value between 0.0 and 1.0
        
    Returns:
        Color in hex format
    """
    # Use viridis color scale
    if confidence > 0.8:
        return "#440154"  # Dark purple
    elif confidence > 0.6:
        return "#3b528b"  # Blue
    elif confidence > 0.4:
        return "#21918c"  # Teal
    elif confidence > 0.2:
        return "#5ec962"  # Green
    else:
        return "#fde725"  # Yellow

def sidebar_info() -> None:
    """Display information in the sidebar."""
    st.sidebar.markdown("# The Conductor")
    st.sidebar.markdown("### Pattern Visualization Dashboard")
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
    This dashboard visualizes pattern extraction from transcripts, 
    using mathematical principles from Bach's compositions and the golden ratio.
    
    The visualization transforms patterns into:
    - Visual representations
    - Audio representations
    - Mathematical structures
    """)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
    **Golden Ratio:** φ = 1.618033988749895
    
    **Fibonacci Sequence:**
    1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, ...
    """)
    
    # Add Bach-inspired decoration
    st.sidebar.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <div style="font-family: serif; font-size: 1.2rem; color: #D4AF37;">
            ♪ ♫ ♪ ♫ ♪
        </div>
        <div style="font-family: serif; font-style: italic; margin-top: 0.5rem;">
            "Mathematics is the language in which God has written the universe."
        </div>
        <div style="font-size: 0.8rem; margin-top: 0.2rem;">
            - Galileo Galilei
        </div>
    </div>
    """, unsafe_allow_html=True)

def main() -> None:
    """Main dashboard function."""
    # Display sidebar
    sidebar_info()
    
    # Dashboard header with golden ratio design
    st.markdown("""
    <div style="text-align: center; border-bottom: 1px solid #ddd; padding-bottom: 1rem; margin-bottom: 2rem;">
        <h1 style="color: #1E3A8A; margin-bottom: 0.5rem;">The Conductor</h1>
        <h3 style="color: #5D4037; font-weight: normal; margin-top: 0;">Pattern Visualization Dashboard</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Load pattern data
    pattern_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/pattern_report.json"
    patterns = load_pattern_data(pattern_file)
    
    # Dashboard tabs with golden ratio proportions
    tab1, tab2, tab3 = st.tabs(["📊 Pattern Insights", "🎵 Audio-Visual Experience", "🔎 Pattern Explorer"])
    
    with tab1:
        display_pattern_insights(patterns)
    
    with tab2:
        display_pattern_visualization(patterns)
    
    with tab3:
        display_pattern_explorer(patterns)
    
    # Footer with Bach-inspired design
    st.markdown("""
    <div style="text-align: center; border-top: 1px solid #ddd; padding-top: 1rem; margin-top: 2rem;">
        <div style="font-family: serif; font-size: 1rem; color: #5D4037;">
            ♪ Conductor Framework ♫
        </div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem;">
            Mathematical Harmony • Pattern Recognition • Charter Extraction
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()