import math
import numpy as np
from typing import Dict, List, Any, Optional, Union
import json
import base64
from dataclasses import dataclass
import matplotlib.pyplot as plt
import io
import base64

# Golden ratio - our fundamental constant
PHI = (1 + math.sqrt(5)) / 2

@dataclass
class VisualPattern:
    """A visual representation of a pattern."""
    pattern_id: str
    pattern_type: str
    data_points: List[Dict[str, float]]
    color_map: List[str]
    metadata: Dict[str, Any]

@dataclass
class AudioPattern:
    """An audio representation of a pattern."""
    pattern_id: str
    pattern_type: str
    frequencies: List[float]
    amplitudes: List[float]
    durations: List[float]
    metadata: Dict[str, Any]

class MultiSensoryVisualizer:
    """Creates multi-sensory representations of patterns.
    
    This class implements transformations between different sensory modalities,
    allowing patterns to be experienced through visual, auditory, and eventually
    other sensory channels.
    """
    
    def __init__(self):
        # Initialize with Bach-inspired color maps
        self.color_maps = {
            "truth": ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78"],
            "connection": ["#2ca02c", "#98df8a", "#d62728", "#ff9896"],
            "growth": ["#9467bd", "#c5b0d5", "#8c564b", "#c49c94"],
            "balance": ["#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7"],
            "creativity": ["#bcbd22", "#dbdb8d", "#17becf", "#9edae5"]
        }
        
        # Bach's frequency ratios
        self.bach_ratios = [1, 4/3, 3/2, 5/3, 2]
        
    def create_golden_spiral(self, num_points: int = 100) -> VisualPattern:
        """Create a golden spiral visualization."""
        points = []
        
        for i in range(num_points):
            theta = i * 2 * math.pi / PHI
            r = PHI ** (i / 20)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append({"x": x, "y": y})
        
        return VisualPattern(
            pattern_id="golden_spiral",
            pattern_type="growth",
            data_points=points,
            color_map=self.color_maps["growth"],
            metadata={
                "description": "Golden spiral based on Fibonacci proportions",
                "phi": PHI
            }
        )
    
    def create_pattern_visualization(self, pattern_type: str, data: List[float]) -> VisualPattern:
        """Create a visualization of a pattern based on its type."""
        # Default to "truth" if pattern_type not recognized
        if pattern_type not in self.color_maps:
            pattern_type = "truth"
        
        # Create visualization based on pattern type
        if pattern_type == "growth":
            return self._create_growth_visualization(data)
        elif pattern_type == "balance":
            return self._create_balance_visualization(data)
        elif pattern_type == "connection":
            return self._create_connection_visualization(data)
        elif pattern_type == "creativity":
            return self._create_creativity_visualization(data)
        else:  # truth is default
            return self._create_truth_visualization(data)
    
    def _create_truth_visualization(self, data: List[float]) -> VisualPattern:
        """Create a visualization for truth patterns."""
        points = []
        
        # Create a balanced, symmetrical pattern
        for i, value in enumerate(data):
            # Convert to coordinates on a circle
            angle = i * 2 * math.pi / len(data)
            radius = 0.5 + (value / 2)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append({"x": x, "y": y})
        
        # Add connection to center for each point
        for i in range(len(points)):
            points.append({"x": 0, "y": 0})
            points.append(points[i])
        
        return VisualPattern(
            pattern_id=f"truth_{len(data)}",
            pattern_type="truth",
            data_points=points,
            color_map=self.color_maps["truth"],
            metadata={
                "description": "Truth pattern visualization",
                "data_points": len(data)
            }
        )
    
    def _create_growth_visualization(self, data: List[float]) -> VisualPattern:
        """Create a visualization for growth patterns."""
        points = []
        
        # Create a spiral pattern with increasing radius
        cumulative_growth = 0
        for i, value in enumerate(data):
            cumulative_growth += value
            # Convert to coordinates on an expanding spiral
            angle = i * 2 * math.pi / PHI
            radius = PHI ** (cumulative_growth / 2)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append({"x": x, "y": y})
        
        # Connect the points
        connected_points = []
        for i in range(len(points) - 1):
            connected_points.append(points[i])
            connected_points.append(points[i + 1])
        
        return VisualPattern(
            pattern_id=f"growth_{len(data)}",
            pattern_type="growth",
            data_points=connected_points if connected_points else points,
            color_map=self.color_maps["growth"],
            metadata={
                "description": "Growth pattern visualization",
                "data_points": len(data)
            }
        )
    
    def _create_balance_visualization(self, data: List[float]) -> VisualPattern:
        """Create a visualization for balance patterns."""
        points = []
        
        # Create a symmetric pattern around center
        for i, value in enumerate(data):
            # Convert to coordinates on horizontal line, alternating up/down
            x = (i - len(data)/2) / (len(data)/2)  # -1 to 1
            sign = 1 if i % 2 == 0 else -1
            y = sign * value
            points.append({"x": x, "y": y})
        
        # Add horizontal center line
        points.append({"x": -1, "y": 0})
        points.append({"x": 1, "y": 0})
        
        return VisualPattern(
            pattern_id=f"balance_{len(data)}",
            pattern_type="balance",
            data_points=points,
            color_map=self.color_maps["balance"],
            metadata={
                "description": "Balance pattern visualization",
                "data_points": len(data)
            }
        )
    
    def _create_connection_visualization(self, data: List[float]) -> VisualPattern:
        """Create a visualization for connection patterns."""
        points = []
        
        # Create nodes in a circle
        node_points = []
        for i in range(len(data)):
            angle = i * 2 * math.pi / len(data)
            x = math.cos(angle)
            y = math.sin(angle)
            node_points.append({"x": x, "y": y})
        
        # Add connections based on values
        for i, value in enumerate(data):
            src = node_points[i]
            # Connect to multiple other nodes based on value
            connections = int(value * 3) + 1  # 1 to 4 connections
            for j in range(connections):
                # Connect to node offset by golden ratio to create harmony
                target_idx = int((i + j * PHI) % len(node_points))
                target = node_points[target_idx]
                points.append(src)
                points.append(target)
        
        return VisualPattern(
            pattern_id=f"connection_{len(data)}",
            pattern_type="connection",
            data_points=points,
            color_map=self.color_maps["connection"],
            metadata={
                "description": "Connection pattern visualization",
                "data_points": len(data)
            }
        )
    
    def _create_creativity_visualization(self, data: List[float]) -> VisualPattern:
        """Create a visualization for creativity patterns."""
        points = []
        
        # Create a flowing, asymmetric pattern
        for i, value in enumerate(data):
            # Create multiple points for each value
            for j in range(3):  # 3 points per value
                angle = (i + j/3) * 2 * math.pi / len(data)
                # Vary radius based on both value and position
                radius = 0.3 + value * (0.7 + 0.3 * math.sin(j * PHI))
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                points.append({"x": x, "y": y})
        
        return VisualPattern(
            pattern_id=f"creativity_{len(data)}",
            pattern_type="creativity",
            data_points=points,
            color_map=self.color_maps["creativity"],
            metadata={
                "description": "Creativity pattern visualization",
                "data_points": len(data)
            }
        )
    
    def create_audio_pattern(self, pattern_type: str, data: List[float]) -> AudioPattern:
        """Create an audio representation of a pattern based on its type."""
        # Base frequency - A4 (440 Hz)
        base_frequency = 440
        
        # Create different frequency patterns based on type
        if pattern_type == "truth":
            # Truth uses pure harmonic ratios
            frequencies = [base_frequency * ratio for ratio in self.bach_ratios]
            # Amplitudes based on data values
            amplitudes = [min(1.0, max(0.1, v)) for v in data]
            # Equal durations
            durations = [0.5] * len(data)
        
        elif pattern_type == "growth":
            # Growth uses expanding frequency ratios
            frequencies = [base_frequency * (PHI ** i) for i in range(len(data))]
            # Amplitudes increase
            amplitudes = [0.3 + 0.7 * i / len(data) for i in range(len(data))]
            # Durations follow Fibonacci sequence
            fib = [1, 1, 2, 3, 5, 8, 13]
            durations = [0.1 * fib[min(i, len(fib)-1)] for i in range(len(data))]
        
        elif pattern_type == "balance":
            # Balance uses symmetric frequency ratios
            frequencies = []
            for i in range(len(data)):
                # Alternate above and below base frequency
                ratio = 1 + (i % 2) * 0.5 * (1 + i//2) * (1 if i % 4 < 2 else -1)
                frequencies.append(base_frequency * ratio)
            # Equal amplitudes
            amplitudes = [0.7] * len(data)
            # Equal durations
            durations = [0.3] * len(data)
        
        elif pattern_type == "connection":
            # Connection uses related frequency ratios
            frequencies = [base_frequency * ratio for ratio in [1, 3/2, 5/3, 2, 5/2, 3, 4]]
            frequencies = frequencies[:len(data)]
            # Amplitudes based on data
            amplitudes = [min(1.0, max(0.1, v)) for v in data]
            # Alternating durations
            durations = [0.2 if i % 2 == 0 else 0.4 for i in range(len(data))]
        
        elif pattern_type == "creativity":
            # Creativity uses more complex ratios
            frequencies = [base_frequency * ratio for ratio in [1, PHI, math.pi/2, math.e/2, PHI**2]]
            frequencies = frequencies[:len(data)]
            # Varied amplitudes
            amplitudes = [0.3 + 0.7 * v for v in data]
            # Varied durations
            durations = [0.1 + 0.3 * v for v in data]
        
        else:
            # Default case
            frequencies = [base_frequency * (1 + 0.2 * i) for i in range(len(data))]
            amplitudes = [0.5] * len(data)
            durations = [0.3] * len(data)
        
        # Ensure all lists are the same length
        min_length = min(len(frequencies), len(amplitudes), len(durations), len(data))
        frequencies = frequencies[:min_length]
        amplitudes = amplitudes[:min_length]
        durations = durations[:min_length]
        
        return AudioPattern(
            pattern_id=f"{pattern_type}_audio_{len(data)}",
            pattern_type=pattern_type,
            frequencies=frequencies,
            amplitudes=amplitudes,
            durations=durations,
            metadata={
                "description": f"{pattern_type.capitalize()} audio pattern",
                "base_frequency": base_frequency,
                "data_points": len(data)
            }
        )
    
    def render_visualization(self, visual: VisualPattern) -> Dict[str, Any]:
        """Render a visual pattern to a format suitable for display."""
        # Create a figure
        plt.figure(figsize=(10, 10))
        
        # Extract x and y coordinates
        x_coords = [p["x"] for p in visual.data_points]
        y_coords = [p["y"] for p in visual.data_points]
        
        # Determine what to plot based on data pattern
        if len(x_coords) % 2 == 0 and visual.pattern_type != "growth":  # Likely line segments
            # Plot line segments
            for i in range(0, len(x_coords), 2):
                if i+1 < len(x_coords):  # Ensure we have pairs
                    plt.plot(
                        [x_coords[i], x_coords[i+1]], 
                        [y_coords[i], y_coords[i+1]],
                        color=visual.color_map[i//2 % len(visual.color_map)],
                        linewidth=2
                    )
        else:  # Likely connected points
            plt.plot(
                x_coords, 
                y_coords,
                color=visual.color_map[0],
                linewidth=2
            )
            plt.scatter(
                x_coords, 
                y_coords,
                color=visual.color_map[1 % len(visual.color_map)],
                s=50
            )
        
        # Set equal aspect and remove axes
        plt.axis('equal')
        plt.axis('off')
        
        # Add title
        plt.title(visual.metadata.get("description", visual.pattern_type))
        
        # Save to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Convert to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return {
            "pattern_id": visual.pattern_id,
            "pattern_type": visual.pattern_type,
            "image_data": f"data:image/png;base64,{img_str}",
            "metadata": visual.metadata
        }
    
    def generate_audio_parameters(self, audio: AudioPattern) -> Dict[str, Any]:
        """Generate parameters for audio synthesis."""
        # In a production system, this would generate actual audio
        # Here we just return the parameters needed for synthesis
        
        return {
            "pattern_id": audio.pattern_id,
            "pattern_type": audio.pattern_type,
            "frequencies": audio.frequencies,
            "amplitudes": audio.amplitudes,
            "durations": audio.durations,
            "total_duration": sum(audio.durations),
            "metadata": audio.metadata
        }

# Create singleton instance
visualizer = MultiSensoryVisualizer()