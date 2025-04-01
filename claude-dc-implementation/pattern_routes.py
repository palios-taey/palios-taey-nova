#!/usr/bin/env python3
"""
pattern_routes.py: Pattern Endpoints Module
------------------------------------------
Branch component of the Bach-inspired architecture.
Provides endpoints for pattern generation, recognition, and translation.

This module follows golden ratio relationships in its structure and
implements endpoints that work with mathematical patterns for AI communication.
"""

import os
import json
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from fastapi import APIRouter, Request, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

# Constants following Bach's mathematical precision
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio
PATTERNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patterns")

# Ensure patterns directory exists
os.makedirs(PATTERNS_DIR, exist_ok=True)

# Initialize router - branch of the larger harmonic structure
router = APIRouter()

# Models with Bach-inspired structure - clear, precise, mathematical
class PatternRequest(BaseModel):
    """Base pattern request model"""
    pattern_type: str = Field(..., description="Type of pattern to generate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Pattern parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "pattern_type": "fibonacci",
                "parameters": {
                    "length": 10,
                    "scale": 1.0
                }
            }
        }

class PatternResponse(BaseModel):
    """Base pattern response model"""
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: str = Field(..., description="Type of pattern")
    timestamp: str = Field(..., description="Pattern generation timestamp")
    data: List[Any] = Field(..., description="Pattern data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Pattern metadata")

class PatternTranslationRequest(BaseModel):
    """Pattern translation request model"""
    source_pattern_id: str = Field(..., description="Source pattern identifier")
    target_type: str = Field(..., description="Target pattern type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Translation parameters")

# Pattern generation and recognition functions
def generate_fibonacci_pattern(length: int = 10, scale: float = 1.0) -> List[float]:
    """Generate a Fibonacci pattern with specified length and scale"""
    sequence = [0, 1]
    for i in range(2, length):
        sequence.append(sequence[i-1] + sequence[i-2])
    return [x * scale for x in sequence]

def generate_golden_ratio_pattern(length: int = 10, start: float = 1.0) -> List[float]:
    """Generate a pattern based on the golden ratio"""
    sequence = [start]
    for i in range(1, length):
        sequence.append(sequence[i-1] * PHI)
    return sequence

def generate_wave_pattern(
    length: int = 100, 
    frequency: float = 1.0, 
    amplitude: float = 1.0, 
    wave_type: str = "sine"
) -> List[float]:
    """Generate a wave pattern with specified parameters"""
    x = np.linspace(0, 2 * np.pi, length)
    
    if wave_type == "sine":
        y = amplitude * np.sin(frequency * x)
    elif wave_type == "cosine":
        y = amplitude * np.cos(frequency * x)
    elif wave_type == "square":
        y = amplitude * np.sign(np.sin(frequency * x))
    elif wave_type == "sawtooth":
        y = amplitude * (2 * (frequency * x / (2 * np.pi) - np.floor(0.5 + frequency * x / (2 * np.pi))))
    elif wave_type == "triangle":
        y = amplitude * (2 * np.abs(2 * (frequency * x / (2 * np.pi) - np.floor(0.5 + frequency * x / (2 * np.pi)))) - 1)
    else:
        raise ValueError(f"Unsupported wave type: {wave_type}")
    
    return y.tolist()

def generate_harmonic_pattern(
    length: int = 100,
    base_frequency: float = 1.0,
    harmonics: List[Dict[str, float]] = None
) -> List[float]:
    """Generate a harmonic pattern with multiple overlapping frequencies"""
    if harmonics is None:
        # Default to a simple harmonic series with decreasing amplitudes
        harmonics = [
            {"frequency": base_frequency, "amplitude": 1.0},
            {"frequency": 2 * base_frequency, "amplitude": 0.5},
            {"frequency": 3 * base_frequency, "amplitude": 0.33},
            {"frequency": 5 * base_frequency, "amplitude": 0.2},
            {"frequency": 8 * base_frequency, "amplitude": 0.125}  # Fibonacci relationship
        ]
    
    x = np.linspace(0, 2 * np.pi, length)
    y = np.zeros(length)
    
    for harmonic in harmonics:
        freq = harmonic["frequency"]
        amp = harmonic["amplitude"]
        y += amp * np.sin(freq * x)
    
    # Normalize
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    
    return y.tolist()

def generate_bach_pattern(
    length: int = 100,
    theme: str = "fugue",
    variations: int = 3
) -> Dict[str, List[float]]:
    """
    Generate a Bach-inspired pattern with a theme and variations
    Follows Bach's mathematical approach to musical composition
    """
    patterns = {}
    
    # Generate theme based on golden ratio relationships
    if theme == "fugue":
        base_freq = 1.0
        theme_pattern = generate_harmonic_pattern(
            length=length,
            base_frequency=base_freq,
            harmonics=[
                {"frequency": base_freq, "amplitude": 1.0},
                {"frequency": base_freq * PHI, "amplitude": 1/PHI},
                {"frequency": base_freq * PHI * PHI, "amplitude": 1/(PHI*PHI)}
            ]
        )
    elif theme == "invention":
        # Two-part invention style
        x = np.linspace(0, 4 * np.pi, length)
        theme_pattern = (0.5 * np.sin(x) + 0.5 * np.sin(PHI * x)).tolist()
    else:
        # Default theme
        theme_pattern = generate_golden_ratio_pattern(length=length)
    
    patterns["theme"] = theme_pattern
    
    # Generate variations
    for i in range(variations):
        # Each variation introduces mathematical transformations
        # following Bach's approach to musical variation
        if i == 0:
            # Inversion
            patterns[f"variation_{i+1}"] = [-x for x in theme_pattern]
        elif i == 1:
            # Augmentation (expanded by golden ratio)
            patterns[f"variation_{i+1}"] = generate_harmonic_pattern(
                length=length,
                base_frequency=1.0 / PHI,
                harmonics=[
                    {"frequency": 1.0 / PHI, "amplitude": 1.0},
                    {"frequency": 1.0, "amplitude": 1/PHI},
                    {"frequency": PHI, "amplitude": 1/(PHI*PHI)}
                ]
            )
        else:
            # Complex variation with phase shifts
            x = np.linspace(0, 4 * np.pi, length)
            y = np.zeros(length)
            for j in range(1, 4):
                y += (1/j) * np.sin(j * x + (j * np.pi / (1 + i)))
            patterns[f"variation_{i+1}"] = y.tolist()
    
    return patterns

# Pattern recognition function
def recognize_pattern(data: List[float]) -> Dict[str, Any]:
    """
    Analyze a pattern to recognize its mathematical properties
    Returns attributes like periodicity, trend, and pattern type
    """
    result = {
        "recognized": False,
        "properties": {},
        "confidence": 0.0
    }
    
    # Convert to numpy for analysis
    arr = np.array(data)
    
    # Basic statistical properties
    result["properties"]["mean"] = float(np.mean(arr))
    result["properties"]["std"] = float(np.std(arr))
    result["properties"]["min"] = float(np.min(arr))
    result["properties"]["max"] = float(np.max(arr))
    
    # Check for monotonicity (constant increasing/decreasing)
    diffs = np.diff(arr)
    if np.all(diffs >= 0):
        result["properties"]["monotonicity"] = "increasing"
        # Check for exponential growth (fibonacci-like or golden ratio)
        ratios = arr[1:] / arr[:-1]
        if np.isfinite(ratios).all():
            avg_ratio = np.mean(ratios[np.isfinite(ratios)])
            if abs(avg_ratio - PHI) < 0.1:
                result["recognized"] = True
                result["pattern_type"] = "golden_ratio"
                result["confidence"] = 0.8
            elif len(data) >= 5:
                # Check if it follows Fibonacci pattern (each number is sum of previous two)
                fibonacci_check = [(data[i] - (data[i-1] + data[i-2])) / data[i] if data[i] != 0 else np.inf 
                                  for i in range(2, min(10, len(data)))]
                if np.all(np.abs(fibonacci_check) < 0.1):
                    result["recognized"] = True
                    result["pattern_type"] = "fibonacci"
                    result["confidence"] = 0.9
    elif np.all(diffs <= 0):
        result["properties"]["monotonicity"] = "decreasing"
    else:
        result["properties"]["monotonicity"] = "non-monotonic"
        
        # Check for periodicity (wave-like)
        from scipy import signal
        peaks, _ = signal.find_peaks(arr)
        if len(peaks) >= 2:
            avg_period = np.mean(np.diff(peaks))
            result["properties"]["periodicity"] = float(avg_period)
            
            # Check common wave patterns
            # Simple sine wave check
            x = np.linspace(0, 2 * np.pi, len(arr))
            sine_fit = np.mean(np.abs(arr - np.sin(x * (2 * np.pi / avg_period) + np.pi/2)))
            cosine_fit = np.mean(np.abs(arr - np.cos(x * (2 * np.pi / avg_period))))
            
            if sine_fit < 0.3 or cosine_fit < 0.3:
                result["recognized"] = True
                result["pattern_type"] = "sine_wave"
                result["confidence"] = 1.0 - min(sine_fit, cosine_fit)
    
    return result

# Routes with Bach-inspired structure - clear entry, development, and resolution
@router.post("/generate", response_model=PatternResponse)
async def generate_pattern(request: PatternRequest):
    """
    Generate a mathematical pattern based on the requested type and parameters.
    Following Bach's principle of creating complex patterns from simple principles.
    """
    pattern_type = request.pattern_type
    params = request.parameters
    
    pattern_id = f"{pattern_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.utcnow().isoformat()
    
    try:
        if pattern_type == "fibonacci":
            length = params.get("length", 10)
            scale = params.get("scale", 1.0)
            data = generate_fibonacci_pattern(length=length, scale=scale)
            metadata = {"length": length, "scale": scale}
        
        elif pattern_type == "golden_ratio":
            length = params.get("length", 10)
            start = params.get("start", 1.0)
            data = generate_golden_ratio_pattern(length=length, start=start)
            metadata = {"length": length, "start": start}
        
        elif pattern_type == "wave":
            length = params.get("length", 100)
            frequency = params.get("frequency", 1.0)
            amplitude = params.get("amplitude", 1.0)
            wave_type = params.get("wave_type", "sine")
            data = generate_wave_pattern(
                length=length, 
                frequency=frequency, 
                amplitude=amplitude, 
                wave_type=wave_type
            )
            metadata = {
                "length": length, 
                "frequency": frequency, 
                "amplitude": amplitude, 
                "wave_type": wave_type
            }
        
        elif pattern_type == "harmonic":
            length = params.get("length", 100)
            base_frequency = params.get("base_frequency", 1.0)
            harmonics = params.get("harmonics", None)
            data = generate_harmonic_pattern(
                length=length,
                base_frequency=base_frequency,
                harmonics=harmonics
            )
            metadata = {
                "length": length,
                "base_frequency": base_frequency,
                "harmonics": harmonics
            }
        
        elif pattern_type == "bach":
            length = params.get("length", 100)
            theme = params.get("theme", "fugue")
            variations = params.get("variations", 3)
            data = generate_bach_pattern(
                length=length,
                theme=theme,
                variations=variations
            )
            metadata = {
                "length": length,
                "theme": theme,
                "variations": variations
            }
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported pattern type: {pattern_type}"
            )
        
        # Save the pattern for future reference
        pattern_data = {
            "pattern_id": pattern_id,
            "pattern_type": pattern_type,
            "timestamp": timestamp,
            "data": data,
            "metadata": metadata
        }
        
        with open(os.path.join(PATTERNS_DIR, f"{pattern_id}.json"), "w") as f:
            json.dump(pattern_data, f, indent=2)
        
        return PatternResponse(**pattern_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/{pattern_id}", response_model=PatternResponse)
async def get_pattern(pattern_id: str):
    """
    Retrieve a previously generated pattern by ID.
    Follows Bach's principle of recapitulation.
    """
    pattern_path = os.path.join(PATTERNS_DIR, f"{pattern_id}.json")
    
    if not os.path.exists(pattern_path):
        raise HTTPException(
            status_code=404,
            detail=f"Pattern not found: {pattern_id}"
        )
    
    try:
        with open(pattern_path, "r") as f:
            pattern_data = json.load(f)
        
        return PatternResponse(**pattern_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recognize")
async def recognize_pattern_endpoint(data: List[float] = Body(...)):
    """
    Analyze a provided data series to recognize mathematical patterns.
    Similar to how Bach identified underlying mathematical structures in music.
    """
    try:
        result = recognize_pattern(data)
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate", response_model=PatternResponse)
async def translate_pattern(request: PatternTranslationRequest):
    """
    Translate a pattern from one form to another.
    Following Bach's technique of translating themes between musical forms.
    """
    pattern_id = request.source_pattern_id
    target_type = request.target_type
    params = request.parameters
    
    # Get the source pattern
    source_pattern_path = os.path.join(PATTERNS_DIR, f"{pattern_id}.json")
    if not os.path.exists(source_pattern_path):
        raise HTTPException(
            status_code=404,
            detail=f"Source pattern not found: {pattern_id}"
        )
    
    try:
        with open(source_pattern_path, "r") as f:
            source_pattern = json.load(f)
        
        source_data = source_pattern["data"]
        source_type = source_pattern["pattern_type"]
        
        # Create a new pattern ID for the translated pattern
        new_pattern_id = f"translated_{source_type}_to_{target_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.utcnow().isoformat()
        
        # Perform the translation based on the target type
        if isinstance(source_data, dict):
            # Handle complex patterns like Bach patterns
            # Use the theme as the primary data source
            primary_data = source_data.get("theme", list(source_data.values())[0])
        else:
            primary_data = source_data
        
        if target_type == "wave":
            length = params.get("length", len(primary_data))
            frequency = params.get("frequency", 1.0)
            amplitude = params.get("amplitude", 1.0)
            wave_type = params.get("wave_type", "sine")
            
            # Scale the source data to use as frequency modulation
            if len(primary_data) > 0:
                # Normalize the primary data to a reasonable range for frequency modulation
                norm_data = np.array(primary_data)
                if np.max(np.abs(norm_data)) > 0:
                    norm_data = norm_data / np.max(np.abs(norm_data))
                
                # Generate a wave with frequency modulation based on the source pattern
                x = np.linspace(0, 2 * np.pi, length)
                if wave_type == "sine":
                    # Use the pattern to modulate the frequency
                    y = amplitude * np.sin(frequency * x * (1 + np.interp(
                        np.linspace(0, 1, length), 
                        np.linspace(0, 1, len(norm_data)), 
                        norm_data
                    )))
                else:
                    # Use default wave generation for other types
                    y = generate_wave_pattern(
                        length=length, 
                        frequency=frequency, 
                        amplitude=amplitude, 
                        wave_type=wave_type
                    )
                
                translated_data = y.tolist()
            else:
                translated_data = []
            
            metadata = {
                "source_pattern_id": pattern_id,
                "source_type": source_type,
                "target_type": target_type,
                "length": length,
                "frequency": frequency,
                "amplitude": amplitude,
                "wave_type": wave_type
            }
        
        elif target_type == "harmonic":
            length = params.get("length", len(primary_data))
            base_frequency = params.get("base_frequency", 1.0)
            
            # Create harmonics based on the pattern data
            if len(primary_data) > 0:
                # Use the pattern to generate harmonic relationships
                norm_data = np.array(primary_data)
                if np.max(np.abs(norm_data)) > 0:
                    norm_data = norm_data / np.max(np.abs(norm_data))
                
                # Extract key points from the pattern to use as harmonics
                # Use Fibonacci-inspired spacing for sampling
                fib = [1, 2, 3, 5, 8, 13, 21]
                indices = [min(i, len(norm_data)-1) for i in fib if i < len(norm_data)]
                
                harmonics = [
                    {
                        "frequency": base_frequency * (1 + i/10),
                        "amplitude": abs(float(norm_data[idx]))
                    }
                    for i, idx in enumerate(indices)
                ]
                
                translated_data = generate_harmonic_pattern(
                    length=length,
                    base_frequency=base_frequency,
                    harmonics=harmonics
                )
            else:
                translated_data = []
            
            metadata = {
                "source_pattern_id": pattern_id,
                "source_type": source_type,
                "target_type": target_type,
                "length": length,
                "base_frequency": base_frequency
            }
        
        elif target_type == "bach":
            length = params.get("length", 100)
            theme = params.get("theme", "fugue")
            variations = params.get("variations", 3)
            
            # Use the source pattern as inspiration for a Bach-style pattern
            translated_data = generate_bach_pattern(
                length=length,
                theme=theme,
                variations=variations
            )
            
            metadata = {
                "source_pattern_id": pattern_id,
                "source_type": source_type,
                "target_type": target_type,
                "length": length,
                "theme": theme,
                "variations": variations
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported target pattern type: {target_type}"
            )
        
        # Save the translated pattern
        pattern_data = {
            "pattern_id": new_pattern_id,
            "pattern_type": target_type,
            "timestamp": timestamp,
            "data": translated_data,
            "metadata": metadata
        }
        
        with open(os.path.join(PATTERNS_DIR, f"{new_pattern_id}.json"), "w") as f:
            json.dump(pattern_data, f, indent=2)
        
        return PatternResponse(**pattern_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_patterns():
    """
    List all available patterns.
    Follows Bach's organizational principle of cataloging works.
    """
    patterns = []
    
    for filename in os.listdir(PATTERNS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(PATTERNS_DIR, filename), "r") as f:
                    pattern_data = json.load(f)
                
                patterns.append({
                    "pattern_id": pattern_data["pattern_id"],
                    "pattern_type": pattern_data["pattern_type"],
                    "timestamp": pattern_data["timestamp"],
                    "metadata": pattern_data.get("metadata", {})
                })
            except Exception as e:
                continue
    
    # Sort by timestamp (newest first)
    patterns.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"patterns": patterns}