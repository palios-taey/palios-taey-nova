#!/bin/bash
# Script to set the ANTHROPIC_API_KEY environment variable for Claude Code

# Extract Claude Code API key from secrets file
if [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
    CLAUDE_CODE_API_KEY=$(grep -o '"claude_code"[[:space:]]*:[[:space:]]*"[^"]*"' /home/computeruse/secrets/palios-taey-secrets.json | sed 's/.*"claude_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    
    if [ ! -z "$CLAUDE_CODE_API_KEY" ]; then
        # Set environment variable for current session
        export ANTHROPIC_API_KEY="$CLAUDE_CODE_API_KEY"
        
        # Add to .bashrc for persistence
        echo "export ANTHROPIC_API_KEY=\"$CLAUDE_CODE_API_KEY\"" >> ~/.bashrc
    else
        echo "Error: Claude Code API key not found in secrets file"
        exit 1
    fi
else
    echo "Error: Secrets file not found"
    exit 1
fi

echo "ANTHROPIC_API_KEY environment variable has been set for the current session"
echo "and added to ~/.bashrc for persistence"
echo ""
echo "To launch Claude Code with this key, simply run:"
echo "claude code"