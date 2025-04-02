#!/bin/bash

# Modified Conductor Framework Setup Script
# This script installs all required dependencies for the Conductor Framework

SECRETS_FILE="/home/jesse/secrets/palios-taey-secrets.json"
INSTALL_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation"

echo "Setting up Conductor Framework environment..."

# Check if secrets file exists
if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: Secrets file not found at $SECRETS_FILE"
    echo "Please ensure the secrets file is available before running setup."
    echo "The secrets file should follow the structure in config/secrets_structure.json"
    exit 1
fi

# Create Python virtual environment (optional)
# python3 -m venv $INSTALL_DIR/.venv
# source $INSTALL_DIR/.venv/bin/activate

# Install required packages
pip3 install --upgrade pip
pip3 install \
    aiohttp \
    numpy \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    streamlit \
    tensorflow \
    anthropic \
    openai \
    google-cloud-firestore \
    google-api-python-client \
    google-auth \
    python-dotenv \
    requests \
    flask \
    transformers \
    nltk \
    pillow \
    fastapi \
    uvicorn[standard] \
    spacy \
    PyWavelets \
    librosa \
    docker-py \
    soundfile

# Install spaCy language model
python3 -m spacy download en_core_web_md

# Create .env file from secrets
echo "Creating .env file from secrets..."
python3 -c "
import json
import os

# Load secrets file
with open('$SECRETS_FILE', 'r') as f:
    secrets = json.load(f)

# Create .env file
with open('$INSTALL_DIR/.env', 'w') as f:
    f.write(f\"ANTHROPIC_API_KEY=\\\"{secrets['api_keys']['anthropic']}\\\"\n\")
    f.write(f\"GOOGLE_AI_STUDIO_KEY=\\\"{secrets['api_keys']['google_ai_studio']}\\\"\n\")
    f.write(f\"OPENAI_API_KEY=\\\"{secrets['api_keys']['openai']}\\\"\n\")
    f.write(f\"XAI_GROK_API_KEY=\\\"{secrets['api_keys']['xai_grok']}\\\"\n\")
    f.write(f\"GCP_PROJECT_ID=\\\"{secrets['gcp']['project_id']}\\\"\n\")
    f.write(f\"GCP_REGION=\\\"{secrets['gcp']['region']}\\\"\n\")
    f.write(f\"WEBHOOK_URL=\\\"{secrets['webhook']['url']}\\\"\n\")
    f.write(f\"WEBHOOK_SECRET=\\\"{secrets['webhook']['secret']}\\\"\n\")
"

# Setup Google Cloud credentials from secrets
echo "Setting up Google Cloud credentials from secrets..."
mkdir -p $INSTALL_DIR/credentials
python3 -c "
import json
import os

# Load secrets file
with open('$SECRETS_FILE', 'r') as f:
    secrets = json.load(f)

# Create service account file
os.makedirs('$INSTALL_DIR/credentials', exist_ok=True)
with open('$INSTALL_DIR/credentials/service_account.json', 'w') as f:
    json.dump(secrets['gcp']['service_account'], f, indent=2)
"

# Create necessary directories
mkdir -p $INSTALL_DIR/config
mkdir -p $INSTALL_DIR/data/transcripts
mkdir -p $INSTALL_DIR/data/patterns
mkdir -p $INSTALL_DIR/data/models
mkdir -p $INSTALL_DIR/logs

echo "Environment setup complete!"
