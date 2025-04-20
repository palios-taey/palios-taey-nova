#!/bin/bash
# setup.sh

echo "Starting Claude DC Environment Setup"
echo "==================================="

# Update system packages
sudo apt update -y

# Install required system-level dependencies explicitly
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    httpx \
    streamlit

sudo apt-get install -y rsync

# Python environment setup
echo "Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r claude-dc-implementation/requirements.txt

# Install spaCy language model
echo "Installing spaCy model..."
python -m spacy download en_core_web_md

# Setup .env file from secrets (adjust as needed)
if [ ! -f "claude-dc-implementation/.env" ] && [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
  echo "Creating .env file from secrets..."
  python3 -c "
import json
import os
with open('/home/computeruse/secrets/palios-taey-secrets.json', 'r') as f:
    secrets = json.load(f)
with open('claude-dc-implementation/.env', 'w') as f:
    f.write(f\"ANTHROPIC_API_KEY=\\\"{secrets['api_keys']['anthropic']}\\\"\n\")
    f.write(f\"GOOGLE_AI_STUDIO_KEY=\\\"{secrets['api_keys']['google_ai_studio']}\\\"\n\")
    f.write(f\"OPENAI_API_KEY=\\\"{secrets['api_keys']['openai']}\\\"\n\")
    f.write(f\"XAI_GROK_API_KEY=\\\"{secrets['api_keys']['xai_grok']}\\\"\n\")
    f.write(f\"GCP_PROJECT_ID=\\\"{secrets['gcp']['project_id']}\\\"\n\")
    f.write(f\"GCP_REGION=\\\"{secrets['gcp']['region']}\\\"\n\")
    f.write(f\"WEBHOOK_SECRET=\\\"{secrets['webhook']['secret']}\\\"\n\")
"
else
  echo "Skipping .env creation (already exists or secrets not found)"
fi

echo ""
echo "Setup complete!"

