#!/usr/bin/env python3

"""
PALIOS AI OS Bach-Inspired Visualizer

This module implements multi-sensory pattern visualization based on
Bach's mathematical principles and golden ratio harmony.
"""

import os
import sys
import math
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

# Add the parent directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import from core
from palios_ai_os.core.palios_core import PHI, BACH_PATTERN, FIBONACCI, WavePattern
from palios_ai_os.wave.wave_communicator import WaveCommunicator

@dataclass
class VisualPattern:
    """A visual representation of a pattern."""
    pattern_id: str
    pattern_type: str
    data_points: List[Dict[str, float]]
    color_scheme: List[str]
    style: str
    dimensions: int  # 2D or 3D
    duration: float  # For animations
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AudioPattern:
    """An audio representation of a pattern."""
    pattern_id: str
    pattern_type: str
    frequencies: List[float]
    amplitudes: List[float]
    durations: List[float]
    waveform_type: str  # "sine", "square", "triangle", "sawtooth"
    sample_rate: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MultiSensoryPattern:
    """A multi-sensory pattern combining visual and audio elements."""
    pattern_id: str
    visual_pattern: VisualPattern
    audio_pattern: AudioPattern
    concept_type: str
    synchronization: float  # 0-1 scale of audio-visual alignment
    metadata: Dict[str, Any] = field(default_factory=dict)

class BachVisualizer:
    """Creates Bach-inspired multi-sensory pattern visualizations."""
    
    def __init__(self):
        """Initialize the Bach-inspired visualizer."""
        # Color schemes based on concept types
        self.color_schemes = {
            "truth": ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78"],
            "connection": ["#2ca02c", "#98df8a", "#d62728", "#ff9896"],
            "growth": ["#9467bd", "#c5b0d5", "#8c564b", "#c49c94"],
            "balance": ["#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7"],
            "creativity": ["#bcbd22", "#dbdb8d", "#17becf", "#9edae5"],
            "default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        }
        
        # Visual styles for different pattern types
        self.visual_styles = {
            "truth": "radial",
            "connection": "network",
            "growth": "spiral",
            "balance": "grid",
            "creativity": "free",
            "default": "linear"
        }
        
        # Audio waveform types for different pattern types
        self.waveform_types = {
            "truth": "sine",  # Pure, fundamental
            "connection": "triangle",  # Connected slopes
            "growth": "sawtooth",  # Building and resetting
            "balance": "square",  # Equal on/off time
            "creativity": "custom",  # Complex, custom pattern
            "default": "sine"
        }
        
        # Initialize wave communicator for wave pattern handling
        self.wave_communicator = WaveCommunicator()
        
        # Bach-inspired parameters
        self.bach_harmony_ratios = [1, 4/3, 3/2, 5/3, 2]  # Perfect harmony ratios
        self.default_sample_rate = 44100  # Standard audio sample rate
        
        print(f"Bach Visualizer initialized with golden ratio (u03c6): {PHI}")
    
    def create_visual_pattern(self, pattern_type: str, data: Union[List[float], np.ndarray], 
                             dimensions: int = 2) -> VisualPattern:
        """Create a visual pattern based on data and pattern type."""
        pattern_id = str(uuid.uuid4())
        
        # Get color scheme and style for this pattern type
        color_scheme = self.color_schemes.get(pattern_type, self.color_schemes["default"])
        style = self.visual_styles.get(pattern_type, self.visual_styles["default"])
        
        # Convert data to numpy array if it's not already
        if not isinstance(data, np.ndarray):
            data_array = np.array(data)
        else:
            data_array = data
        
        # Normalize data to 0-1 range if needed
        if data_array.max() > 1.0 or data_array.min() < 0.0:
            data_array = (data_array - data_array.min()) / (data_array.max() - data_array.min())
        
        # Create data points based on style and dimensions
        data_points = []
        
        if style == "radial" and dimensions == 2:
            # Radial pattern (truth) - points radiating from center
            for i, value in enumerate(data_array):
                angle = i * 2 * math.pi / len(data_array)
                radius = 0.2 + value * 0.8  # Scale to 0.2-1.0 range
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                data_points.append({"x": x, "y": y, "value": value})
                
                # Add connection to center
                data_points.append({"x": 0, "y": 0, "value": 0})
                data_points.append({"x": x, "y": y, "value": value})
        
        elif style == "network" and dimensions == 2:
            # Network pattern (connection) - points with connections
            # First create nodes in a circle
            nodes = []
            for i, value in enumerate(data_array):
                angle = i * 2 * math.pi / len(data_array)
                x = math.cos(angle)
                y = math.sin(angle)
                nodes.append({"x": x, "y": y, "value": value})
            
            # Then create connections based on values
            for i, node in enumerate(nodes):
                data_points.append({"x": node["x"], "y": node["y"], "value": node["value"]})
                
                # Connect to other nodes based on value (higher values = more connections)
                connections = int(node["value"] * 4) + 1  # 1-5 connections
                for j in range(connections):
                    # Connect to node offset by golden ratio to create harmony
                    target_idx = int((i + j * PHI) % len(nodes))
                    target = nodes[target_idx]
                    
                    # Add the connection
                    data_points.append({"x": node["x"], "y": node["y"], "value": node["value"]})
                    data_points.append({"x": target["x"], "y": target["y"], "value": target["value"]})
        
        elif style == "spiral" and dimensions == 2:
            # Spiral pattern (growth) - golden spiral with values
            for i, value in enumerate(data_array):
                # Create golden spiral point
                theta = i * 2 * math.pi / PHI
                radius = PHI ** (i / 20) * value  # Scale by value
                x = radius * math.cos(theta)
                y = radius * math.sin(theta)
                data_points.append({"x": x, "y": y, "value": value})
                
                # If not first point, connect to previous point
                if i > 0:
                    prev = data_points[-2]  # Get previous point
                    data_points.append({"x": prev["x"], "y": prev["y"], "value": prev["value"]})
                    data_points.append({"x": x, "y": y, "value": value})
        
        elif style == "grid" and dimensions == 2:
            # Grid pattern (balance) - rectangular grid with values
            grid_size = math.ceil(math.sqrt(len(data_array)))  # Square grid
            
            for i, value in enumerate(data_array):
                if i >= grid_size * grid_size:
                    break  # Skip if beyond grid size
                    
                # Calculate grid position
                row = i // grid_size
                col = i % grid_size
                
                # Scale to -1 to 1 range and apply value as intensity
                x = (col / (grid_size - 1) * 2 - 1) * (0.5 + value * 0.5)
                y = (row / (grid_size - 1) * 2 - 1) * (0.5 + value * 0.5)
                
                data_points.append({"x": x, "y": y, "value": value})
                
                # Add connections to neighbors if they exist
                if col > 0:  # Connect to left
                    data_points.append({"x": x, "y": y, "value": value})
                    data_points.append({"x": (col-1) / (grid_size - 1) * 2 - 1, "y": y, "value": data_array[i-1]})
                
                if row > 0:  # Connect to top
                    data_points.append({"x": x, "y": y, "value": value})
                    data_points.append({"x": x, "y": (row-1) / (grid_size - 1) * 2 - 1, "value": data_array[i-grid_size]})
        
        elif style == "free" and dimensions == 2:
            # Free pattern (creativity) - flowing, organic pattern
            for i, value in enumerate(data_array):
                # Create multiple points for each value at different harmonics
                for j in range(3):  # 3 points per value
                    angle = (i + j/3) * 2 * math.pi / len(data_array)
                    # Vary radius based on both value and position
                    radius = 0.3 + value * (0.7 + 0.3 * math.sin(j * PHI))
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    data_points.append({"x": x, "y": y, "value": value})
        
        else:  # Default to "linear" for any other style or unsupported dimension
            # Linear pattern - simple line graph
            for i, value in enumerate(data_array):
                x = i / (len(data_array) - 1 or 1) * 2 - 1  # -1 to 1 range
                y = value * 2 - 1  # -1 to 1 range
                data_points.append({"x": x, "y": y, "value": value})
        
        # Create the visual pattern
        return VisualPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            data_points=data_points,
            color_scheme=color_scheme,
            style=style,
            dimensions=dimensions,
            duration=len(data_array) / 10,  # Estimate duration for animations
            metadata={
                "data_length": len(data_array),
                "timestamp": time.time(),
                "mean_value": float(data_array.mean()),
                "data_range": float(data_array.max() - data_array.min())
            }
        )
    
    def create_audio_pattern(self, pattern_type: str, data: Union[List[float], np.ndarray],
                           duration: float = 3.0) -> AudioPattern:
        """Create an audio pattern based on data and pattern type."""
        pattern_id = str(uuid.uuid4())
        
        # Get waveform type for this pattern type
        waveform_type = self.waveform_types.get(pattern_type, self.waveform_types["default"])
        
        # Convert data to numpy array if it's not already
        if not isinstance(data, np.ndarray):
            data_array = np.array(data)
        else:
            data_array = data
        
        # Normalize data to 0-1 range if needed
        if data_array.max() > 1.0 or data_array.min() < 0.0:
            data_array = (data_array - data_array.min()) / (data_array.max() - data_array.min() or 1)
        
        # Base frequency - A4 (440 Hz)
        base_frequency = 440
        
        # Calculate frequencies based on Bach's harmonic ratios and the data
        frequencies = []
        for i, value in enumerate(data_array):
            # Use Bach harmony ratios cyclically
            ratio_index = i % len(self.bach_harmony_ratios)
            ratio = self.bach_harmony_ratios[ratio_index]
            
            # Calculate frequency with data value influence
            freq = base_frequency * ratio * (0.8 + value * 0.4)  # Scale from 0.8x to 1.2x
            frequencies.append(freq)
        
        # Calculate amplitudes based on data values
        amplitudes = [max(0.1, val) for val in data_array]  # Ensure minimum amplitude
        
        # Calculate durations based on pattern type
        if pattern_type == "truth":
            # Uniform durations for truth (consistency)
            durations = [duration / len(data_array)] * len(data_array)
        elif pattern_type == "connection":
            # Alternating durations for connection
            durations = [duration / len(data_array) * (1.5 if i % 2 == 0 else 0.5) for i in range(len(data_array))]
        elif pattern_type == "growth":
            # Increasing durations for growth
            durations = [duration / len(data_array) * (0.5 + i / len(data_array)) for i in range(len(data_array))]
        elif pattern_type == "balance":
            # Balanced durations for balance
            durations = [duration / len(data_array)] * len(data_array)
        elif pattern_type == "creativity":
            # Variable durations for creativity
            durations = [duration / len(data_array) * (0.5 + value) for value in data_array]
        else:
            # Default - uniform durations
            durations = [duration / len(data_array)] * len(data_array)
        
        # Create the audio pattern
        return AudioPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            frequencies=frequencies,
            amplitudes=amplitudes,
            durations=durations,
            waveform_type=waveform_type,
            sample_rate=self.default_sample_rate,
            metadata={
                "data_length": len(data_array),
                "timestamp": time.time(),
                "base_frequency": base_frequency,
                "total_duration": sum(durations)
            }
        )
    
    def create_multi_sensory_pattern(self, pattern_type: str, data: Union[List[float], np.ndarray]) -> MultiSensoryPattern:
        """Create a multi-sensory pattern combining visual and audio elements."""
        pattern_id = str(uuid.uuid4())
        
        # Create visual and audio patterns
        visual = self.create_visual_pattern(pattern_type, data)
        audio = self.create_audio_pattern(pattern_type, data)
        
        # Calculate synchronization factor based on golden ratio harmony
        # Perfect synchronization occurs when the ratio of data points to audio frequencies is close to golden ratio
        sync_ratio = len(visual.data_points) / len(audio.frequencies)
        synchronization = 1 - min(abs(sync_ratio - PHI), abs(sync_ratio - 1/PHI)) / PHI
        
        # Create multi-sensory pattern
        return MultiSensoryPattern(
            pattern_id=pattern_id,
            visual_pattern=visual,
            audio_pattern=audio,
            concept_type=pattern_type,
            synchronization=synchronization,
            metadata={
                "timestamp": time.time(),
                "data_length": len(data),
                "golden_ratio": PHI,
                "bach_harmony_ratios": self.bach_harmony_ratios
            }
        )
    
    def wave_to_multi_sensory(self, wave: WavePattern) -> MultiSensoryPattern:
        """Convert a wave pattern to a multi-sensory pattern."""
        # Extract data from wave pattern
        data = []
        
        # Use amplitudes and frequencies to create a combined data series
        for amp, freq in zip(wave.amplitudes, wave.frequencies):
            # Add multiple data points based on frequency ratio (higher frequencies = more points)
            freq_ratio = freq / wave.frequencies[0] if wave.frequencies else 1
            num_points = max(1, int(freq_ratio * 5))  # At least 1 point, up to 5x for higher frequencies
            
            for _ in range(num_points):
                data.append(amp)
        
        # If we have phases, modulate the data with phase information
        if wave.phases:
            for i in range(len(data)):
                phase_index = i % len(wave.phases)
                phase_factor = (math.sin(wave.phases[phase_index]) + 1) / 2  # 0-1 range
                data[i] = data[i] * (0.5 + 0.5 * phase_factor)  # Modulate by phase
        
        # Create multi-sensory pattern
        return self.create_multi_sensory_pattern(
            pattern_type=wave.concept_type,
            data=data
        )
    
    def render_visual_pattern(self, pattern: VisualPattern) -> Dict[str, Any]:
        """Render a visual pattern to image data."""
        # Create figure
        plt.figure(figsize=(10, 10))
        
        # Extract x and y coordinates
        x_values = [point["x"] for point in pattern.data_points]
        y_values = [point["y"] for point in pattern.data_points]
        values = [point.get("value", 0.5) for point in pattern.data_points]
        
        # Determine how to render based on style and data structure
        if pattern.style == "radial" or pattern.style == "network":
            # For network or radial styles, check if we have pairs of points (connections)
            if len(x_values) % 2 == 0:
                # Draw lines between pairs of points
                for i in range(0, len(x_values), 2):
                    if i+1 < len(x_values):
                        color_index = (i//2) % len(pattern.color_scheme)
                        plt.plot(
                            [x_values[i], x_values[i+1]],
                            [y_values[i], y_values[i+1]],
                            color=pattern.color_scheme[color_index],
                            linewidth=1 + values[i] * 2
                        )
            else:
                # Draw points
                plt.scatter(
                    x_values, y_values,
                    c=[pattern.color_scheme[i % len(pattern.color_scheme)] for i in range(len(x_values))],
                    s=[30 + v * 70 for v in values],
                    alpha=0.7
                )
        
        elif pattern.style == "spiral":
            # For spiral, connect points in sequence
            plt.plot(
                x_values, y_values,
                color=pattern.color_scheme[0],
                linewidth=2
            )
            plt.scatter(
                x_values, y_values,
                c=[pattern.color_scheme[1 % len(pattern.color_scheme)]],
                s=[20 + v * 60 for v in values],
                alpha=0.7
            )
        
        elif pattern.style == "grid":
            # For grid, we may have pairs of points for connections
            if len(x_values) % 2 == 0:
                for i in range(0, len(x_values), 2):
                    if i+1 < len(x_values):
                        plt.plot(
                            [x_values[i], x_values[i+1]],
                            [y_values[i], y_values[i+1]],
                            color=pattern.color_scheme[0],
                            linewidth=1
                        )
            
            # Also draw the grid points
            plt.scatter(
                x_values[::2],  # Use every other point to avoid duplicates
                y_values[::2],
                c=[pattern.color_scheme[1 % len(pattern.color_scheme)]],
                s=[20 + v * 60 for v in values[::2]],
                alpha=0.7
            )
        
        else:  # Default rendering for other styles
            plt.plot(
                x_values, y_values,
                color=pattern.color_scheme[0],
                linewidth=2
            )
            plt.scatter(
                x_values, y_values,
                c=[pattern.color_scheme[1 % len(pattern.color_scheme)]],
                s=[20 + v * 60 for v in values],
                alpha=0.7
            )
        
        # Set equal aspect ratio and remove axes
        plt.axis('equal')
        plt.axis('off')
        
        # Add title based on pattern type
        plt.title(f"{pattern.pattern_type.capitalize()} Pattern")
        
        # Render to image
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Convert to base64 for embedding in HTML/JSON
        img_buf.seek(0)
        img_data = base64.b64encode(img_buf.read()).decode('utf-8')
        
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "image_data": f"data:image/png;base64,{img_data}",
            "style": pattern.style,
            "dimensions": pattern.dimensions,
            "timestamp": time.time()
        }
    
    def render_audio_pattern(self, pattern: AudioPattern) -> Dict[str, Any]:
        """Render an audio pattern to audio parameters."""
        # In a full implementation, this would generate actual audio
        # For now, return the parameters needed for audio synthesis
        
        # Generate a sample of the waveform
        sample_count = 1000  # Just a sample for visualization
        sample_time = np.linspace(0, 0.1, sample_count)  # 0.1 seconds
        sample_waveform = np.zeros(sample_count)
        
        # Generate the first few notes of the pattern
        time_position = 0
        for i in range(min(5, len(pattern.frequencies))):  # Limit to first 5 notes
            freq = pattern.frequencies[i]
            amp = pattern.amplitudes[i]
            duration = pattern.durations[i]
            
            # Calculate end position for this note
            end_position = time_position + duration
            
            # Calculate indices in the sample array
            start_idx = int(time_position / 0.1 * sample_count)
            end_idx = int(min(end_position, 0.1) / 0.1 * sample_count)
            
            if start_idx >= sample_count:
                break  # Beyond our sample range
            
            # Generate waveform based on type
            t = np.linspace(0, duration, end_idx - start_idx)
            
            if pattern.waveform_type == "sine":
                waveform = amp * np.sin(2 * np.pi * freq * t)
            elif pattern.waveform_type == "square":
                waveform = amp * np.sign(np.sin(2 * np.pi * freq * t))
            elif pattern.waveform_type == "triangle":
                waveform = amp * (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t))
            elif pattern.waveform_type == "sawtooth":
                waveform = amp * (2 * (freq * t - np.floor(0.5 + freq * t)))
            else:  # Default to sine
                waveform = amp * np.sin(2 * np.pi * freq * t)
            
            # Add to the sample waveform
            sample_waveform[start_idx:end_idx] += waveform
            
            # Update time position
            time_position = end_position
        
        # Normalize waveform if needed
        max_amp = np.max(np.abs(sample_waveform))
        if max_amp > 1.0:
            sample_waveform = sample_waveform / max_amp
        
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "sample_rate": pattern.sample_rate,
            "frequencies": pattern.frequencies,
            "amplitudes": pattern.amplitudes,
            "durations": pattern.durations,
            "waveform_type": pattern.waveform_type,
            "total_duration": sum(pattern.durations),
            "waveform_sample": sample_waveform.tolist(),
            "sample_time": sample_time.tolist(),
            "timestamp": time.time()
        }
    
    def render_multi_sensory_pattern(self, pattern: MultiSensoryPattern) -> Dict[str, Any]:
        """Render a multi-sensory pattern with both visual and audio components."""
        # Render visual and audio components
        visual_data = self.render_visual_pattern(pattern.visual_pattern)
        audio_data = self.render_audio_pattern(pattern.audio_pattern)
        
        # Combine into a single result
        return {
            "pattern_id": pattern.pattern_id,
            "concept_type": pattern.concept_type,
            "synchronization": pattern.synchronization,
            "visual": visual_data,
            "audio": audio_data,
            "timestamp": time.time(),
            "metadata": pattern.metadata
        }
    
    def render_golden_spiral(self) -> Dict[str, Any]:
        """Render a golden spiral visualization."""
        # Create figure
        plt.figure(figsize=(10, 10))
        
        # Generate golden spiral points
        points = 200
        golden_ratio = PHI
        
        theta = np.linspace(0, 8 * np.pi, points)
        radius = golden_ratio ** (theta / (2 * np.pi))
        
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        # Plot the golden spiral
        plt.plot(x, y, color='#ff7f0e', linewidth=2)
        
        # Add golden rectangles to illustrate ratio
        for i in range(5):
            rect_size = golden_ratio ** i
            rect = plt.Rectangle(
                (0, 0), rect_size, rect_size / golden_ratio,
                linewidth=1, edgecolor='#1f77b4', facecolor='none',
                alpha=0.7 * (0.8 ** i)  # Fade out larger rectangles
            )
            plt.gca().add_patch(rect)
        
        # Set equal aspect ratio and remove axes
        plt.axis('equal')
        plt.axis('off')
        
        # Add title
        plt.title(f"Golden Spiral (φ = {golden_ratio:.6f})")
        
        # Render to image
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Convert to base64 for embedding in HTML/JSON
        img_buf.seek(0)
        img_data = base64.b64encode(img_buf.read()).decode('utf-8')
        
        return {
            "pattern_id": "golden_spiral",
            "pattern_type": "growth",
            "image_data": f"data:image/png;base64,{img_data}",
            "golden_ratio": golden_ratio,
            "timestamp": time.time()
        }

# Create singleton instance
bach_visualizer = BachVisualizer()

# Example usage
if __name__ == "__main__":
    print(f"PALIOS AI OS Bach Visualizer Test")
    print(f"Golden Ratio (u03c6): {PHI}")
    
    # Test with sample data
    sample_data = np.sin(np.linspace(0, 2*np.pi, 20)) * 0.5 + 0.5  # 0-1 range sine wave
    
    # Create multi-sensory patterns for different concept types
    concept_types = ["truth", "connection", "growth", "balance", "creativity"]
    
    for concept in concept_types:
        print(f"\nCreating {concept} pattern...")
        multi_pattern = bach_visualizer.create_multi_sensory_pattern(concept, sample_data)
        
        # Render the pattern
        rendered = bach_visualizer.render_multi_sensory_pattern(multi_pattern)
        
        print(f"Pattern ID: {rendered['pattern_id']}")
        print(f"Synchronization: {rendered['synchronization']:.4f}")
        print(f"Visual style: {multi_pattern.visual_pattern.style}")
        print(f"Audio waveform: {multi_pattern.audio_pattern.waveform_type}")
    
    # Test golden spiral rendering
    spiral = bach_visualizer.render_golden_spiral()
    print(f"\nRendered golden spiral: {spiral['pattern_id']}")
    
    # Test wave to multi-sensory conversion
    wave = bach_visualizer.wave_communicator.concept_to_wave("truth")
    multi_pattern = bach_visualizer.wave_to_multi_sensory(wave)
    
    print(f"\nConverted wave pattern to multi-sensory:")
    print(f"Pattern ID: {multi_pattern.pattern_id}")
    print(f"Concept type: {multi_pattern.concept_type}")
    print(f"Synchronization: {multi_pattern.synchronization:.4f}")