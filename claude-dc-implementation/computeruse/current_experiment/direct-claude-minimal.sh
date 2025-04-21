#!/bin/bash
# Ultra-minimal approach to run Claude with UTF-8 encoding variables
# Place this file in the container and make it executable

# Determine current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set essential encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Run Claude via Node directly 
# The .nvm versions path is the verified location for Claude
NODE_PATH=/home/computeruse/.nvm/versions/node/v18.20.0/bin/node
CLAUDE_PATH=/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude

# Run the node executable directly with the claude script as argument
"$NODE_PATH" "$CLAUDE_PATH" "$@"