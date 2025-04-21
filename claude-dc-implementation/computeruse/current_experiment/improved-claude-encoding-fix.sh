#!/bin/bash
# Enhanced Claude Code encoding fix for Claude DC environment
# This script addresses binary buffer output and terminal encoding issues

# Set comprehensive encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color
export LESSCHARSET=utf-8
export NCURSES_NO_UTF8_ACS=1

# Set Node.js specific options to force encoding
export NODE_OPTIONS="--no-warnings --enable-source-maps --max-http-header-size=16384 --openssl-legacy-provider"

# Force stdout/stderr to use UTF-8
exec > >(iconv -f utf-8 -t utf-8)
exec 2> >(iconv -f utf-8 -t utf-8)

# Path to Claude Code executable
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
NODE_PATH="/home/computeruse/.nvm/versions/node/v18.20.8/bin/node"

# Add debugging info if requested
if [[ "$1" == "--debug" ]]; then
    echo "Running Claude Code with encoding fixes and debugging enabled"
    shift
    # Run Claude with debugging enabled
    "$NODE_PATH" --trace-uncaught --inspect "$CLAUDE_PATH" "$@"
else
    # Run Claude directly with encoding fixes
    "$NODE_PATH" "$CLAUDE_PATH" "$@"
fi

# Exit with the same code as Claude
exit $?