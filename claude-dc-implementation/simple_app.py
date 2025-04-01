"""
Simple Flask Application for Pattern-Based Demo
Following Bach's mathematical principles
"""

import os
import math
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Constants
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio
API_VERSION = "0.618.0"  # Golden ratio version
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """Root endpoint providing system information or HTML interface"""
    # Check if the request accepts HTML
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # Return the HTML template
        return render_template("index.html")
    else:
        # Return JSON for API requests
        return jsonify({
            "name": "Pattern-Based Demo Server",
            "version": API_VERSION,
            "status": "operational",
            "pattern_harmony": "golden_ratio",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "patterns": "/patterns",
                "visualization": "/visualization",
                "documentation": "/documentation",
            }
        })

@app.route('/health')
def health_check():
    """Health check endpoint following Bach's mathematical precision"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": API_VERSION,
        "components": {
            "pattern_router": "operational",
            "visualization_router": "operational",
            "websocket_manager": "operational"
        }
    })

@app.route('/patterns/list')
def list_patterns():
    """List all available patterns"""
    return jsonify({
        "patterns": []
    })

@app.route('/visualization/visualizations')
def list_visualizations():
    """List all available visualizations"""
    return jsonify({
        "visualizations": []
    })

@app.route('/visualization/audio')
def list_audio():
    """List all available audio files"""
    return jsonify({
        "audio_files": []
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)