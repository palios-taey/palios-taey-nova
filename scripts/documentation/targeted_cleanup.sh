#!/bin/bash

# Script to handle specific cleanup tasks identified by Jesse
echo "Starting targeted documentation cleanup..."

# Create archive directory if it doesn't exist
mkdir -p docs/archive/misc

# Task 1: Consolidate AI-AI folders
echo "Consolidating AI-AI content..."
if [ -d "docs/protocols/ai-ai" ] && [ "$(ls -A docs/protocols/ai-ai 2>/dev/null)" ]; then
  echo "Moving files from protocols/ai-ai to ai-ai folder"
  mkdir -p docs/ai-ai
  cp -r docs/protocols/ai-ai/* docs/ai-ai/
  
  # Archive original files
  mkdir -p docs/archive/protocols
  cp -r docs/protocols/ai-ai docs/archive/protocols/
  
  # Remove the now duplicated directory
  if [ -d "docs/ai-ai" ] && [ "$(ls -A docs/ai-ai 2>/dev/null)" ]; then
    echo "Removing original protocols/ai-ai directory"
    rm -rf docs/protocols/ai-ai
  fi
fi

# Task 2: Move amendments to appropriate location
echo "Organizing amendments..."
if [ -d "docs/amendments" ]; then
  mkdir -p docs/history/amendments
  
  echo "Moving content from amendments to history/amendments"
  cp -r docs/amendments/* docs/history/amendments/
  
  # Archive original files
  mkdir -p docs/archive/amendments
  cp -r docs/amendments/* docs/archive/amendments/
  
  # Remove the now duplicated directory
  if [ -d "docs/history/amendments" ] && [ "$(ls -A docs/history/amendments 2>/dev/null)" ]; then
    echo "Removing original amendments directory"
    rm -rf docs/amendments
  fi
fi

# Task 3: Move infrastructure.md to deployment folder
echo "Moving infrastructure.md..."
if [ -f "docs/infrastructure.md" ]; then
  echo "Moving infrastructure.md to deployment folder"
  cp docs/infrastructure.md docs/deployment/infrastructure.md
  
  # Archive original file
  cp docs/infrastructure.md docs/archive/misc/
  
  # Remove original file
  if [ -f "docs/deployment/infrastructure.md" ]; then
    echo "Removing original infrastructure.md"
    rm docs/infrastructure.md
  fi
fi

echo "Targeted cleanup completed!"
echo "Files have been moved to the appropriate locations."
echo "Original files have been archived in docs/archive."
