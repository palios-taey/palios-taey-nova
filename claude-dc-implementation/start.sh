#!/bin/bash

# Create necessary directories
mkdir -p edge/local_storage
mkdir -p templates
mkdir -p static

# Set up Python environment
pip install -r requirements.txt

# Start the server
python app.py