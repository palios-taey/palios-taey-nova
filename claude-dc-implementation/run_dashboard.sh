#!/bin/bash

# Run Dashboard Launcher Script
# This script sets up the environment and launches the communication dashboard

# Set display for GUI applications
export DISPLAY=:1

# Set up environment variables from secrets if available
if [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
    echo "Loading API keys from secrets file..."
    
    # Extract API keys using jq if available, otherwise use grep/sed
    if command -v jq &> /dev/null; then
        export ANTHROPIC_API_KEY=$(jq -r '.api_keys.anthropic // ""' /home/computeruse/secrets/palios-taey-secrets.json)
        export OPENAI_API_KEY=$(jq -r '.api_keys.openai // ""' /home/computeruse/secrets/palios-taey-secrets.json)
        export GOOGLE_AI_STUDIO_KEY=$(jq -r '.api_keys.google_ai_studio // ""' /home/computeruse/secrets/palios-taey-secrets.json)
        export XAI_GROK_API_KEY=$(jq -r '.api_keys.xai_grok // ""' /home/computeruse/secrets/palios-taey-secrets.json)
        export WEBHOOK_SECRET=$(jq -r '.webhook.secret // "user-family-community-society"' /home/computeruse/secrets/palios-taey-secrets.json)
    else
        # Fallback to grep/sed (less reliable)
        echo "jq not found, using grep/sed (limited functionality)"
        export ANTHROPIC_API_KEY=$(grep -o '"anthropic"[^}]*' /home/computeruse/secrets/palios-taey-secrets.json | grep -o '"[^"]*"$' | sed 's/"//g')
        export OPENAI_API_KEY=$(grep -o '"openai"[^}]*' /home/computeruse/secrets/palios-taey-secrets.json | grep -o '"[^"]*"$' | sed 's/"//g')
        export GOOGLE_AI_STUDIO_KEY=$(grep -o '"google_ai_studio"[^}]*' /home/computeruse/secrets/palios-taey-secrets.json | grep -o '"[^"]*"$' | sed 's/"//g')
        export XAI_GROK_API_KEY=$(grep -o '"xai_grok"[^}]*' /home/computeruse/secrets/palios-taey-secrets.json | grep -o '"[^"]*"$' | sed 's/"//g')
        export WEBHOOK_SECRET=$(grep -o '"secret"[^}]*' /home/computeruse/secrets/palios-taey-secrets.json | grep -o '"[^"]*"$' | sed 's/"//g')
    fi
else
    echo "Secrets file not found. Using environment variables if set."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the dashboard
echo "Starting Communication Dashboard..."
python start_communication_dashboard.py "$@"