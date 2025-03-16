#!/bin/bash

# Script to update verification strings in all Claude-to-Claude documents
# Usage: ./update_all_verifications.sh -c VERIFICATION_CODE

# Display help
show_help() {
    echo "Usage: $0 -c VERIFICATION_CODE"
    echo ""
    echo "Options:"
    echo "  -c VERIFICATION_CODE   Verification code to use (REQUIRED)"
    echo ""
    echo "Example: $0 -c NOVA_IMPLEMENTATION_DEPLOYMENT_20250317"
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
while getopts "c:h" opt; do
    case $opt in
        c) VERIFICATION_CODE=$OPTARG ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Validate verification code
if [ -z "$VERIFICATION_CODE" ]; then
    echo "Error: Verification code must be specified"
    show_help
fi

# Current date for updating LAST_UPDATED field
CURRENT_DATE=$(date +%Y-%m-%d)

# Function to update a single document
update_document() {
    local doc="$1"
    echo "Updating verification strings in: $doc"
    
    # Update VERIFICATION_STRING
    sed -i "s/VERIFICATION_STRING:.*$/VERIFICATION_STRING: $VERIFICATION_CODE/" "$doc"
    
    # Update VERIFICATION_CONFIRMATION
    sed -i "s/VERIFICATION_CONFIRMATION:.*$/VERIFICATION_CONFIRMATION: $VERIFICATION_CODE/" "$doc"
    
    # Update LAST_UPDATED date
    sed -i "s/LAST_UPDATED:.*$/LAST_UPDATED: $CURRENT_DATE/" "$doc"
    
    echo "  - Updated verification strings to: $VERIFICATION_CODE"
    echo "  - Updated last modified date to: $CURRENT_DATE"
}

# Find all Claude-to-Claude documents
echo "Searching for Claude-to-Claude documents..."
claude_docs=$(grep -l "CLAUDE_PROTOCOL" $(find docs -name "*.md"))

# Update each document
echo "Found $(echo "$claude_docs" | wc -l) Claude-to-Claude documents."
echo "Updating all documents with verification code: $VERIFICATION_CODE"

for doc in $claude_docs; do
    update_document "$doc"
done

echo "Verification update complete!"
echo "All Claude-to-Claude documents now use verification code: $VERIFICATION_CODE"
