#!/bin/bash

# Script to reorganize documents into the new structure

# Display help
show_help() {
    echo "Usage: $0 [-m MAPPING_FILE] [-d]"
    echo ""
    echo "Options:"
    echo "  -m MAPPING_FILE    File containing mapping of old to new locations"
    echo "  -d                 Dry run (show what would happen without making changes)"
    echo ""
    echo "Example: $0 -m document_mapping.txt"
    echo "         $0 -m document_mapping.txt -d"
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
DRY_RUN=false
while getopts "m:dh" opt; do
    case $opt in
        m) MAPPING_FILE=$OPTARG ;;
        d) DRY_RUN=true ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Validate mapping file
if [ -z "$MAPPING_FILE" ] || [ ! -f "$MAPPING_FILE" ]; then
    echo "Error: Mapping file does not exist or was not specified"
    show_help
fi

# Process each line in the mapping file
echo "Processing document reorganization..."
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN MODE - no changes will be made"
fi

while IFS="|" read -r old_path new_path; do
    # Skip empty lines or comments
    if [ -z "$old_path" ] || [[ "$old_path" == \#* ]]; then
        continue
    fi
    
    # Trim whitespace
    old_path=$(echo "$old_path" | xargs)
    new_path=$(echo "$new_path" | xargs)
    
    # Check if source exists
    if [ ! -f "$old_path" ]; then
        echo "WARNING: Source file does not exist: $old_path"
        continue
    fi
    
    # Create destination directory if it doesn't exist
    new_dir=$(dirname "$new_path")
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$new_dir"
    fi
    
    # Move file or show what would happen
    if [ "$DRY_RUN" = true ]; then
        echo "Would move: $old_path -> $new_path"
    else
        # Create directory
        mkdir -p "$(dirname "$new_path")"
        
        # Move file
        mv "$old_path" "$new_path"
        echo "Moved: $old_path -> $new_path"
        
        # Update internal links in all files
        old_path_escaped=$(echo "$old_path" | sed 's/\//\\\//g')
        new_path_escaped=$(echo "$new_path" | sed 's/\//\\\//g')
        
        # Find all markdown files
        find docs -name "*.md" -type f | while read -r file; do
            # Replace links
            sed -i "s/($old_path_escaped)/($new_path_escaped)/g" "$file"
            sed -i "s/($old_path_escaped)]/($new_path_escaped)]/g" "$file"
        done
    fi
done < "$MAPPING_FILE"

echo "Document reorganization complete!"
if [ "$DRY_RUN" = true ]; then
    echo "This was a dry run. No changes were made."
fi
