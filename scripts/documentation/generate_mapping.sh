#!/bin/bash

# Script to analyze current docs and generate a mapping file for reorganization

# Display help
show_help() {
    echo "Usage: $0 [-o OUTPUT_FILE] [-d DOCS_DIR]"
    echo ""
    echo "Options:"
    echo "  -o OUTPUT_FILE    Output mapping file (default: docs/document_mapping.txt)"
    echo "  -d DOCS_DIR       Docs directory to analyze (default: docs)"
    echo ""
    echo "Example: $0 -o docs/new_mapping.txt"
    exit 1
}

# Parse arguments
OUTPUT_FILE="docs/document_mapping.txt"
DOCS_DIR="docs"

while getopts "o:d:h" opt; do
    case $opt in
        o) OUTPUT_FILE=$OPTARG ;;
        d) DOCS_DIR=$OPTARG ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Check if docs directory exists
if [ ! -d "$DOCS_DIR" ]; then
    echo "Error: Docs directory $DOCS_DIR does not exist"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p $(dirname "$OUTPUT_FILE")

# Initialize output file
echo "# Format: old_path | new_path" > "$OUTPUT_FILE"
echo "# Each line contains the current path and the new path separated by a pipe (|)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to determine the appropriate target directory
determine_target_dir() {
    local file=$1
    local content=$(cat "$file")
    local filename=$(basename "$file")
    local directory=$(dirname "$file")
    
    # Check for Claude format
    if grep -q "CLAUDE_PROTOCOL" "$file"; then
        echo "docs/claude/$filename"
        return
    fi
    
    # Check for AI-AI format
    if grep -q "RSPROTV" "$file"; then
        echo "docs/ai-ai/$filename"
        return
    fi
    
    # Check for framework documents
    if [[ "$directory" == *"framework"* ]] || [[ "$filename" == *"framework"* ]]; then
        echo "docs/framework/$filename"
        return
    fi
    
    # Check for charter documents
    if [[ "$directory" == *"charter"* ]] || [[ "$filename" == *"charter"* ]]; then
        echo "docs/charter/$filename"
        return
    fi
    
    # Check for protocol documents
    if [[ "$directory" == *"protocol"* ]] || [[ "$filename" == *"protocol"* ]] || [[ "$directory" == *"communication"* ]]; then
        echo "docs/protocols/$filename"
        return
    fi
    
    # Check for implementation documents
    if [[ "$directory" == *"implementation"* ]] || [[ "$directory" == *"api"* ]] || [[ "$directory" == *"architecture"* ]]; then
        echo "docs/implementation/$filename"
        return
    fi
    
    # Check for deployment documents
    if [[ "$directory" == *"deployment"* ]]; then
        echo "docs/deployment/$filename"
        return
    fi
    
    # Check for history documents
    if [[ "$directory" == *"history"* ]] || [[ "$directory" == *"amendments"* ]]; then
        echo "docs/history/$filename"
        return
    fi
    
    # Default to keeping in the same directory
    echo "$file"
}

# Find all markdown files in the docs directory
find "$DOCS_DIR" -name "*.md" -type f | while read -r file; do
    # Skip files in the templates directory
    if [[ "$file" == *"/templates/"* ]]; then
        continue
    fi
    
    # Determine target directory
    target_file=$(determine_target_dir "$file")
    
    # Add to mapping file
    echo "$file | $target_file" >> "$OUTPUT_FILE"
done

# Find all JSON files in the docs directory (for Charter files)
find "$DOCS_DIR" -name "*.json" -type f | while read -r file; do
    # Check if it's a charter file
    if [[ "$file" == *"charter"* ]]; then
        filename=$(basename "$file")
        echo "$file | docs/charter/$filename" >> "$OUTPUT_FILE"
    fi
done

echo "Mapping file generated at $OUTPUT_FILE"
