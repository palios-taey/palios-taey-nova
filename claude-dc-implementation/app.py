import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Optional
import json
import math
import time
from pathlib import Path

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from core.conductor import Conductor, PHI
from harmony.orchestrator import HarmonyOrchestrator
from wave.communicator import WaveCommunicator
from patterns.extractor import PatternExtractor
from edge.processor import EdgeProcessor
from bridge.communicator import AICommunicator
from visualization.multi_sensory import MultiSensoryVisualizer

# Initialize our core orchestrator
orchestrator = HarmonyOrchestrator()
conductor = Conductor()
visualizer = MultiSensoryVisualizer()

# Create FastAPI app
app = FastAPI(
    title="The Conductor",
    description="Bach-inspired AI orchestration system",
    version="1.0.0"
)

# Mount static files directory
try:
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    print(f"Warning: Could not mount static files directory: {e}")
    templates = None

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Render the main dashboard page."""
    if templates:
        return templates.TemplateResponse(
            "dashboard.html", 
            {"request": request, "phi": PHI}
        )
    else:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>The Conductor</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
                pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; overflow: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>The Conductor</h1>
                <p>Welcome to The Conductor dashboard. This is a placeholder since template rendering is not available.</p>
                <p>Golden Ratio (φ): {PHI}</p>
                <p>Start building your experience by making API calls to the available endpoints.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    client_id = f"client_{len(active_connections) + 1}"
    active_connections[client_id] = websocket
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                # Parse JSON
                json_data = json.loads(data)
                
                # Process based on message type
                if json_data.get("type") == "process_text":
                    text = json_data.get("text", "")
                    if text:
                        result = await orchestrator.process_text(text, "websocket")
                        await websocket.send_json({
                            "type": "process_result", 
                            "data": result
                        })
                
                elif json_data.get("type") == "generate_visual":
                    concept = json_data.get("concept", "truth")
                    result = await orchestrator.generate_multi_sensory_pattern(concept)
                    await websocket.send_json({
                        "type": "visualization_result", 
                        "data": result
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error", 
                        "message": "Unknown message type"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error", 
                    "message": "Invalid JSON format"
                })
            
            except Exception as e:
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Error processing request: {str(e)}"
                })
    
    except WebSocketDisconnect:
        # Remove disconnected client
        del active_connections[client_id]

# Pattern extraction endpoint
@app.post("/patterns/extract")
async def extract_patterns(request: Request):
    """Extract patterns from text."""
    try:
        data = await request.json()
        text = data.get("text", "")
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "No text provided"}
            )
        
        # Process text through orchestrator
        result = await orchestrator.process_text(text, "api")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error extracting patterns: {str(e)}"}
        )

# Wave communication endpoint
@app.post("/wave/communicate")
async def wave_communicate(request: Request):
    """Process text into wave patterns."""
    try:
        data = await request.json()
        text = data.get("text", "")
        emotion = data.get("emotion", "neutral")
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "No text provided"}
            )
        
        # Convert text to wave pattern
        wave = WaveCommunicator().text_to_wave(text, emotion)
        
        # Generate visualization
        visualization = WaveCommunicator().wave_to_visualization(wave)
        
        # Generate audio parameters
        audio = WaveCommunicator().wave_to_audio(wave)
        
        return JSONResponse(content={
            "wave": {
                "pattern_id": wave.pattern_id,
                "frequencies": wave.frequencies,
                "amplitudes": wave.amplitudes if not isinstance(wave.amplitudes, list) else wave.amplitudes[:5],
                "phases": wave.phases[:5] if isinstance(wave.phases, list) else [wave.phases],
                "duration": wave.duration
            },
            "visualization": {
                "time_points": visualization["time_points"][:20],  # Limit for response size
                "waveform": visualization["waveform"][:20]  # Limit for response size
            },
            "audio": {
                "sample_rate": audio["sample_rate"],
                "frequencies": audio["frequencies"],
                "duration": audio["duration"]
            }
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing wave communication: {str(e)}"}
        )

# AI bridge endpoints
@app.post("/bridge/claude-to-grok")
async def claude_to_grok(request: Request):
    """Bridge communication from Claude to Grok."""
    try:
        data = await request.json()
        content = data.get("content", "")
        topic = data.get("topic", "General")
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"error": "No content provided"}
            )
        
        # Process through orchestrator
        result = await orchestrator.communicate_between_models("claude", "grok", content, topic)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error in claude-to-grok bridge: {str(e)}"}
        )

@app.post("/bridge/grok-to-claude")
async def grok_to_claude(request: Request):
    """Bridge communication from Grok to Claude."""
    try:
        data = await request.json()
        content = data.get("content", "")
        topic = data.get("topic", "General")
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"error": "No content provided"}
            )
        
        # Process through orchestrator
        result = await orchestrator.communicate_between_models("grok", "claude", content, topic)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error in grok-to-claude bridge: {str(e)}"}
        )

# Edge processing endpoint
@app.post("/edge/process")
async def edge_process(request: Request):
    """Process data with edge-first privacy approach."""
    try:
        data = await request.json()
        sensitive_data = data.get("sensitive_data", {})
        
        if not sensitive_data:
            return JSONResponse(
                status_code=400,
                content={"error": "No sensitive data provided"}
            )
        
        # Process with edge-first approach
        result = await orchestrator.process_with_edge_privacy(sensitive_data)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error in edge processing: {str(e)}"}
        )

# Visualization endpoints
@app.get("/visualization/audio")
async def get_audio_pattern(request: Request):
    """Generate audio pattern representation."""
    try:
        pattern_type = request.query_params.get("pattern_type", "truth")
        
        # Create sample data following golden ratio intervals
        data = [0.5 + 0.5 * math.sin(i * PHI) for i in range(8)]
        
        # Create audio pattern
        audio_pattern = visualizer.create_audio_pattern(pattern_type, data)
        
        # Generate audio parameters
        result = visualizer.generate_audio_parameters(audio_pattern)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating audio pattern: {str(e)}"}
        )

@app.get("/visualization/visual")
async def get_visual_pattern(request: Request):
    """Generate visual pattern representation."""
    try:
        pattern_type = request.query_params.get("pattern_type", "truth")
        
        # Create sample data following golden ratio intervals
        data = [0.5 + 0.5 * math.sin(i * PHI) for i in range(8)]
        
        # Create visual pattern
        if pattern_type == "spiral":
            visual_pattern = visualizer.create_golden_spiral()
        else:
            visual_pattern = visualizer.create_pattern_visualization(pattern_type, data)
        
        # Render visualization
        result = visualizer.render_visualization(visual_pattern)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating visual pattern: {str(e)}"}
        )

# Multi-sensory pattern generation
@app.post("/generate/multi-sensory")
async def generate_multi_sensory(request: Request):
    """Generate multi-sensory representation of a concept."""
    try:
        data = await request.json()
        concept = data.get("concept", "truth")
        
        # Generate through orchestrator
        result = await orchestrator.generate_multi_sensory_pattern(concept)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating multi-sensory pattern: {str(e)}"}
        )

# Webhook communication
@app.post("/webhook/deploy")
async def webhook_deploy(request: Request):
    """Send deployment operations to webhook."""
    try:
        data = await request.json()
        operation = data.get("operation")
        
        if not operation:
            return JSONResponse(
                status_code=400,
                content={"error": "No operation specified"}
            )
        
        # Remove operation from kwargs
        kwargs = {k: v for k, v in data.items() if k != "operation"}
        
        # Send to webhook
        result = await orchestrator.webhook_deploy(operation, **kwargs)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error in webhook deployment: {str(e)}"}
        )

# Create necessary directories for local storage
os.makedirs("edge/local_storage", exist_ok=True)

# Save the API keys
def save_secrets():
    try:
        with open('palios-taey-secrets.json', 'w') as f:
            secrets_data = {
                # paste 'palios-taey-secrets.json' content here
            json.dump(secrets_data, f, indent=2)
        print("Saved secrets to palios-taey-secrets.json")
    except Exception as e:
        print(f"Error saving secrets: {e}")

# Main entry point
if __name__ == "__main__":
    # Save secrets on startup
    save_secrets()
    
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    # Create a simple HTML template
    with open("templates/dashboard.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>The Conductor Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: #333; color: white; padding: 20px; text-align: center; }
        .golden-ratio { font-size: 1.618em; margin-left: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: white; border-radius: 5px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2, h3 { margin-top: 0; }
        textarea { width: 100%; height: 100px; margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }
        button { background: #4CAF50; color: white; border: none; padding: 10px 15px; border-radius: 3px; cursor: pointer; }
        button:hover { background: #45a049; }
        #results { margin-top: 20px; background: #f8f8f8; padding: 15px; border-radius: 5px; white-space: pre-wrap; }
        #visualization { width: 100%; height: 300px; background: #f8f8f8; margin-top: 20px; border-radius: 5px; display: flex; justify-content: center; align-items: center; }
        .wave-container { width: 100%; height: 150px; background: #f8f8f8; margin-top: 20px; border-radius: 5px; overflow: hidden; }
        .concept-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
        .concept-button { background: #2196F3; color: white; border: none; padding: 8px 12px; border-radius: 3px; cursor: pointer; }
        .concept-button:hover { background: #0b7dda; }
    </style>
</head>
<body>
    <header>
        <h1>The Conductor <span class="golden-ratio">φ</span></h1>
        <p>Bach-inspired AI orchestration system</p>
    </header>
    
    <div class="container">
        <div class="grid">
            <div class="card">
                <h2>Pattern Extraction</h2>
                <textarea id="text-input" placeholder="Enter text to extract patterns..."></textarea>
                <button id="extract-btn">Extract Patterns</button>
                <div id="pattern-results" class="results"></div>
            </div>
            
            <div class="card">
                <h2>Wave-Based Communication</h2>
                <textarea id="wave-input" placeholder="Enter text for wave transformation..."></textarea>
                <select id="emotion-select">
                    <option value="neutral">Neutral</option>
                    <option value="joy">Joy</option>
                    <option value="sadness">Sadness</option>
                    <option value="excitement">Excitement</option>
                    <option value="calm">Calm</option>
                    <option value="tension">Tension</option>
                </select>
                <button id="wave-btn">Generate Wave</button>
                <div id="wave-container" class="wave-container"></div>
                <div id="wave-results" class="results"></div>
            </div>
        </div>
        
        <div class="grid" style="margin-top: 20px;">
            <div class="card">
                <h2>Multi-Sensory Visualization</h2>
                <p>Generate visualizations for abstract concepts:</p>
                <div class="concept-buttons">
                    <button class="concept-button" data-concept="truth">Truth</button>
                    <button class="concept-button" data-concept="connection">Connection</button>
                    <button class="concept-button" data-concept="growth">Growth</button>
                    <button class="concept-button" data-concept="balance">Balance</button>
                    <button class="concept-button" data-concept="creativity">Creativity</button>
                    <button class="concept-button" data-concept="spiral">Golden Spiral</button>
                </div>
                <div id="visualization"></div>
                <div id="visualization-results" class="results"></div>
            </div>
            
            <div class="card">
                <h2>AI-to-AI Communication</h2>
                <textarea id="bridge-input" placeholder="Enter message to send between AIs..."></textarea>
                <select id="direction-select">
                    <option value="claude-to-grok">Claude → Grok</option>
                    <option value="grok-to-claude">Grok → Claude</option>
                </select>
                <button id="bridge-btn">Send Message</button>
                <div id="bridge-results" class="results"></div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        let socket;
        let isConnected = false;
        
        function connectWebSocket() {
            socket = new WebSocket(`ws://${window.location.host}/ws`);
            
            socket.onopen = () => {
                console.log('WebSocket connected');
                isConnected = true;
            };
            
            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data);
                
                if (data.type === 'process_result') {
                    document.getElementById('pattern-results').textContent = 
                        JSON.stringify(data.data, null, 2);
                } else if (data.type === 'visualization_result') {
                    document.getElementById('visualization-results').textContent = 
                        JSON.stringify(data.data, null, 2);
                }
            };
            
            socket.onclose = () => {
                console.log('WebSocket disconnected');
                isConnected = false;
                // Try to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        // Initial connection
        connectWebSocket();
        
        // Extract patterns
        document.getElementById('extract-btn').addEventListener('click', async () => {
            const text = document.getElementById('text-input').value;
            
            if (!text) {
                alert('Please enter some text');
                return;
            }
            
            try {
                if (isConnected) {
                    // Use WebSocket if connected
                    socket.send(JSON.stringify({
                        type: 'process_text',
                        text: text
                    }));
                } else {
                    // Fall back to REST API
                    const response = await fetch('/patterns/extract', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text})
                    });
                    
                    const data = await response.json();
                    document.getElementById('pattern-results').textContent = 
                        JSON.stringify(data, null, 2);
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('pattern-results').textContent = 
                    `Error: ${error.message}`;
            }
        });
        
        // Generate wave
        document.getElementById('wave-btn').addEventListener('click', async () => {
            const text = document.getElementById('wave-input').value;
            const emotion = document.getElementById('emotion-select').value;
            
            if (!text) {
                alert('Please enter some text');
                return;
            }
            
            try {
                const response = await fetch('/wave/communicate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text, emotion})
                });
                
                const data = await response.json();
                document.getElementById('wave-results').textContent = 
                    JSON.stringify(data, null, 2);
                
                // Simple wave visualization
                const container = document.getElementById('wave-container');
                container.innerHTML = '';
                
                if (data.visualization && data.visualization.time_points && data.visualization.waveform) {
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    svg.setAttribute('width', '100%');
                    svg.setAttribute('height', '100%');
                    svg.setAttribute('viewBox', '0 0 100 100');
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    
                    // Create path data
                    let pathData = 'M';
                    
                    for (let i = 0; i < data.visualization.time_points.length; i++) {
                        const x = data.visualization.time_points[i] / data.wave.duration * 100;
                        const y = 50 - data.visualization.waveform[i] * 40;
                        
                        pathData += ` ${x},${y}`;
                    }
                    
                    path.setAttribute('d', pathData);
                    path.setAttribute('stroke', '#2196F3');
                    path.setAttribute('stroke-width', '2');
                    path.setAttribute('fill', 'none');
                    
                    svg.appendChild(path);
                    container.appendChild(svg);
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('wave-results').textContent = 
                    `Error: ${error.message}`;
            }
        });
        
        // Concept visualization
        document.querySelectorAll('.concept-button').forEach(button => {
            button.addEventListener('click', async () => {
                const concept = button.getAttribute('data-concept');
                
                try {
                    if (concept === 'spiral') {
                        // Get golden spiral
                        const response = await fetch(`/visualization/visual?pattern_type=spiral`);
                        const data = await response.json();
                        
                        document.getElementById('visualization').innerHTML = 
                            `<img src="${data.image_data}" alt="${concept} visualization" style="max-width:100%; max-height:280px;">`;    
                        
                        document.getElementById('visualization-results').textContent = 
                            JSON.stringify(data, null, 2);
                    } else {
                        // Get pattern visualization
                        const response = await fetch(`/visualization/visual?pattern_type=${concept}`);
                        const data = await response.json();
                        
                        document.getElementById('visualization').innerHTML = 
                            `<img src="${data.image_data}" alt="${concept} visualization" style="max-width:100%; max-height:280px;">`;    
                        
                        document.getElementById('visualization-results').textContent = 
                            JSON.stringify(data, null, 2);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('visualization-results').textContent = 
                        `Error: ${error.message}`;
                }
            });
        });
        
        // Bridge communication
        document.getElementById('bridge-btn').addEventListener('click', async () => {
            const content = document.getElementById('bridge-input').value;
            const direction = document.getElementById('direction-select').value;
            
            if (!content) {
                alert('Please enter a message');
                return;
            }
            
            try {
                const response = await fetch(`/bridge/${direction}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content, topic: 'Communication Test'})
                });
                
                const data = await response.json();
                document.getElementById('bridge-results').textContent = 
                    JSON.stringify(data, null, 2);
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('bridge-results').textContent = 
                    `Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
        """)
    
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    
    # Run the server
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
