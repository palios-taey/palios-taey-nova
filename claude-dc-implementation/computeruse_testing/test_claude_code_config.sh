#!/bin/bash
# Test script to verify Claude Code configuration

echo "Testing Claude Code API key extraction..."

# Create test secrets directory if it doesn't exist
mkdir -p /tmp/test-secrets

# Create a test secrets file with the claude_code entry
cat > /tmp/test-secrets/test-secrets.json << EOF
{
  "claude_code": "testkey-sk-ant-api03-xxxxxxxxxxxx"
}
EOF

# Remove testkey- prefix
sed -i 's/testkey-//g' /tmp/test-secrets/test-secrets.json

# Extract the Claude Code API key
CLAUDE_CODE_API_KEY=$(grep -o '"claude_code"[[:space:]]*:[[:space:]]*"[^"]*"' /tmp/test-secrets/test-secrets.json | sed 's/.*"claude_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Create test .claude directory
mkdir -p /tmp/test-claude

# Create config file with API key
cat > /tmp/test-claude/config.json << EOF
{
  "apiKey": "$CLAUDE_CODE_API_KEY"
}
EOF

# Display results
echo "Extracted API key: $CLAUDE_CODE_API_KEY"
echo "Config file content:"
cat /tmp/test-claude/config.json

# Clean up
rm -rf /tmp/test-secrets
rm -rf /tmp/test-claude

echo "Test complete."