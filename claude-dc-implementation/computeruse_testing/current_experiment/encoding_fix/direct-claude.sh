#!/bin/bash
# Direct script to run Claude Code
# Copy this file directly inside /home/computeruse/ in the container

# Set encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Go to home directory
cd /home/computeruse

# Run Claude directly with full path
/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude