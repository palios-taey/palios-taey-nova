#!/bin/bash

# Detailed script to generate a repository index with paths and clickable links
# This will crawl the repository and create a centralized index

# Configuration
REPO_NAME="palios-taey/palios-taey-nova"
GITHUB_PREFIX="https://github.com/${REPO_NAME}/blob/main"
REPO_ROOT=$(git rev-parse --show-toplevel)
INDEX_FILE="$REPO_ROOT/docs/universal/repository_index.md"
CURRENT_DATE=$(date +"%Y-%m-%d")

# Create header
cat > "$INDEX_FILE" << EOF
# PALIOS-TAEY Repository Index

**Last Updated:** $CURRENT_DATE

This document provides a centralized index of the PALIOS-TAEY repository structure designed for AI model navigation.

## Repository Structure
EOF

# Function to process a directory
process_directory() {
  local dir=$1
  local level=$2
  local header_prefix=""
  
  # Create header prefix based on nesting level
  for ((i=0; i<level; i++)); do
    header_prefix="#$header_prefix"
  done
  
  # Get directory name without path
  dir_name=$(basename "$dir")
  
  # Add directory header if not root
  if [ "$dir" != "$REPO_ROOT" ]; then
    echo -e "\n$header_prefix### $dir_name\n" >> "$INDEX_FILE"
  fi
  
  # Add files in the current directory
  find "$dir" -maxdepth 1 -type f -name "*.md" -o -name "*.json" | sort | while read -r file; do
    rel_path=$(realpath --relative-to="$REPO_ROOT" "$file")
    filename=$(basename "$file")
    full_url="${GITHUB_PREFIX}/${rel_path}"
    
    # Output both the path and a clickable link
    echo "  - **(${full_url}${filename})**" >> "$INDEX_FILE"
  done
  
  # Process subdirectories
  find "$dir" -maxdepth 1 -type d | sort | grep -v "^\.$" | grep -v "^\.\.$ " | grep -v "^$dir$" | while read -r subdir; do
    # Skip .git directory and other hidden directories
    if [[ $(basename "$subdir") != .* ]]; then
      process_directory "$subdir" $((level + 1))
    fi
  done
}

# Process the docs directory
echo -e "\n## Documentation\n" >> "$INDEX_FILE"
process_directory "$REPO_ROOT/docs" 2

# Process current-execution-status directory
echo -e "\n## Current Execution Status\n" >> "$INDEX_FILE"
process_directory "$REPO_ROOT/current-execution-status" 2

echo "Repository index generated at $INDEX_FILE with GitHub URLs"
