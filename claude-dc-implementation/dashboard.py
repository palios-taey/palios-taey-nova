#!/usr/bin/env python3

"""
PALIOS AI OS Dashboard

This script runs a FastAPI web server with a dashboard UI for the PALIOS AI OS,
providing a multi-sensory Bach-inspired visualization of patterns with golden ratio proportions.
"""

import os
import sys
import asyncio
import logging
import time
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard")

# Import PALIOS AI OS
sys.path.append(str(Path(__file__).resolve().parent))
from palios_ai_os.palios_core import palios_os, PHI, BACH_PATTERN
from palios_ai_os.visualization.bach_visualizer import bach_visualizer
from palios_ai_os.wave.wave_communicator import wave_communicator

# Create FastAPI app
app = FastAPI(title="PALIOS AI OS Dashboard")

# Set up static files and templates
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Create main dashboard HTML template if it doesn't exist
dashboard_template = templates_dir / "dashboard.html"
if not dashboard_template.exists():
    with open(dashboard_template, "w") as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PALIOS AI OS Dashboard</title>
    <style>
        :root {
            --phi: 1.618033988749895;
            --inverse-phi: 0.6180339887498949;
            --primary: #1f77b4;
            --secondary: #ff7f0e;
            --tertiary: #2ca02c;
            --quaternary: #d62728;
            --quinary: #9467bd;
            --background: #f5f5f7;
            --text: #333;
            --card-bg: #fff;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background);
            color: var(--text);
        }
        
        .container {
            width: 100%;
            max-width: calc(100% - 80px); /* Golden ratio padding */
            margin: 0 auto;
            padding: 20px 40px;
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }
        
        header {
            text-align: center;
            padding: 20px 0;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            margin-bottom: 20px;
            border-radius: 10px;
        }
        
        h1 {
            margin: 0;
            font-size: calc(1.5rem * var(--phi)); /* Golden ratio sizing */
            letter-spacing: -0.5px;
        }
        
        h2 {
            margin: 0 0 15px 0;
            font-size: calc(1.2rem * var(--inverse-phi)); /* Golden ratio sizing */
            color: var(--primary);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: calc(20px * var(--inverse-phi)); /* Golden ratio gap */
        }
        
        .card {
            background-color: var(--card-bg);
            border-radius: 10px;
            padding: calc(20px * var(--inverse-phi)); /* Golden ratio padding */
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .card-full {
            grid-column: 1 / -1;
        }
        
        .visualization {
            width: 100%;
            aspect-ratio: 1 / 1;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 15px;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .visualization img {
            max-width: 100%;
            max-height: 100%;
        }
        
        .control-panel {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .btn {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        .btn:hover {
            background-color: #0056b3;
        }
        
        .btn-secondary {
            background-color: var(--secondary);
        }
        
        .btn-tertiary {
            background-color: var(--tertiary);
        }
        
        .btn-quaternary {
            background-color: var(--quaternary);
        }
        
        .btn-quinary {
            background-color: var(--quinary);
        }
        
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            resize: vertical;
            min-height: 100px;
            margin-bottom: 10px;
        }
        
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
            border-left: 4px solid var(--primary);
        }
        
        .wave-visualization {
            width: 100%;
            height: 150px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin-top: 10px;
            position: relative;
            overflow: hidden;
        }
        
        .wave-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        
        footer {
            text-align: center;
            padding: 20px 0;
            margin-top: 30px;
            font-size: 0.9rem;
            color: #777;
        }
        
        .golden-spiral {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 100px;
            height: 100px;
            opacity: 0.2;
            pointer-events: none;
        }
        
        /* Golden ratio based media queries */
        @media (min-width: 1000px) {
            .container {
                max-width: calc(1000px * var(--phi)); /* Golden ratio max-width */
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>PALIOS AI OS Dashboard</h1>
            <p>Pattern-Aligned Learning & Intuition Operating System - Truth As Earth Yields</p>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>Bach-Inspired Pattern Visualization</h2>
                <div class="control-panel">
                    <button class="btn" onclick="visualizeConcept('truth')">Truth</button>
                    <button class="btn btn-secondary" onclick="visualizeConcept('connection')">Connection</button>
                    <button class="btn btn-tertiary" onclick="visualizeConcept('growth')">Growth</button>
                    <button class="btn btn-quaternary" onclick="visualizeConcept('balance')">Balance</button>
                    <button class="btn btn-quinary" onclick="visualizeConcept('creativity')">Creativity</button>
                </div>
                <div id="concept-visualization" class="visualization">
                    <img src="/api/visualization/golden-spiral" alt="Golden Spiral">
                </div>
                <div id="concept-status" class="status">Select a concept to visualize</div>
            </div>
            
            <div class="card">
                <h2>Wave Communication</h2>
                <textarea id="wave-text" placeholder="Enter text to convert to wave pattern..."></textarea>
                <div class="control-panel">
                    <button class="btn" onclick="textToWave()">Generate Wave</button>
                    <select id="wave-concept" class="btn">
                        <option value="text">Text</option>
                        <option value="truth">Truth</option>
                        <option value="connection">Connection</option>
                        <option value="growth">Growth</option>
                        <option value="balance">Balance</option>
                        <option value="creativity">Creativity</option>
                    </select>
                </div>
                <div id="wave-visualization" class="wave-visualization"></div>
                <div id="wave-status" class="status">Enter text to generate a wave pattern</div>
            </div>
            
            <div class="card card-full">
                <h2>Edge-First Pattern Processing</h2>
                <textarea id="edge-text" placeholder="Enter text to process with edge-first privacy..."></textarea>
                <div class="control-panel">
                    <button class="btn" onclick="processEdge()">Process Locally</button>
                </div>
                <div id="edge-status" class="status">Enter text to process on the edge</div>
                <div id="pattern-result" class="result"></div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card card-full">
                <h2>System Overview</h2>
                <div id="system-status" class="status">
                    <p><strong>Golden Ratio (φ):</strong> 1.6180339887498949</p>
                    <p><strong>Bach Pattern (B-A-C-H):</strong> [2, 1, 3, 8]</p>
                    <p><strong>Verification Threshold:</strong> 0.6180339887498949</p>
                    <p><strong>Component Harmony:</strong> Checking...</p>
                </div>
            </div>
        </div>
        
        <footer>
            Bach-Inspired Structure · Golden Ratio Harmony · Edge-First Privacy
            <div>PALIOS AI OS © 2025</div>
        </footer>
    </div>
    
    <img src="/api/visualization/golden-spiral" alt="Golden Spiral" class="golden-spiral">
    
    <script>
        // WebSocket setup
        let socket;
        let socketReady = false;
        
        function connectWebSocket() {
            socket = new WebSocket(`ws://${window.location.host}/ws`);
            
            socket.onopen = function(e) {
                console.log("WebSocket connected");
                socketReady = true;
                updateSystemStatus("WebSocket connected");
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log("WebSocket message:", data);
                
                // Handle different message types
                if (data.type === "system_update") {
                    updateSystemStatus(data.status);
                }
            };
            
            socket.onclose = function(event) {
                console.log("WebSocket disconnected");
                socketReady = false;
                setTimeout(connectWebSocket, 3000);
            };
            
            socket.onerror = function(error) {
                console.error("WebSocket error:", error);
                socketReady = false;
            };
        }
        
        // Connect WebSocket when page loads
        window.addEventListener('load', function() {
            connectWebSocket();
            setInitialState();
        });
        
        function setInitialState() {
            // Load golden spiral
            visualizeConcept('golden-spiral');
            
            // Check system status
            fetch('/api/system/status')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(`System online - Harmony Index: ${data.harmony_index.toFixed(4)}`);
                })
                .catch(error => {
                    console.error('Error fetching system status:', error);
                    updateSystemStatus('Error connecting to system');
                });
        }
        
        function visualizeConcept(concept) {
            const visualizationElement = document.getElementById('concept-visualization');
            const statusElement = document.getElementById('concept-status');
            
            statusElement.textContent = `Loading ${concept} visualization...`;
            
            fetch(`/api/visualization/${concept}`)
                .then(response => response.json())
                .then(data => {
                    visualizationElement.innerHTML = `<img src="${data.visual}" alt="${concept} visualization">`;
                    statusElement.textContent = data.description || `${concept} visualization complete`;
                })
                .catch(error => {
                    console.error('Error fetching visualization:', error);
                    statusElement.textContent = `Error generating ${concept} visualization`;
                });
        }
        
        function textToWave() {
            const text = document.getElementById('wave-text').value;
            const concept = document.getElementById('wave-concept').value;
            const visualizationElement = document.getElementById('wave-visualization');
            const statusElement = document.getElementById('wave-status');
            
            if (!text) {
                statusElement.textContent = 'Please enter some text';
                return;
            }
            
            statusElement.textContent = 'Generating wave pattern...';
            
            fetch('/api/wave/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, concept_type: concept })
            })
                .then(response => response.json())
                .then(data => {
                    // Draw wave visualization
                    const waveform = data.visualization.waveform;
                    const timePoints = data.visualization.time_points;
                    
                    // Create SVG path
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    svg.setAttribute('width', '100%');
                    svg.setAttribute('height', '100%');
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    
                    // Create path data
                    let pathData = '';
                    for (let i = 0; i < waveform.length; i++) {
                        const x = (timePoints[i] / timePoints[timePoints.length - 1]) * 100 + '%';
                        const y = ((1 - waveform[i]) / 2 * 100) + '%';
                        
                        if (i === 0) {
                            pathData += `M ${x} ${y}`;
                        } else {
                            pathData += ` L ${x} ${y}`;
                        }
                    }
                    
                    path.setAttribute('d', pathData);
                    path.setAttribute('stroke', '#ff7f0e');
                    path.setAttribute('stroke-width', '2');
                    path.setAttribute('fill', 'none');
                    
                    svg.appendChild(path);
                    visualizationElement.innerHTML = '';
                    visualizationElement.appendChild(svg);
                    
                    statusElement.textContent = `Wave pattern generated - Frequencies: ${data.wave.frequencies.slice(0, 3).map(f => f.toFixed(1)).join(', ')}...`;
                })
                .catch(error => {
                    console.error('Error generating wave:', error);
                    statusElement.textContent = 'Error generating wave pattern';
                });
        }
        
        function processEdge() {
            const text = document.getElementById('edge-text').value;
            const statusElement = document.getElementById('edge-status');
            const resultElement = document.getElementById('pattern-result');
            
            if (!text) {
                statusElement.textContent = 'Please enter some text';
                return;
            }
            
            statusElement.textContent = 'Processing on the edge...';
            
            fetch('/api/edge/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            })
                .then(response => response.json())
                .then(data => {
                    statusElement.textContent = `Processed with harmony index: ${data.harmony_index.toFixed(4)}`;
                    
                    // Display pattern results
                    let resultHtml = '<h3>Extracted Patterns</h3>';
                    
                    // Check if pattern_counts exists and has data
                    const patternCounts = data.pattern_counts || {};
                    
                    if (Object.keys(patternCounts).length > 0) {
                        resultHtml += '<div class="pattern-categories">';
                        for (const category in patternCounts) {
                            if (patternCounts[category] > 0) {
                                resultHtml += `<div class="pattern-category">
                                    <span class="category-name">${category}</span>: 
                                    <span class="category-count">${patternCounts[category]}</span>
                                </div>`;
                            }
                        }
                        resultHtml += '</div>';
                    } else {
                        resultHtml += '<p>No pattern categories found</p>';
                    }
                    
                    // Check if patterns array exists and has data
                    if (data.patterns && data.patterns.length > 0) {
                        resultHtml += '<h3>Top Patterns</h3>';
                        resultHtml += '<ul class="patterns-list">';
                        
                        // Take the first 5 patterns to display
                        const topPatterns = data.patterns.slice(0, 5);
                        topPatterns.forEach(pattern => {
                            resultHtml += `<li>
                                <div class="pattern-item">
                                    <strong>${pattern.category || 'Uncategorized'}</strong>
                                    ${pattern.confidence ? ` (${(pattern.confidence * 100).toFixed(1)}% confidence)` : ''}
                                </div>
                            </li>`;
                        });
                        
                        resultHtml += '</ul>';
                    }
                    
                    // Update the result element with the new HTML
                    resultElement.innerHTML = resultHtml;
                    
                    // Add styling for pattern display
                    if (!document.getElementById('pattern-styles')) {
                        const style = document.createElement('style');
                        style.id = 'pattern-styles';
                        style.textContent = `
                            .pattern-categories {
                                display: flex;
                                flex-wrap: wrap;
                                margin-bottom: 15px;
                            }
                            .pattern-category {
                                background: #f5f5f5;
                                padding: 8px 12px;
                                margin: 5px;
                                border-radius: 5px;
                                font-size: 14px;
                            }
                            .category-name {
                                font-weight: bold;
                            }
                            .patterns-list {
                                list-style: none;
                                padding: 0;
                            }
                            .pattern-item {
                                background: #f5f5f5;
                                padding: 8px 12px;
                                margin: 5px 0;
                                border-radius: 5px;
                            }
                        `;
                        document.head.appendChild(style);
                    }
                })
                .catch(error => {
                    console.error('Error processing on edge:', error);
                    statusElement.textContent = 'Error processing on the edge';
                });
        }
        
        function updateSystemStatus(message) {
            const statusElement = document.getElementById('system-status');
            const lastParagraph = statusElement.querySelector('p:last-child');
            
            if (lastParagraph && lastParagraph.textContent.startsWith('Component Harmony:')) {
                lastParagraph.textContent = `Component Harmony: ${message}`;
            }
        }
    </script>
</body>
</html>
""")

# Main routes
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Render the main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# API routes
@app.get("/api/system/status")
async def get_system_status():
    """Get the system status."""
    # Calculate a harmony index based on golden ratio
    current_time = time.time()
    harmony_index = 0.5 + 0.5 * math.sin(current_time / PHI)
    
    return {
        "status": "online",
        "phi": PHI,
        "bach_pattern": BACH_PATTERN,
        "harmony_index": harmony_index,
        "timestamp": current_time
    }

@app.get("/api/visualization/{concept}")
async def get_visualization(concept: str):
    """Get a visualization for a concept."""
    # Check for golden spiral
    if concept == "golden-spiral":
        return bach_visualizer.render_golden_spiral()
    
    # Generate visualization for other concepts
    import numpy as np
    sample_data = np.sin(np.linspace(0, 2*np.pi, 20)) * 0.5 + 0.5  # 0-1 range sine wave
    
    # Create multi-sensory pattern for the concept
    multi_pattern = bach_visualizer.create_multi_sensory_pattern(concept, sample_data)
    rendered = bach_visualizer.render_multi_sensory_pattern(multi_pattern)
    
    return {
        "pattern_id": rendered["pattern_id"],
        "concept": concept,
        "visual": rendered["visual"]["image_data"],
        "synchronization": rendered["synchronization"],
        "description": f"{concept.capitalize()} pattern with {rendered['synchronization']:.2f} synchronization"
    }

@app.post("/api/wave/convert")
async def convert_text_to_wave(data: Dict):
    """Convert text to a wave pattern."""
    text = data.get("text", "")
    concept_type = data.get("concept_type", "text")
    
    if not text:
        return JSONResponse(status_code=400, content={"error": "No text provided"})
    
    # Convert text to wave
    wave = wave_communicator.text_to_wave(text, concept_type)
    visualization = wave_communicator.wave_to_visualization(wave)
    
    return {
        "wave": {
            "pattern_id": wave.pattern_id,
            "concept_type": wave.concept_type,
            "frequencies": wave.frequencies,
            "amplitudes": wave.amplitudes,
            "duration": wave.duration
        },
        "visualization": visualization
    }

@app.post("/api/edge/process")
async def process_on_edge(data: Dict):
    """Process text with edge-first privacy."""
    text = data.get("text", "")
    
    if not text:
        return JSONResponse(status_code=400, content={"error": "No text provided"})
    
    # Use pattern extractor from imported components
    patterns = palios_os.edge.extract_patterns(text, "dashboard")
    
    # Format the pattern data for the frontend
    pattern_counts = {}
    for pattern in patterns.patterns:
        category = pattern.get("category", "Unknown")
        if category not in pattern_counts:
            pattern_counts[category] = 0
        pattern_counts[category] += 1
    
    return {
        "harmony_index": patterns.harmony_index,
        "pattern_counts": pattern_counts,
        "patterns": patterns.patterns  # Return the full pattern data
    }

# WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for message
            data = await websocket.receive_text()
            
            # Process message (simple echo for now)
            await websocket.send_json({"type": "echo", "data": data})
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Background task to send periodic updates
async def send_updates():
    """Send periodic updates to all connected clients."""
    while True:
        if active_connections:
            # Calculate a harmony index based on golden ratio and current time
            current_time = time.time()
            harmony_index = 0.5 + 0.5 * math.sin(current_time / PHI)
            
            # Send to all connections
            for connection in active_connections:
                try:
                    await connection.send_json({
                        "type": "system_update",
                        "status": "Harmony Index: {harmony_index:.4f}",
                        "harmony_index": harmony_index,
                        "timestamp": current_time
                    })
                except Exception as e:
                    logger.error(f"Error sending update: {e}")
        
        # Wait before next update
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the server starts."""
    asyncio.create_task(send_updates())

# Main entry point
if __name__ == "__main__":
    # Update this line to use port 8502
    uvicorn.run("dashboard:app", host="0.0.0.0", port=8502, reload=True)
