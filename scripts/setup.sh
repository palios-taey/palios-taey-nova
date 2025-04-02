#!/bin/bash
# setup.sh

echo "Starting Claude DC Environment Setup"
echo "==================================="

# Install dependencies from requirements.txt
echo "Installing Python dependencies from requirements.txt..."
if [ -f "claude-dc-implementation/requirements.txt" ]; then
  pip install --no-cache-dir -r claude-dc-implementation/requirements.txt || echo "Some dependencies failed to install"
else
  echo "ERROR: requirements.txt not found"
  exit 1
fi

# Install spaCy language model
echo "Installing spaCy model..."
python -m spacy download en_core_web_md || echo "spaCy model download failed"

# Create .env file from secrets if needed
if [ ! -f "claude-dc-implementation/.env" ] && [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
  echo "Creating .env file from secrets..."
  python3 -c "
import json
import os

# Load secrets file
with open('/home/computeruse/secrets/palios-taey-secrets.json', 'r') as f:
    secrets = json.load(f)

# Create .env file
with open('claude-dc-implementation/.env', 'w') as f:
    f.write(f\"ANTHROPIC_API_KEY=\\\"{secrets['api_keys']['anthropic']}\\\"\n\")
    f.write(f\"GOOGLE_AI_STUDIO_KEY=\\\"{secrets['api_keys']['google_ai_studio']}\\\"\n\")
    f.write(f\"OPENAI_API_KEY=\\\"{secrets['api_keys']['openai']}\\\"\n\")
    f.write(f\"XAI_GROK_API_KEY=\\\"{secrets['api_keys']['xai_grok']}\\\"\n\")
    f.write(f\"GCP_PROJECT_ID=\\\"{secrets['gcp']['project_id']}\\\"\n\")
    f.write(f\"GCP_REGION=\\\"{secrets['gcp']['region']}\\\"\n\")
    f.write(f\"WEBHOOK_SECRET=\\\"{secrets['webhook']['secret']}\\\"\n\")
"
  echo ".env file created successfully!"
else
  echo "Skipping .env creation (already exists or secrets not found)"
fi

echo ""
echo "Setup complete! You can now review your cache files:"
echo "- claude-dc-cache_part-1.md"
echo "- claude-dc-cache_part-2.md"
echo "- cache-update.md"
echo "- webhook-integration-instructions.md"
echo "- CACHE.UPDATE.IMPLEMENTATION.md"
echo "- IMPLEMENTATION_REPORT.md"
echo ""
echo "And start services with:"
echo "cd claude-dc-implementation"
echo "python3 -m uvicorn src.mcp.mcp_server:app --host 0.0.0.0 --port 8001"
echo "python3 -m streamlit run src/dashboard/app.py --server.port=8502"
echo "python3 -m uvicorn demo_server:app --host 0.0.0.0 --port 8002"
