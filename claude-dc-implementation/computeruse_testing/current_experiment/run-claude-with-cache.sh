#!/bin/bash
# Run Claude Code with prompt cache file
# Uses the original working run-claude-code-simple.sh

# Ensure we're in the home directory
cd /home/computeruse

# Run Claude Code with prompt cache
./run-claude-code-simple.sh --prompt-cache-file=/home/computeruse/cache/cache.md "$@"