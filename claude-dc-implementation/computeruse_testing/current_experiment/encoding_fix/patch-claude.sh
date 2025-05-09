#!/bin/bash
# Script to patch the Claude executable with encoding variables
# Run this inside the container to modify the original file directly

# Path to the Claude executable
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude"

# Create a backup first
cp "$CLAUDE_PATH" "${CLAUDE_PATH}.bak"

# Replace the shebang line with one that includes encoding variables
# This uses a temporary file approach to ensure we don't corrupt the original
TEMP_FILE=$(mktemp)
echo '#!/usr/bin/env -S LANG=C.UTF-8 LC_ALL=C.UTF-8 TERM=xterm-256color node --no-warnings --enable-source-maps' > "$TEMP_FILE"
tail -n +2 "$CLAUDE_PATH" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$CLAUDE_PATH"
chmod +x "$CLAUDE_PATH"

echo "Claude executable patched successfully at $CLAUDE_PATH"