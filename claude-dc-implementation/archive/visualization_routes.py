#!/usr/bin/env python3
"""
visualization_routes.py: Visualization and Audio Endpoints
---------------------------------------------------------
Branch component of the Bach-inspired architecture.
Provides endpoints for visual and audio representation of patterns.

This module follows golden ratio relationships in its structure and
implements endpoints that transform mathematical patterns into
multi-sensory experiences.
"""

import os
import io
import json
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from fastapi import APIRouter, Request, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# For audio generation
from scipy.io import wavfile

# Constants following golden ratio relationships
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio
PATTERNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patterns")
VISUALIZATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "visualizations")
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "audio")

# Ensure directories exist
os.makedirs(PATTERNS_DIR, exist_ok=True)
os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# Initialize router - branch of the larger harmonic structure
router = APIRouter()

# Models with Bach-inspired structure - clear, precise, mathematical
class VisualizationRequest(BaseModel):
    """Request model for pattern visualization"""
    pattern_id: str = Field(..., description="Pattern ID to visualize")
    visualization_type: str = Field(default="line", description="Type of visualization")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Visualization parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "pattern_id": "fibonacci_20250326121530",
                "visualization_type": "line",
                "parameters": {
                    "width": 800,
                    "height": 600,
                    "color": "#1f77b4",
                    "title": "Fibonacci Sequence Visualization"
                }
            }
        }

class AudioRequest(BaseModel):
    """Request model for pattern sonification"""
    pattern_id: str = Field(..., description="Pattern ID to convert to audio")
    audio_type: str = Field(default="direct", description="Type of audio conversion")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Audio parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "pattern_id": "wave_20250326121530",
                "audio_type": "direct",
                "parameters": {
                    "sample_rate": 44100,
                    "duration": 5.0,
                    "base_frequency": 440
                }
            }
        }

# Visualization functions
def create_line_visualization(
    data: Union[List[float], Dict[str, List[float]]],
    title: str = "Pattern Visualization",
    width: int = 800,
    height: int = 600,
    color: str = "#1f77b4",
    background: str = "#f8f9fa",
    grid: bool = True,
    show_points: bool = False,
    line_width: float = 1.5,
):
    """Create a line visualization of pattern data"""
    # Set figure size with golden ratio proportions
    fig_width = width / 100  # Convert pixels to inches (assuming 100 dpi)
    fig_height = height / 100
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=background)
    
    # Plot data
    if isinstance(data, dict):
        # Multiple lines (e.g., Bach patterns with variations)
        for i, (name, values) in enumerate(data.items()):
            # Use color with golden ratio hue shifts for variations
            hue = i / (len(data) * PHI)
            from matplotlib.colors import hsv_to_rgb
            rgb = hsv_to_rgb([hue, 0.8, 0.9])
            
            ax.plot(
                values, 
                label=name,
                color=rgb,
                linewidth=line_width,
                marker='o' if show_points else None,
                markersize=4 if show_points else 0
            )
        ax.legend()
    else:
        # Single line
        ax.plot(
            data, 
            color=color, 
            linewidth=line_width,
            marker='o' if show_points else None,
            markersize=4 if show_points else 0
        )
    
    # Customize appearance with Bach-inspired precision
    ax.set_title(title)
    ax.set_facecolor(background)
    
    if grid:
        ax.grid(True, linestyle='--', alpha=0.7)
    
    # Adjust layout for clean proportions
    plt.tight_layout()
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    return buf

def create_circle_visualization(
    data: List[float],
    title: str = "Circular Pattern Visualization",
    width: int = 800,
    height: int = 800,  # Keep square for circles
    color: str = "#1f77b4",
    background: str = "#f8f9fa",
    line_width: float = 1.5,
):
    """Create a circular visualization of pattern data"""
    # Set figure size with golden ratio proportions
    fig_width = width / 100  # Convert pixels to inches (assuming 100 dpi)
    fig_height = height / 100
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=background, subplot_kw={'projection': 'polar'})
    
    # Normalize data for radial display
    if max(data) != min(data):
        normalized_data = [(x - min(data)) / (max(data) - min(data)) for x in data]
    else:
        normalized_data = [0.5 for _ in data]
    
    # Convert to polar coordinates
    theta = np.linspace(0, 2 * np.pi, len(data), endpoint=False)
    
    # Plot data
    ax.plot(theta, normalized_data, color=color, linewidth=line_width)
    ax.fill(theta, normalized_data, color=color, alpha=0.25)
    
    # Customize appearance with Bach-inspired precision
    ax.set_title(title)
    ax.set_facecolor(background)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Remove radial labels for cleaner look
    ax.set_yticklabels([])
    
    # Adjust layout for clean proportions
    plt.tight_layout()
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    return buf

def create_spectrogram_visualization(
    data: List[float],
    title: str = "Pattern Spectrogram",
    width: int = 800,
    height: int = 600,
    cmap: str = "viridis",
    background: str = "#f8f9fa",
):
    """Create a spectrogram visualization of pattern data"""
    # Set figure size with golden ratio proportions
    fig_width = width / 100  # Convert pixels to inches (assuming 100 dpi)
    fig_height = height / 100
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=background)
    
    # Create spectrogram
    # Reshape data if needed to create a 2D representation
    if len(data) < 64:
        # Not enough data points, repeat the pattern
        repetitions = math.ceil(64 / len(data))
        expanded_data = data * repetitions
        data_to_use = expanded_data[:64]
    else:
        data_to_use = data
    
    # Determine a good block size based on data length
    block_size = min(32, len(data_to_use) // 8)
    block_size = max(block_size, 4)  # Ensure minimum block size
    
    # Create spectrogram data
    from scipy import signal
    frequencies, times, Sxx = signal.spectrogram(
        data_to_use,
        fs=100,  # Arbitrary sample rate
        window=signal.get_window('hann', block_size),
        nperseg=block_size,
        noverlap=block_size // 2,
        scaling='spectrum'
    )
    
    # Plot the spectrogram
    pcm = ax.pcolormesh(times, frequencies, 10 * np.log10(Sxx), cmap=cmap, shading='gouraud')
    fig.colorbar(pcm, ax=ax, label='Power/Frequency (dB/Hz)')
    
    # Customize appearance with Bach-inspired precision
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('Frequency')
    ax.set_facecolor(background)
    
    # Adjust layout for clean proportions
    plt.tight_layout()
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    return buf

# Audio generation functions
def create_direct_audio(
    data: List[float],
    sample_rate: int = 44100,
    duration: float = 5.0,
):
    """
    Create audio directly from pattern data.
    Maps the pattern directly to audio amplitudes.
    """
    # Normalize data to range [-1, 1] for audio
    if max(data) != min(data):
        normalized_data = [2 * (x - min(data)) / (max(data) - min(data)) - 1 for x in data]
    else:
        normalized_data = [0 for _ in data]
    
    # Calculate total number of samples
    num_samples = int(sample_rate * duration)
    
    # Interpolate or repeat pattern to fill the duration
    if len(normalized_data) < num_samples:
        # Repeat the pattern to fill the duration
        repetitions = math.ceil(num_samples / len(normalized_data))
        audio_data = normalized_data * repetitions
        audio_data = audio_data[:num_samples]
    else:
        # Interpolate to reduce to requested duration
        indices = np.linspace(0, len(normalized_data) - 1, num_samples)
        audio_data = np.interp(indices, np.arange(len(normalized_data)), normalized_data)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, audio_data)
    buf.seek(0)
    
    return buf

def create_frequency_modulated_audio(
    data: List[float],
    sample_rate: int = 44100,
    duration: float = 5.0,
    base_frequency: float = 440.0,  # A4 note
    frequency_range: float = 1000.0,
):
    """
    Create audio using frequency modulation based on pattern data.
    Maps the pattern to frequency variations around a base frequency.
    """
    # Normalize data to range [0, 1]
    if max(data) != min(data):
        normalized_data = [(x - min(data)) / (max(data) - min(data)) for x in data]
    else:
        normalized_data = [0.5 for _ in data]
    
    # Calculate total number of samples
    num_samples = int(sample_rate * duration)
    
    # Time array
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    # Interpolate pattern to match number of samples
    indices = np.linspace(0, len(normalized_data) - 1, num_samples)
    pattern_interpolated = np.interp(indices, np.arange(len(normalized_data)), normalized_data)
    
    # Generate frequency modulation
    frequencies = base_frequency + pattern_interpolated * frequency_range
    
    # Generate phase by integrating frequency
    phase = 2 * np.pi * np.cumsum(frequencies) / sample_rate
    
    # Generate audio signal
    audio_data = 0.8 * np.sin(phase)
    
    # Apply envelope to avoid clicks
    envelope = np.ones(num_samples)
    attack_samples = int(0.01 * sample_rate)  # 10ms attack
    decay_samples = int(0.01 * sample_rate)   # 10ms decay
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
    audio_data = audio_data * envelope
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, audio_data)
    buf.seek(0)
    
    return buf

def create_harmonic_audio(
    data: Union[List[float], Dict[str, List[float]]],
    sample_rate: int = 44100,
    duration: float = 5.0,
    base_frequency: float = 220.0,  # A3 note
):
    """
    Create audio using harmonic synthesis based on pattern data.
    Uses the pattern to control harmonic content of the sound.
    """
    # Handle different data types
    if isinstance(data, dict):
        # Use main theme or first available series
        if "theme" in data:
            primary_data = data["theme"]
        else:
            primary_data = list(data.values())[0]
    else:
        primary_data = data
    
    # Normalize data to range [0, 1]
    if max(primary_data) != min(primary_data):
        normalized_data = [(x - min(primary_data)) / (max(primary_data) - min(primary_data)) for x in primary_data]
    else:
        normalized_data = [0.5 for _ in primary_data]
    
    # Calculate total number of samples
    num_samples = int(sample_rate * duration)
    
    # Time array
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    # Interpolate pattern to match number of samples
    indices = np.linspace(0, len(normalized_data) - 1, num_samples)
    pattern_interpolated = np.interp(indices, np.arange(len(normalized_data)), normalized_data)
    
    # Generate harmonic series
    audio_data = np.zeros(num_samples)
    
    # Use pattern data to control harmonic amplitudes
    num_harmonics = min(15, len(normalized_data))
    for i in range(num_harmonics):
        # Get amplitude for this harmonic
        if i < len(normalized_data):
            # Use data point directly
            harmonic_amplitude = normalized_data[i]
        else:
            # For higher harmonics, use modulo indexing
            harmonic_amplitude = normalized_data[i % len(normalized_data)]
        
        # Calculate frequency for this harmonic
        harmonic_frequency = base_frequency * (i + 1)
        
        # Add harmonic with appropriate amplitude
        # Use golden ratio to create natural decay of higher harmonics
        decay_factor = 1.0 / (1.0 + i / PHI)
        amplitude = harmonic_amplitude * decay_factor * 0.7  # Scale to avoid clipping
        
        # Add this harmonic to the signal
        audio_data += amplitude * np.sin(2 * np.pi * harmonic_frequency * t)
    
    # Apply overall amplitude envelope based on pattern
    # Map the pattern to an amplitude envelope
    envelope = np.interp(np.linspace(0, 1, num_samples), np.linspace(0, 1, len(pattern_interpolated)), pattern_interpolated)
    
    # Smooth the envelope
    from scipy.ndimage import gaussian_filter1d
    smooth_envelope = gaussian_filter1d(envelope, sigma=sample_rate/100)
    
    # Apply the envelope
    audio_data = audio_data * smooth_envelope
    
    # Normalize to prevent clipping
    max_amplitude = np.max(np.abs(audio_data))
    if max_amplitude > 0:
        audio_data = audio_data / max_amplitude * 0.9
    
    # Apply short fade in/out to avoid clicks
    attack_samples = int(0.01 * sample_rate)  # 10ms attack
    decay_samples = int(0.01 * sample_rate)   # 10ms decay
    audio_data[:attack_samples] *= np.linspace(0, 1, attack_samples)
    audio_data[-decay_samples:] *= np.linspace(1, 0, decay_samples)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, audio_data)
    buf.seek(0)
    
    return buf

def create_bach_inspired_audio(
    data: Union[List[float], Dict[str, List[float]]],
    sample_rate: int = 44100,
    duration: float = 10.0,
    base_frequency: float = 220.0,  # A3 note
):
    """
    Create audio inspired by Bach's compositional techniques.
    Uses counterpoint and mathematical relationships to create structured audio.
    """
    # Handle different data types and extract counterpoint voices
    voices = []
    
    if isinstance(data, dict):
        # Use theme and variations as separate voices
        for name, series in data.items():
            if len(series) > 0:
                # Normalize each voice
                if max(series) != min(series):
                    normalized = [(x - min(series)) / (max(series) - min(series)) for x in series]
                else:
                    normalized = [0.5 for _ in series]
                voices.append(normalized)
    else:
        # Create counterpoint voices from the single data series
        # First voice is the original pattern
        if max(data) != min(data):
            voices.append([(x - min(data)) / (max(data) - min(data)) for x in data])
        else:
            voices.append([0.5 for _ in data])
        
        # Second voice is the inversion
        voices.append([1.0 - x for x in voices[0]])
        
        # Third voice is shifted by golden ratio
        shift = int(len(data) / PHI) % len(data)
        voices.append(voices[0][shift:] + voices[0][:shift])
    
    # Ensure we have at least 3 voices for Bach-like counterpoint
    while len(voices) < 3:
        # Create additional voices as needed
        if len(voices) == 1:
            # Add inversion
            voices.append([1.0 - x for x in voices[0]])
        elif len(voices) == 2:
            # Add third voice as combination
            voices.append([(voices[0][i] + voices[1][i])/2 for i in range(len(voices[0]))])
    
    # Limit to maximum 4 voices for clarity
    voices = voices[:4]
    
    # Calculate total number of samples
    num_samples = int(sample_rate * duration)
    
    # Time array
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    # Bach often used mathematical relationships between voice frequencies
    # Use frequency ratios inspired by just intonation
    frequency_ratios = [1.0, 5.0/4.0, 3.0/2.0, 15.0/8.0][:len(voices)]
    
    # Generate audio
    audio_data = np.zeros(num_samples)
    
    for voice_idx, voice_data in enumerate(voices):
        # Interpolate this voice to match the number of samples
        indices = np.linspace(0, len(voice_data) - 1, num_samples)
        voice_interpolated = np.interp(indices, np.arange(len(voice_data)), voice_data)
        
        # Voice frequency
        voice_freq = base_frequency * frequency_ratios[voice_idx]
        
        # Create segments - Bach often used distinct segments with motivic development
        segment_length = int(num_samples / (1 + voice_idx))  # Different segment lengths for each voice
        num_segments = math.ceil(num_samples / segment_length)
        
        voice_audio = np.zeros(num_samples)
        
        for segment in range(num_segments):
            start = segment * segment_length
            end = min((segment + 1) * segment_length, num_samples)
            segment_duration = (end - start) / sample_rate
            
            # Time array for this segment
            segment_t = np.linspace(0, segment_duration, end - start, endpoint=False)
            
            # Frequency for this segment, modulated by the voice data
            segment_data = voice_interpolated[start:end]
            
            # Various treatments for different segments - inspired by Bach's variations
            if segment % 3 == 0:  # Every third segment
                # Simple sine wave with frequency modulation
                frequency = voice_freq * (1.0 + 0.2 * segment_data)
                phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
                segment_audio = np.sin(phase[:len(segment_t)])
            
            elif segment % 3 == 1:  # Every third segment + 1
                # Harmonic-rich sound (square-ish wave)
                segment_audio = np.sin(2 * np.pi * voice_freq * segment_t)
                segment_audio += 0.3 * np.sin(2 * np.pi * voice_freq * 3 * segment_t)
                segment_audio += 0.15 * np.sin(2 * np.pi * voice_freq * 5 * segment_t)
                segment_audio = np.tanh(2 * segment_audio) * 0.5  # Soft clipping
                
                # Amplitude modulation
                segment_audio = segment_audio * (0.7 + 0.3 * segment_data)
            
            else:  # Remaining segments
                # Arpeggiated pattern - inspired by Bach's broken chord patterns
                arp_freq = voice_freq * np.array([1.0, 5.0/4.0, 3.0/2.0, 2.0])
                arp_len = len(arp_freq)
                arp_rate = 8  # notes per second
                
                segment_audio = np.zeros(len(segment_t))
                for i in range(len(segment_t)):
                    arp_idx = int(segment_t[i] * arp_rate) % arp_len
                    segment_audio[i] = 0.7 * np.sin(2 * np.pi * arp_freq[arp_idx] * segment_t[i])
            
            # Apply envelope
            envelope = np.ones(len(segment_audio))
            attack = int(0.01 * sample_rate)  # 10ms attack
            decay = int(0.01 * sample_rate)   # 10ms decay
            
            if len(envelope) > attack + decay:
                envelope[:attack] = np.linspace(0, 1, attack)
                envelope[-decay:] = np.linspace(1, 0, decay)
            
            segment_audio = segment_audio * envelope
            
            # Add to voice audio
            voice_audio[start:end] = segment_audio
        
        # Add this voice to the overall audio
        # Use golden ratio relationships for voice balancing
        voice_volume = 0.8 / (1 + voice_idx / PHI)
        audio_data += voice_audio * voice_volume
    
    # Normalize to prevent clipping
    max_amplitude = np.max(np.abs(audio_data))
    if max_amplitude > 0:
        audio_data = audio_data / max_amplitude * 0.9
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, audio_data)
    buf.seek(0)
    
    return buf

# Routes with Bach-inspired structure - clear entry, development, and resolution
@router.post("/visualize")
async def visualize_pattern(request: VisualizationRequest):
    """
    Visualize a pattern with specified visualization type.
    Following Bach's principle of making abstract patterns visible.
    """
    pattern_id = request.pattern_id
    viz_type = request.visualization_type
    params = request.parameters
    
    # Load the pattern data
    pattern_path = os.path.join(PATTERNS_DIR, f"{pattern_id}.json")
    
    if not os.path.exists(pattern_path):
        raise HTTPException(
            status_code=404,
            detail=f"Pattern not found: {pattern_id}"
        )
    
    try:
        with open(pattern_path, "r") as f:
            pattern_data = json.load(f)
        
        data = pattern_data["data"]
        pattern_type = pattern_data["pattern_type"]
        
        # Set default title based on pattern information
        default_title = f"{pattern_type.capitalize()} Pattern Visualization"
        title = params.get("title", default_title)
        
        # Extract other parameters
        width = params.get("width", 800)
        height = params.get("height", 600)
        color = params.get("color", "#1f77b4")
        background = params.get("background", "#f8f9fa")
        grid = params.get("grid", True)
        show_points = params.get("show_points", False)
        line_width = params.get("line_width", 1.5)
        
        # Create visualization based on type
        if viz_type == "line":
            buf = create_line_visualization(
                data=data,
                title=title,
                width=width,
                height=height,
                color=color,
                background=background,
                grid=grid,
                show_points=show_points,
                line_width=line_width
            )
        
        elif viz_type == "circle":
            # If data is a dictionary, use the main theme or first item
            if isinstance(data, dict):
                if "theme" in data:
                    circle_data = data["theme"]
                else:
                    circle_data = list(data.values())[0]
            else:
                circle_data = data
            
            buf = create_circle_visualization(
                data=circle_data,
                title=title,
                width=width,
                height=height,
                color=color,
                background=background,
                line_width=line_width
            )
        
        elif viz_type == "spectrogram":
            # If data is a dictionary, use the main theme or first item
            if isinstance(data, dict):
                if "theme" in data:
                    spectro_data = data["theme"]
                else:
                    spectro_data = list(data.values())[0]
            else:
                spectro_data = data
            
            cmap = params.get("cmap", "viridis")
            
            buf = create_spectrogram_visualization(
                data=spectro_data,
                title=title,
                width=width,
                height=height,
                cmap=cmap,
                background=background
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported visualization type: {viz_type}"
            )
        
        # Generate a unique filename for this visualization
        viz_filename = f"{pattern_id}_{viz_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
        viz_path = os.path.join(VISUALIZATIONS_DIR, viz_filename)
        
        # Save the visualization file
        with open(viz_path, "wb") as f:
            f.write(buf.getvalue())
        
        # Return the visualization image
        return StreamingResponse(buf, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sonify")
async def sonify_pattern(request: AudioRequest):
    """
    Convert a pattern to audio with specified audio type.
    Following Bach's principle of translating mathematical patterns to audible form.
    """
    pattern_id = request.pattern_id
    audio_type = request.audio_type
    params = request.parameters
    
    # Load the pattern data
    pattern_path = os.path.join(PATTERNS_DIR, f"{pattern_id}.json")
    
    if not os.path.exists(pattern_path):
        raise HTTPException(
            status_code=404,
            detail=f"Pattern not found: {pattern_id}"
        )
    
    try:
        with open(pattern_path, "r") as f:
            pattern_data = json.load(f)
        
        data = pattern_data["data"]
        pattern_type = pattern_data["pattern_type"]
        
        # Extract parameters
        sample_rate = params.get("sample_rate", 44100)
        duration = params.get("duration", 5.0)
        base_frequency = params.get("base_frequency", 440.0)
        
        # Create audio based on type
        if audio_type == "direct":
            # If data is a dictionary, use the main theme or first item
            if isinstance(data, dict):
                if "theme" in data:
                    audio_data = data["theme"]
                else:
                    audio_data = list(data.values())[0]
            else:
                audio_data = data
            
            buf = create_direct_audio(
                data=audio_data,
                sample_rate=sample_rate,
                duration=duration
            )
        
        elif audio_type == "frequency":
            # If data is a dictionary, use the main theme or first item
            if isinstance(data, dict):
                if "theme" in data:
                    audio_data = data["theme"]
                else:
                    audio_data = list(data.values())[0]
            else:
                audio_data = data
            
            frequency_range = params.get("frequency_range", 1000.0)
            
            buf = create_frequency_modulated_audio(
                data=audio_data,
                sample_rate=sample_rate,
                duration=duration,
                base_frequency=base_frequency,
                frequency_range=frequency_range
            )
        
        elif audio_type == "harmonic":
            buf = create_harmonic_audio(
                data=data,
                sample_rate=sample_rate,
                duration=duration,
                base_frequency=base_frequency
            )
        
        elif audio_type == "bach":
            buf = create_bach_inspired_audio(
                data=data,
                sample_rate=sample_rate,
                duration=duration,
                base_frequency=base_frequency
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio type: {audio_type}"
            )
        
        # Generate a unique filename for this audio
        audio_filename = f"{pattern_id}_{audio_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # Save the audio file
        with open(audio_path, "wb") as f:
            f.write(buf.getvalue())
        
        # Return the audio file
        return StreamingResponse(buf, media_type="audio/wav")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations")
async def list_visualizations():
    """
    List all available visualizations.
    Follows Bach's organizational principle.
    """
    visualizations = []
    
    for filename in os.listdir(VISUALIZATIONS_DIR):
        if filename.endswith(".png"):
            viz_path = f"/static/visualizations/{filename}"
            parts = filename.split("_")
            
            if len(parts) >= 3:
                pattern_id = parts[0]
                viz_type = parts[1]
                
                visualizations.append({
                    "filename": filename,
                    "path": viz_path,
                    "pattern_id": pattern_id,
                    "visualization_type": viz_type,
                    "created": datetime.fromtimestamp(os.path.getctime(
                        os.path.join(VISUALIZATIONS_DIR, filename)
                    )).isoformat()
                })
    
    # Sort by creation time (newest first)
    visualizations.sort(key=lambda x: x["created"], reverse=True)
    
    return {"visualizations": visualizations}

@router.get("/audio")
async def list_audio():
    """
    List all available audio files.
    Follows Bach's organizational principle.
    """
    audio_files = []
    
    for filename in os.listdir(AUDIO_DIR):
        if filename.endswith(".wav"):
            audio_path = f"/static/audio/{filename}"
            parts = filename.split("_")
            
            if len(parts) >= 3:
                pattern_id = parts[0]
                audio_type = parts[1]
                
                audio_files.append({
                    "filename": filename,
                    "path": audio_path,
                    "pattern_id": pattern_id,
                    "audio_type": audio_type,
                    "created": datetime.fromtimestamp(os.path.getctime(
                        os.path.join(AUDIO_DIR, filename)
                    )).isoformat()
                })
    
    # Sort by creation time (newest first)
    audio_files.sort(key=lambda x: x["created"], reverse=True)
    
    return {"audio_files": audio_files}

@router.get("/visualization/{filename}")
async def get_visualization(filename: str = Path(...)):
    """Get a specific visualization by filename"""
    file_path = os.path.join(VISUALIZATIONS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Visualization not found")
    
    return FileResponse(file_path, media_type="image/png")

@router.get("/audio/{filename}")
async def get_audio(filename: str = Path(...)):
    """Get a specific audio file by filename"""
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(file_path, media_type="audio/wav")