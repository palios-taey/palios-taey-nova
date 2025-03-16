#!/bin/bash

# Script to update verification strings in Claude-to-Claude documents
# Usage: ./update_verification.sh -f DOCUMENT_FILE [-c CODE]

# Display help
show_help() {
    echo "Usage: $0 -f DOCUMENT_FILE [-c VERIFICATION_CODE]"
    echo ""
    echo "Options:"
    echo "  -f DOCUMENT_FILE       Claude-to-Claude document to update"
    echo "  -c VERIFICATION_CODE   Custom verification code (default: auto-generated using filename and date)"
    echo ""
    echo "Example: $0 -f docs/claude/document_structure.md"
    echo "         $0 -f docs/claude/quality_framework.md -c QUALITY_FRAMEWORK_VERIFIED_20250317"
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
while getopts "f:c:h" opt; do
    case $opt in
        f) DOCUMENT_FILE=$OPTARG ;;
        c) VERIFICATION_CODE=$OPTARG ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Validate file argument
if [ -z "$DOCUMENT_FILE" ] || [ ! -f "$DOCUMENT_FILE" ]; then
    echo "Error: Document file does not exist or was not specified"
    show_help
fi

# Check if file is a Claude-to-Claude document
if ! grep -q "CLAUDE_PROTOCOL" "$DOCUMENT_FILE"; then
    echo "Error: This doesn't appear to be a Claude-to-Claude document (missing CLAUDE_PROTOCOL header)"
    exit 1
fi

# Generate verification code if not provided
if [ -z "$VERIFICATION_CODE" ]; then
    # Extract document name from filepath and convert to uppercase
    DOC_NAME=$(basename "$DOCUMENT_FILE" .md | tr '[:lower:]' '[:upper:]' | tr '-' '_')
    CURRENT_DATE=$(date +%Y%m%d)
    VERIFICATION_CODE="${DOC_NAME}_VERIFICATION_${CURRENT_DATE}"
    echo "Generated verification code: $VERIFICATION_CODE"
fi

# Update VERIFICATION_STRING
sed -i "s/VERIFICATION_STRING:.*$/VERIFICATION_STRING: $VERIFICATION_CODE/" "$DOCUMENT_FILE"

# Update VERIFICATION_CONFIRMATION
sed -i "s/VERIFICATION_CONFIRMATION:.*$/VERIFICATION_CONFIRMATION: $VERIFICATION_CODE/" "$DOCUMENT_FILE"

# Also update LAST_UPDATED date
CURRENT_DATE=$(date +%Y-%m-%d)
sed -i "s/LAST_UPDATED:.*$/LAST_UPDATED: $CURRENT_DATE/" "$DOCUMENT_FILE"

echo "Verification strings updated in $DOCUMENT_FILE"
echo "VERIFICATION_STRING and VERIFICATION_CONFIRMATION set to: $VERIFICATION_CODE"
echo "LAST_UPDATED set to: $CURRENT_DATE"
