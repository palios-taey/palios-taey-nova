#!/bin/bash
# Script to update verification strings in all Claude-to-Claude documents
# Usage: ./update_all_verifications.sh -c [NEW_VERIFICATION_CODE]

# Process command line arguments
while getopts "c:" opt; do
  case $opt in
    c) NEW_VERIFICATION_CODE="$OPTARG"
      ;;
    \?) echo "Invalid option -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Check if verification code is provided
if [ -z "$NEW_VERIFICATION_CODE" ]; then
  echo "Error: Verification code is required. Usage: $0 -c [VERIFICATION_CODE]"
  exit 1
fi

# Get current date in YYYY-MM-DD format
CURRENT_DATE=$(date +"%Y-%m-%d")

echo "Searching for Claude-to-Claude documents..."

# Find all Claude-to-Claude documents
CLAUDE_DOCS=$(find docs -type f -name "*.md" | xargs grep -l "CLAUDE_PROTOCOL" | sort)

# Count documents
DOC_COUNT=$(echo "$CLAUDE_DOCS" | wc -l | xargs)

echo "Found $DOC_COUNT Claude-to-Claude documents."
echo "Updating all documents with verification code: $NEW_VERIFICATION_CODE"

# Update each document
for DOC in $CLAUDE_DOCS; do
  echo "Updating verification strings in: $DOC"
  
  # Update VERIFICATION_STRING
  sed -i '' "s/\*\*VERIFICATION_STRING:\*\* [A-Z0-9_]*/**VERIFICATION_STRING:** $NEW_VERIFICATION_CODE/g" "$DOC"
  
  # Update VERIFICATION_CONFIRMATION
  sed -i '' "s/VERIFICATION_CONFIRMATION: [A-Z0-9_]*/VERIFICATION_CONFIRMATION: $NEW_VERIFICATION_CODE/g" "$DOC"
  
  # Update LAST_UPDATED date
  sed -i '' "s/\*\*LAST_UPDATED:\*\* [0-9-]*/**LAST_UPDATED:** $CURRENT_DATE/g" "$DOC"
  
  echo "  - Updated verification strings to: $NEW_VERIFICATION_CODE"
  echo "  - Updated last modified date to: $CURRENT_DATE"
done

echo "Verification update complete!"
echo "All Claude-to-Claude documents now use verification code: $NEW_VERIFICATION_CODE"