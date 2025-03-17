"""
PALIOS-TAEY System Main Server
This module serves as the main entry point for the PALIOS-TAEY system,
integrating all components and providing API endpoints.
"""

import os
import sys
import json
import logging
from flask import Flask, jsonify

# Initialize environment
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', 'server.log'))
    ]
)
logger = logging.getLogger(__name__)

# Set default environment variables
if 'PROJECT_ID' not in os.environ:
    os.environ['PROJECT_ID'] = os.environ.get('GOOGLE_CLOUD_PROJECT', 'palios-taey-dev')
if 'ENVIRONMENT' not in os.environ:
    os.environ['ENVIRONMENT'] = 'production'
if 'USE_MOCK_RESPONSES' not in os.environ:
    os.environ['USE_MOCK_RESPONSES'] = 'True'

# Create Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/')
def index():
    return jsonify({
        "system": "PALIOS-TAEY",
        "status": "active"
    })

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
