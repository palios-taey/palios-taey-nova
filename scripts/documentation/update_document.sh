#!/bin/bash

# Script to update existing documents

# Display help
show_help() {
    echo "Usage: $0 -f FILE [-s SECTION] [-c CONTENT] [-r]"
    echo ""
    echo "Options:"
    echo "  -f FILE       File to update"
    echo "  -s SECTION    Section to update (optional)"
    echo "  -c CONTENT    New content for section (required if -s is specified)"
    echo "  -r            Update the LAST_UPDATED date (optional)"
    echo ""
    echo "Example: $0 -f docs/claude/quality_framework.md -r"
    echo "         $0 -f docs/claude/quality_framework.md -s \"## Purpose\" -c \"New purpose content\""
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
UPDATE_DATE=false
while getopts "f:s:c:rh" opt; do
    case $opt in
        f) FILE=$OPTARG ;;
        s) SECTION=$OPTARG ;;
        c) CONTENT=$OPTARG ;;
        r) UPDATE_DATE=true ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Validate file argument
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Error: File does not exist or was not specified"
    show_help
fi

# Update document
if [ ! -z "$SECTION" ]; then
    # Check if content is provided
    if [ -z "$CONTENT" ]; then
        echo "Error: Content is required when updating a section"
        show_help
    fi
    
    # Check if section exists
    if ! grep -q "$SECTION" "$FILE"; then
        echo "Error: Section '$SECTION' not found in $FILE"
        exit 1
    fi
    
    # Create temporary file
    TMP_FILE=$(mktemp)
    
    # Copy content to temporary file with section updated
    awk -v section="$SECTION" -v content="$CONTENT" '
    $0 ~ section {
        print $0
        getline
        while ($0 !~ /^##/ && NF > 0) {
            getline
        }
        print content
        if ($0 ~ /^##/ || NF == 0) {
            print ""
            print $0
        }
        next
    }
    { print }
    ' "$FILE" > "$TMP_FILE"
    
    # Replace original file with updated content
    mv "$TMP_FILE" "$FILE"
    
    echo "Updated section '$SECTION' in $FILE"
fi

# Update the LAST_UPDATED date if requested
if [ "$UPDATE_DATE" = true ]; then
    CURRENT_DATE=$(date +%Y-%m-%d)
    sed -i "s/LAST_UPDATED: [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/LAST_UPDATED: $CURRENT_DATE/" "$FILE"
    echo "Updated last modified date to $CURRENT_DATE in $FILE"
fi

echo "Document update complete!"
