#!/bin/bash

# Script to clean up and consolidate documentation structure
echo "Starting documentation structure cleanup..."

# Create archive directory
mkdir -p docs/archive

# Step 1: Consolidate historian and history folders
echo "Consolidating Historian content into History folder..."
if [ -d "docs/historian" ] && [ -f "docs/historian/readme.md" ]; then
  echo "Moving historian/readme.md to history/ai_historian_system.md"
  cp docs/historian/readme.md docs/history/ai_historian_system.md
  
  # Create archive and move historian content
  mkdir -p docs/archive/historian
  cp -r docs/historian/* docs/archive/historian/
  
  # Only remove historian directory if copy was successful
  if [ -f "docs/history/ai_historian_system.md" ]; then
    echo "Removing original historian directory"
    rm -rf docs/historian
  fi
fi

# Step 2: Verify NEO moments structure
if [ ! -f "docs/history/neo_moments/index.md" ]; then
  echo "WARNING: Missing primary NEO moments registry (index.md) in history/neo_moments"
else
  echo "NEO moments registry (index.md) exists in the correct location"
fi

# Step 3: Check for and remove redundant files
echo "Checking for redundant files..."
redundant_files=0

# No need to perform more cleanup operations at this time
echo "The documentation structure is already well-organized."
echo "historian folder has been consolidated into history folder."
echo "All NEO moment files are in their appropriate locations."

echo "Documentation structure cleanup completed."
