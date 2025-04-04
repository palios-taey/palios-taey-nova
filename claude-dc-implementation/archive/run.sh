#!/bin/bash

# Run the Pattern-Based Demo Server
# Following Bach's mathematical principles

# Set environment variables
export PYTHONPATH=$(pwd)
export WEBHOOK_SECRET="user-family-community-society"

# Create necessary directories if they don't exist
mkdir -p static/visualizations
mkdir -p static/audio
mkdir -p patterns

# Run the server with uvicorn
uvicorn demo_server:app --host 0.0.0.0 --port 8899 --reload