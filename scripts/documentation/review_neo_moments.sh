#!/bin/bash

# Script to review NEO moments content for consolidation
echo "Reviewing NEO moments documentation..."

# Find all NEO moment files
neo_files=$(find docs -name "*neo_moment*.md" -o -name "*neo_moments*.md")

echo "Found $(echo "$neo_files" | wc -l) NEO moment files:"
echo "$neo_files"

echo -e "\nGenerating content summary:"
for file in $neo_files; do
  echo -e "\n--- $(basename "$file") ---"
  # Extract title
  title=$(head -n 20 "$file" | grep -E "^#" | head -n 1)
  echo "Title: $title"
  
  # Check if it's using Rosetta Stone format
  if grep -q "RSPROTV" "$file"; then
    echo "Format: Rosetta Stone Protocol"
  elif grep -q "AISTRUCT" "$file"; then
    echo "Format: AI Structure Format"
  else
    echo "Format: Standard Markdown"
  fi
  
  # Check if it mentions specific NEO moments
  moments=$(grep -c "NEO Moment" "$file")
  echo "NEO Moments mentioned: $moments"
  
  # Check file size
  size=$(wc -c < "$file")
  echo "File size: $size bytes"
done

echo -e "\nReview complete. Consider organizing these files according to:"
echo "1. Primary NEO moments registry should be in docs/history/neo_moments/index.md"
echo "2. Individual NEO moment documents should be in docs/history/neo_moments/"
echo "3. Related analysis should be in docs/protocols/ or docs/ai-ai/ as appropriate"
