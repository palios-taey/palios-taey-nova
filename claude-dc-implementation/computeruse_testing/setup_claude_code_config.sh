#!/bin/bash
# Script to setup Claude Code config directly in Claude DC's environment

# Create the .config/claude directory if it doesn't exist
mkdir -p ~/.config/claude

# Extract Claude Code API key from secrets file
if [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
    CLAUDE_CODE_API_KEY=$(grep -o '"claude_code"[[:space:]]*:[[:space:]]*"[^"]*"' /home/computeruse/secrets/palios-taey-secrets.json | sed 's/.*"claude_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    
    if [ -z "$CLAUDE_CODE_API_KEY" ]; then
        echo "Error: Claude Code API key not found in secrets file"
        exit 1
    fi
else
    echo "Error: Secrets file not found"
    exit 1
fi

# Create the config.json file with the API key
cat > ~/.config/claude/config.json << EOF
{
  "api_key": "$CLAUDE_CODE_API_KEY"
}
EOF

# Set proper permissions
chmod 600 ~/.config/claude/config.json

echo "Claude Code API key has been configured in ~/.config/claude/config.json"
echo "This should allow Claude Code to start without manual key entry"