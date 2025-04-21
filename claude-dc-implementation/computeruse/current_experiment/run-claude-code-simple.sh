#!/bin/bash
# Ultra-simple wrapper script for running Claude Code with correct encoding
# This fixes the UTF-8 encoding issues in the container environment

# Set proper locale to fix encoding issues
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Run Claude Code directly - rely on PATH to find it
cd /home/computeruse
claude-code "$@"