#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="The Conductor - Pattern Dashboard",
    page_icon="🎵",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.6rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.6rem;
        color: #5D4037;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: normal;
    }
    
    .pattern-card {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: rgba(255, 255, 255, 0.8);
        border-left: 5px solid #1E88E5;
    }
    
    .stPlotlyChart {
        background-color: rgba(240, 242, 246, 0.7);
        border-radius: 10px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def load_pattern_data():
    """Load pattern data from file."""
    pattern_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns/pattern_report.json"
    
    if os.path.exists(pattern_file):
        with open(pattern_file, 'r') as f:
            return json.load(f)
    else:
        st.error("Pattern data file not found. Please run the transcript processor first.")
        return None

def display_header():
    """Display the dashboard header."""
    st.markdown('<div class="main-header">The Conductor Framework</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pattern Visualization Dashboard</div>', unsafe_allow_html=True)

def confidence_color(confidence):
    """Convert confidence value to a color."""
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

def display_pattern_distribution(patterns):
    """Display pattern distribution charts."""
    st.markdown("## 📊 Pattern Distribution")
    
    # Create columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Create pie chart of pattern frequency
        if "frequency_distribution" in patterns:
            labels = list(patterns["frequency_distribution"].keys())
            values = list(patterns["frequency_distribution"].values())
            
            fig = px.pie(
                values=values,
                names=labels,
                color_discrete_sequence=px.colors.sequential.Viridis,
                hole=0.4
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create bar chart of pattern counts
        if "pattern_count" in patterns:
            pattern_types = list(patterns["pattern_count"].keys())
            counts = list(patterns["pattern_count"].values())
            
            fig = px.bar(
                x=pattern_types,
                y=counts,
                color=pattern_types,
                color_discrete_sequence=px.colors.sequential.Viridis,
                labels={"x": "Pattern Type", "y": "Count"}
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=400,
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_top_patterns(patterns):
    """Display top patterns."""
    st.markdown("## 🔍 Top Patterns")
    
    if "top_patterns" in patterns:
        for pattern in patterns["top_patterns"][:5]:  # Show top 5
            # Create a card for each pattern
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

def display_pattern_explorer(patterns):
    """Display pattern explorer."""
    st.markdown("## 🔎 Pattern Explorer")
    
    # Get all pattern types
    all_pattern_types = []
    
    if "pattern_count" in patterns:
        all_pattern_types = list(patterns["pattern_count"].keys())
    
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
        
        for pattern in filtered_patterns:
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
        st.info("No patterns match the selected filters.")

def main():
    """Main function to run the dashboard."""
    # Display header
    display_header()
    
    # Load pattern data
    patterns = load_pattern_data()
    
    if patterns:
        # Create tabs
        tab1, tab2 = st.tabs(["📊 Pattern Distribution", "🔍 Pattern Explorer"])
        
        with tab1:
            display_pattern_distribution(patterns)
            display_top_patterns(patterns)
        
        with tab2:
            display_pattern_explorer(patterns)
    
    # Add footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding-top: 1rem;">
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