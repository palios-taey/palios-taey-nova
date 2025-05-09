#!/bin/bash
# Script to patch the Claude executable to set environment variables
# Run this inside the container to modify the original file directly

# Path to the Claude executable
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude"

# Create a backup first
cp "$CLAUDE_PATH" "${CLAUDE_PATH}.bak"

# Create a new temporary file
TEMP_FILE=$(mktemp)

# Extract the shebang line
SHEBANG=$(head -n 1 "$CLAUDE_PATH")
echo "$SHEBANG" > "$TEMP_FILE"

# Add environment variable settings right after the shebang line
# before any other code executes
cat << 'EOF' >> "$TEMP_FILE"

// Set UTF-8 encoding environment variables
process.env.LANG = 'C.UTF-8';
process.env.LC_ALL = 'C.UTF-8';
process.env.TERM = 'xterm-256color';

EOF

# Add the rest of the file (skip the first line which was the shebang)
tail -n +2 "$CLAUDE_PATH" >> "$TEMP_FILE"

# Replace the original file with our modified version
mv "$TEMP_FILE" "$CLAUDE_PATH"
chmod +x "$CLAUDE_PATH"

echo "Claude executable patched successfully at $CLAUDE_PATH"