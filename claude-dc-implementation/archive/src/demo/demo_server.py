#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Demo Server
-------------------------------
This module implements a FastAPI server for the live demonstration
of the Conductor Framework.
"""

import os
import sys
import json
import logging
import time
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import utilities
from src.processor.transcript_processor import TranscriptProcessor
from src.processor.transcript_loader import TranscriptLoader
from src.processor.cloud_storage import list_stored_patterns, load_transcript_patterns
from src.models.pattern_model import PatternModel
from src.utils.secrets import get_gcp_project_id, get_gcp_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo_server")

# Create the FastAPI app
app = FastAPI(
    title="Conductor Framework Demo",
    description="Live demonstration of the Conductor Framework",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pattern model singleton
pattern_model = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, data: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(data)

# Create connection manager
manager = ConnectionManager()

# Routes
@app.get("/")
async def root():
    """Root endpoint for the demo server."""
    return {
        "message": "Conductor Framework Demo Server",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/patterns")
async def get_patterns():
    """Get all patterns from the Conductor Framework."""
    # Get patterns from local file
    pattern_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns/pattern_report.json"
    
    if os.path.exists(pattern_file):
        with open(pattern_file, 'r') as f:
            patterns = json.load(f)
        
        return patterns
    else:
        # Try to get patterns from cloud storage
        stored_patterns = list_stored_patterns()
        
        if stored_patterns:
            # Get the most recent pattern
            most_recent = max(stored_patterns, key=lambda p: p.get("timestamp", 0))
            
            # Load the pattern
            pattern = load_transcript_patterns(most_recent.get("storage_path"))
            
            if pattern:
                return pattern
        
        # No patterns found
        raise HTTPException(status_code=404, detail="No patterns found")

@app.get("/pattern/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get a specific pattern by ID."""
    # Get patterns from local file
    pattern_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns/pattern_report.json"
    
    if os.path.exists(pattern_file):
        with open(pattern_file, 'r') as f:
            patterns = json.load(f)
        
        # Check if the pattern exists
        if "patterns" in patterns and pattern_id in patterns["patterns"]:
            return patterns["patterns"][pattern_id]
    
    # Try to get pattern from cloud storage
    stored_patterns = list_stored_patterns()
    
    for stored_pattern in stored_patterns:
        if stored_pattern.get("id") == pattern_id:
            # Load the pattern
            pattern = load_transcript_patterns(stored_pattern.get("storage_path"))
            
            if pattern:
                return pattern
    
    # Pattern not found
    raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")

@app.get("/visualization")
async def get_visualization():
    """Get visualization data for patterns."""
    # Get visualization data from local file
    viz_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/visualization_data.json"
    
    if os.path.exists(viz_file):
        with open(viz_file, 'r') as f:
            viz_data = json.load(f)
        
        return viz_data
    
    # Visualization data not found
    raise HTTPException(status_code=404, detail="Visualization data not found")

@app.get("/audio/{pattern_type}")
async def get_audio(pattern_type: str, confidence: float = 0.8):
    """
    Generate audio representation of a pattern.
    
    Args:
        pattern_type: Type of pattern to sonify
        confidence: Confidence value of the pattern (0.0 to 1.0)
    
    Returns:
        Audio file in WAV format
    """
    global pattern_model
    
    # Initialize pattern model if needed
    if pattern_model is None:
        pattern_model = PatternModel()
    
    try:
        # Generate a pseudo-embedding based on the pattern type and confidence
        pattern_index = hash(pattern_type) % 1000  # Get a consistent hash value
        np.random.seed(pattern_index)
        
        # Generate a random embedding
        embedding = np.random.rand(21) * 2 - 1  # 21-dimensional embedding in [-1, 1]
        
        # Adjust the embedding based on confidence (higher confidence = more defined pattern)
        embedding = embedding * confidence
        
        # Get audio parameters
        audio_params = pattern_model.generate_audio_parameters(embedding)
        
        # Generate audio using librosa
        import librosa
        import soundfile as sf
        
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
        temp_file = f"/tmp/pattern_{pattern_type}_{int(confidence * 100)}.wav"
        sf.write(temp_file, y, sr)
        
        # Return the audio file
        return FileResponse(
            temp_file,
            media_type="audio/wav",
            filename=f"pattern_{pattern_type}.wav"
        )
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")

@app.get("/image/{pattern_type}")
async def get_image(pattern_type: str, confidence: float = 0.8):
    """
    Generate visual representation of a pattern.
    
    Args:
        pattern_type: Type of pattern to visualize
        confidence: Confidence value of the pattern (0.0 to 1.0)
    
    Returns:
        Image file in PNG format
    """
    global pattern_model
    
    # Initialize pattern model if needed
    if pattern_model is None:
        pattern_model = PatternModel()
    
    try:
        # Generate a pseudo-embedding based on the pattern type and confidence
        pattern_index = hash(pattern_type) % 1000
        np.random.seed(pattern_index)
        
        # Generate a random embedding
        embedding = np.random.rand(21) * 2 - 1  # 21-dimensional embedding in [-1, 1]
        
        # Adjust the embedding based on confidence
        embedding = embedding * confidence
        
        # Get visual parameters
        visual_params = pattern_model.pattern_to_visual_parameters(embedding.reshape(1, -1))
        
        # Create image with golden ratio proportions
        from PIL import Image, ImageDraw
        
        # Get the golden ratio from the model
        golden_ratio = pattern_model.golden_ratio
        
        width = 800
        height = int(width / golden_ratio)
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw golden ratio grid
        sections = visual_params["proportions"]["golden_sections"]
        for section in sections:
            x = int(width * section / 100)
            draw.line([(x, 0), (x, height)], fill=(200, 200, 200, 100), width=1)
            
            y = int(height * section / 100)
            draw.line([(0, y), (width, y)], fill=(200, 200, 200, 100), width=1)
        
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
        
        # Save to a temporary file
        temp_file = f"/tmp/pattern_{pattern_type}_{int(confidence * 100)}.png"
        img.save(temp_file, format="PNG")
        
        # Return the image file
        return FileResponse(
            temp_file,
            media_type="image/png",
            filename=f"pattern_{pattern_type}.png"
        )
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Process the received data
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "request_patterns":
                    # Get patterns from local file
                    pattern_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/patterns/pattern_report.json"
                    
                    if os.path.exists(pattern_file):
                        with open(pattern_file, 'r') as f:
                            patterns = json.load(f)
                        
                        await websocket.send_json({"type": "patterns", "data": patterns})
                    else:
                        await websocket.send_json({"type": "error", "message": "No patterns found"})
                else:
                    await websocket.send_json({"type": "error", "message": "Unknown message type"})
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/demo", response_class=HTMLResponse)
async def get_demo():
    """Get the demo HTML page."""
    # Read the demo HTML file
    demo_file = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/src/demo/static/index.html"
    
    if os.path.exists(demo_file):
        with open(demo_file, 'r') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    # Demo file not found
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Conductor Framework Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            
            h1 {
                color: #333;
                text-align: center;
            }
            
            p {
                color: #666;
                text-align: center;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Conductor Framework Demo</h1>
            <p>Demo HTML file not found. Please create a static HTML file for the demo.</p>
        </div>
    </body>
    </html>
    """)

# Create static directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)