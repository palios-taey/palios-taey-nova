#!/bin/bash

# Script to analyze documentation statistics

# Display help
show_help() {
    echo "Usage: $0 [-d DOCS_DIR]"
    echo ""
    echo "Options:"
    echo "  -d DOCS_DIR       Docs directory to analyze (default: docs)"
    echo ""
    echo "Example: $0 -d docs"
    exit 1
}

# Parse arguments
DOCS_DIR="docs"

while getopts "d:h" opt; do
    case $opt in
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

# Calculate statistics
total_files=$(find "$DOCS_DIR" -name "*.md" -type f | wc -l)
claude_format=$(grep -l "CLAUDE_PROTOCOL" $(find "$DOCS_DIR" -name "*.md" -type f) | wc -l)
ai_ai_format=$(grep -l "RSPROTV" $(find "$DOCS_DIR" -name "*.md" -type f) | wc -l)
with_verification=$(grep -l "VERIFICATION_STRING" $(find "$DOCS_DIR" -name "*.md" -type f) | wc -l)

# Count internal links
total_links=0
broken_links=0

find "$DOCS_DIR" -name "*.md" -type f | while read -r file; do
    # Extract all internal links
    links=$(grep -o '\[.*\](\/docs\/.*\.md)' "$file" | sed 's/.*(\(\/docs\/.*\.md\))/\1/')
    
    # Count links
    link_count=$(echo "$links" | grep -v "^$" | wc -l)
    total_links=$((total_links + link_count))
    
    # Check for broken links
    for link in $links; do
        # Remove leading slash for file path check
        link_path="${link:1}"
        if [ ! -f "$link_path" ]; then
            broken_links=$((broken_links + 1))
        fi
    done
done

# Print statistics
echo "Documentation Statistics:"
echo "------------------------"
echo "Total Markdown Files: $total_files"
echo "Claude-to-Claude Format: $claude_format ($(($claude_format * 100 / $total_files))%)"
echo "AI-AI Format: $ai_ai_format ($(($ai_ai_format * 100 / $total_files))%)"
echo "With Verification: $with_verification ($(($with_verification * 100 / $total_files))%)"
echo "Total Internal Links: $total_links"
echo "Broken Links: $broken_links"
echo "Average Links per Document: $(($total_links / $total_files))"
