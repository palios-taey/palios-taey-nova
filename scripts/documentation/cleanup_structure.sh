#!/bin/bash

# Script to clean up and consolidate documentation structure
echo "Starting documentation structure cleanup..."

# Create necessary directories
mkdir -p docs/history/neo_moments
mkdir -p docs/archive

# Step 1: Move Historian content to History folder
echo "Consolidating Historian content into History folder..."
if [ -f "docs/historian/readme.md" ]; then
  echo "Moving historian/readme.md to history/ai_historian_system.md"
  cp docs/historian/readme.md docs/history/ai_historian_system.md
  # Archive the original
  mkdir -p docs/archive/historian
  mv docs/historian/* docs/archive/historian/
fi

# Step 2: Check for any duplicated files and organize
echo "Checking for duplicated content..."
find docs/history -type f -name "*.md" | while read file; do
  basename=$(basename "$file")
  # Check for similar files with different names
  similar_files=$(find docs -type f -not -path "docs/history/*" -name "*$(echo $basename | cut -d. -f1)*.md" 2>/dev/null)
  if [ ! -z "$similar_files" ]; then
    echo "Found similar files to $basename:"
    echo "$similar_files"
    echo "Consider reviewing these files for consolidation."
  fi
done

# Step 3: Consolidate AI-AI protocols if needed
if [ -d "docs/protocols/ai-ai" ]; then
  echo "Checking AI-AI protocols organization..."
  mkdir -p docs/ai-ai
  find docs/protocols/ai-ai -type f -name "*.md" | while read file; do
    dest="docs/ai-ai/$(basename "$file")"
    if [ ! -f "$dest" ]; then
      echo "Moving $(basename "$file") to ai-ai folder"
      cp "$file" "$dest"
    else
      echo "File $(basename "$file") already exists in ai-ai folder"
    fi
  done
fi

# Step 4: Organize documents in the root folder
echo "Organizing root documents..."
root_docs=$(find docs -maxdepth 1 -type f -name "*.md" | grep -v "README.md")
for doc in $root_docs; do
  filename=$(basename "$doc")
  
  # Determine target directory based on content
  if grep -q "architecture" "$doc" || grep -q "implementation" "$doc"; then
    echo "Moving $filename to implementation folder"
    cp "$doc" "docs/implementation/$filename"
    mkdir -p docs/archive/root
    mv "$doc" "docs/archive/root/$filename"
  elif grep -q "deployment" "$doc" || grep -q "infrastructure" "$doc"; then
    echo "Moving $filename to deployment folder"
    cp "$doc" "docs/deployment/$filename"
    mkdir -p docs/archive/root
    mv "$doc" "docs/archive/root/$filename"
  else
    echo "Keeping $filename in root folder for now"
  fi
done

echo "Documentation structure cleanup completed!"
echo "Original files have been preserved in docs/archive"
echo "Please review the changes and remove archived files only when certain they are no longer needed."
