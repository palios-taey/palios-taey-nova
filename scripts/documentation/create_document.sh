#!/bin/bash

# Script to create a new document from a template

# Display help
show_help() {
    echo "Usage: $0 -t TEMPLATE_TYPE -n DOCUMENT_NAME -p PATH [-d DESCRIPTION]"
    echo ""
    echo "Options:"
    echo "  -t TEMPLATE_TYPE   Template type (claude, ai_ai, framework, implementation)"
    echo "  -n DOCUMENT_NAME   Document name (used in filename and title)"
    echo "  -p PATH            Path where the document should be created (without filename)"
    echo "  -d DESCRIPTION     Brief description (optional)"
    echo ""
    echo "Example: $0 -t claude -n quality_framework -p docs/claude -d \"Quality framework for code generation\""
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
while getopts "t:n:p:d:h" opt; do
    case $opt in
        t) TEMPLATE_TYPE=$OPTARG ;;
        n) DOCUMENT_NAME=$OPTARG ;;
        p) PATH_TO_CREATE=$OPTARG ;;
        d) DESCRIPTION=$OPTARG ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Validate required arguments
if [ -z "$TEMPLATE_TYPE" ] || [ -z "$DOCUMENT_NAME" ] || [ -z "$PATH_TO_CREATE" ]; then
    echo "Error: Missing required arguments"
    show_help
fi

# Validate template type
if [ "$TEMPLATE_TYPE" != "claude" ] && [ "$TEMPLATE_TYPE" != "ai_ai" ] && [ "$TEMPLATE_TYPE" != "framework" ] && [ "$TEMPLATE_TYPE" != "implementation" ]; then
    echo "Error: Invalid template type. Must be one of: claude, ai_ai, framework, implementation"
    exit 1
fi

# Create filename
FILENAME="${DOCUMENT_NAME}.md"
FULL_PATH="${PATH_TO_CREATE}/${FILENAME}"

# Check if file already exists
if [ -f "$FULL_PATH" ]; then
    echo "Error: File already exists at $FULL_PATH"
    exit 1
fi

# Create directory if it doesn't exist
mkdir -p "$PATH_TO_CREATE"

# Copy template to destination
cp "docs/templates/${TEMPLATE_TYPE}_template.md" "$FULL_PATH"

# Replace placeholders
TITLE_CASE_NAME=$(echo "$DOCUMENT_NAME" | sed -e 's/_/ /g' -e 's/\b\(.\)/\u\1/g')
CURRENT_DATE=$(date +%Y-%m-%d)

if [ "$TEMPLATE_TYPE" == "claude" ]; then
    # Replace in Claude template
    sed -i "s/DOCUMENT_TITLE/$TITLE_CASE_NAME/g" "$FULL_PATH"
    sed -i "s/DOCUMENT_TYPE/$(echo $DOCUMENT_NAME | tr '[:lower:]' '[:upper:]')/g" "$FULL_PATH"
    sed -i "s/VERIFICATION_STRING_HERE/${DOCUMENT_NAME}_verification_$(date +%Y%m%d)/g" "$FULL_PATH"
    sed -i "s/YYYY-MM-DD/$CURRENT_DATE/g" "$FULL_PATH"
    if [ ! -z "$DESCRIPTION" ]; then
        sed -i "s/Brief description of the document's purpose and how it fits into the broader documentation ecosystem./$DESCRIPTION/g" "$FULL_PATH"
    fi
elif [ "$TEMPLATE_TYPE" == "ai_ai" ]; then
    # Replace in AI-AI template
    sed -i "s/Document Title/$TITLE_CASE_NAME/g" "$FULL_PATH"
    sed -i "s/DOCUMENT_ID/$(echo $DOCUMENT_NAME | cut -c 1-3)$(date +%y%m%d)/g" "$FULL_PATH"
    sed -i "s/DOCUMENT_TYPE/$(echo $DOCUMENT_NAME | tr '[:lower:]' '[:upper:]')/g" "$FULL_PATH"
    sed -i "s/YYYY-MM-DDThh:mm:ssZ/$(date -u +%Y-%m-%dT%H:%M:%SZ)/g" "$FULL_PATH"
    sed -i "s/YYYY-MM-DD/$CURRENT_DATE/g" "$FULL_PATH"
elif [ "$TEMPLATE_TYPE" == "framework" ] || [ "$TEMPLATE_TYPE" == "implementation" ]; then
    # Replace in framework or implementation template
    sed -i "s/Framework Title/$TITLE_CASE_NAME/g" "$FULL_PATH"
    sed -i "s/Implementation Guide: \[Component Name\]/Implementation Guide: $TITLE_CASE_NAME/g" "$FULL_PATH"
fi

echo "Created new $TEMPLATE_TYPE document at $FULL_PATH"
