#!/bin/bash
# Wrapper script for running Claude Code with correct encoding settings
# This fixes the UTF-8 encoding issues in the container environment

# Set proper locale to fix encoding issues
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Preserve current directory to run from root
# But tell Claude Code which directory to focus on
export CLAUDE_CODE_PROJECT_DIR="/home/computeruse/github/palios-taey-nova"

# Run Claude Code with the project directory
cd /home/computeruse
claude-code --dir "$CLAUDE_CODE_PROJECT_DIR" "$@"