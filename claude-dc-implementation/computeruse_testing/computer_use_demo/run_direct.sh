#!/bin/bash
# Run the direct implementation version of Claude DC

# Set the Python environment
export PYTHONPATH=.

# Ensure the API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ANTHROPIC_API_KEY environment variable not set."
  echo "Please set your API key with: export ANTHROPIC_API_KEY='your_key_here'"
  exit 1
fi

# Execute the direct implementation
python3 run_direct_implementation.py