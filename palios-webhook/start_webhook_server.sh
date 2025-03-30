#!/bin/bash
# Install dependencies if needed
pip install -r requirements.txt

# Start the webhook server
python webhook_server.py
