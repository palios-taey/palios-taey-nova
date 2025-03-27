#!/bin/bash
# Script to generate a detailed index of the PALIOS-TAEY repository with metadata including character counts.
# Run this script from the root directory of the repository (palios-taey-nova).
# Processes files in the root directory (non-recursively) and all files in /current-execution-status, /docs, and /transcripts.

# Function to get file size in bytes
get_size() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    stat -f%z "$1" 2>/dev/null || echo "N/A"
  else
    # Linux
    stat --format=%s "$1" 2>/dev/null || echo "N/A"
  fi
}

# Function to get last modification time
get_mtime() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    date -r "$1" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "N/A"
  else
    # Linux
    stat --format=%y "$1" 2>/dev/null || echo "N/A"
  fi
}

# Initialize summary variables
total_chars=0
total_size=0
file_count=0

# Process files in the root directory and specified subdirectories
(
  find . -maxdepth 1 -type f          # Files directly in root (no subdirectories)
  find ./current-execution-status -type f  # All files in /current-execution-status
  find ./docs -type f                      # All files in /docs
  find ./transcripts -type f               # All files in /transcripts
) | while read -r file; do
  if [ -f "$file" ]; then
    # Get metadata
    char_count=$(wc -m < "$file" 2>/dev/null || echo "N/A")
    size=$(get_size "$file")
    mtime=$(get_mtime "$file")
    extension="${file##*.}"

    # Print file details
    echo "File: $file"
    echo "Characters: $char_count"
    echo "Size: $size bytes"
    echo "Modified: $mtime"
    echo "Extension: $extension"
    echo ""

    # Update summary totals (only if metadata is valid)
    if [[ "$char_count" != "N/A" ]]; then
      total_chars=$((total_chars + char_count))
    fi
    if [[ "$size" != "N/A" ]]; then
      total_size=$((total_size + size))
    fi
    file_count=$((file_count + 1))
  fi
done

# Initialize variables before the loop
total_files=0
total_chars=0
total_size=0

# Inside the loop, for each file, add:
total_chars=$((total_chars + $(wc -m < "$file" 2>/dev/null || echo 0)))
total_size=$((total_size + $(stat -f %z "$file" 2>/dev/null || stat -c %s "$file" 2>/dev/null || echo 0)))
total_files=$((total_files + 1))

# After the loop, print:
echo "Summary:"
echo "Total files: $total_files"
echo "Total characters: $total_chars"
echo "Total size: $total_size bytes"
