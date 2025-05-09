#!/bin/bash
# Script to setup Claude Code with API key

# Create config directory if it doesn't exist
mkdir -p ~/.config/claude

# Create config file with API key
cat > ~/.config/claude/config.json << EOF
{
  "api_key": "sk-ant-api-key-here"
}
EOF

# Set proper permissions
chmod 600 ~/.config/claude/config.json

# Also set environment variable as backup method
echo 'export ANTHROPIC_API_KEY="sk-ant-api-key-here"' >> ~/.bashrc

echo "Claude Code API key has been configured!"
echo "To use immediately in current session, run:"
echo "export ANTHROPIC_API_KEY=\"sk-ant-api-key-here\""
echo ""
echo "Replace \"sk-ant-api-key-here\" with your actual API key in both:"
echo "1. ~/.config/claude/config.json"
echo "2. The export command above"