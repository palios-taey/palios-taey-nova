#!/bin/bash
# Script to test Claude Code encoding issues in Claude DC environment

# Set encoding variables for this script
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Claude Code path
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
NODE_PATH="/home/computeruse/.nvm/versions/node/v18.20.8/bin/node"

echo "=== Claude Code Encoding Test ==="
echo "Testing terminal UTF-8 support..."
echo "UTF-8 test: äöüß 你好 こんにちは 😀 🚀"
echo ""

echo "Testing Node.js UTF-8 handling..."
"$NODE_PATH" -e "console.log('UTF-8 test from Node.js: äöüß 你好 こんにちは 😀 🚀')"
echo ""

echo "Testing Claude Code version..."
LANG=C.UTF-8 LC_ALL=C.UTF-8 "$CLAUDE_PATH" --version
echo ""

echo "Checking Node.js version..."
"$NODE_PATH" --version
echo ""

echo "=== System Environment Variables ==="
echo "LANG: $LANG"
echo "LC_ALL: $LC_ALL"
echo "TERM: $TERM"
echo "NODE_PATH: $NODE_PATH"
echo ""

echo "=== Testing Simple Claude Code Query ==="
echo "Running: '$CLAUDE_PATH \"What is 2+2?\"'"
echo "This will help identify where the encoding issue occurs. Press Ctrl+C if it hangs."
echo ""

# Run Claude with a simple query to test
LANG=C.UTF-8 LC_ALL=C.UTF-8 "$CLAUDE_PATH" "What is 2+2?"

# Exit with the same code as Claude
exit $?