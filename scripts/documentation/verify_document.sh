#!/bin/bash

# Script to verify document format and links

# Display help
show_help() {
    echo "Usage: $0 [-d DIRECTORY] [-f FILE]"
    echo ""
    echo "Options:"
    echo "  -d DIRECTORY  Directory to verify (recursive)"
    echo "  -f FILE       Single file to verify"
    echo ""
    echo "Example: $0 -d docs/claude"
    echo "         $0 -f docs/claude/quality_framework.md"
    exit 1
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
fi

# Parse arguments
while getopts "d:f:h" opt; do
    case $opt in
        d) DIRECTORY=$OPTARG ;;
        f) FILE=$OPTARG ;;
        h) show_help ;;
        *) show_help ;;
    esac
done

# Function to verify a single file
verify_file() {
    local file=$1
    local errors=0
    
    echo "Verifying $file..."
    
    # Check file extension
    if [[ "$file" != *.md ]]; then
        echo "  ERROR: File does not have .md extension"
        errors=$((errors+1))
    fi
    
    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "  ERROR: File does not exist"
        return 1
    fi
    
    # Determine file type based on content
    if grep -q "CLAUDE_PROTOCOL_V1.0:MTD" "$file"; then
        # Claude format checks
        if ! grep -q "VERIFICATION_STRING:" "$file"; then
            echo "  ERROR: Missing VERIFICATION_STRING in Claude document"
            errors=$((errors+1))
        fi
        
        if ! grep -q "VERIFICATION_CONFIRMATION:" "$file"; then
            echo "  ERROR: Missing VERIFICATION_CONFIRMATION in Claude document"
            errors=$((errors+1))
        fi
        
        # Verify VERIFICATION_STRING matches VERIFICATION_CONFIRMATION
        VS=$(grep "VERIFICATION_STRING:" "$file" | sed 's/^.*VERIFICATION_STRING: \(.*\)$/\1/')
        VC=$(grep "VERIFICATION_CONFIRMATION:" "$file" | sed 's/^.*VERIFICATION_CONFIRMATION: \(.*\)$/\1/')
        
        if [ "$VS" != "$VC" ]; then
            echo "  ERROR: VERIFICATION_STRING does not match VERIFICATION_CONFIRMATION"
            errors=$((errors+1))
        fi
    elif grep -q "RSPROTV1" "$file"; then
        # AI-AI format checks
        if ! grep -q "AISTRUCT:" "$file"; then
            echo "  ERROR: Missing AISTRUCT section in AI-AI document"
            errors=$((errors+1))
        fi
    fi
    
    # Check for broken internal links
    LINKS=$(grep -o '\[.*\](\/docs\/.*\.md)' "$file" | sed 's/.*(\(\/docs\/.*\.md\))/\1/')
    for link in $LINKS; do
        # Remove leading slash for file path check
        link_path="${link:1}"
        if [ ! -f "$link_path" ]; then
            echo "  ERROR: Broken internal link to $link_path"
            errors=$((errors+1))
        fi
    done
    
    # Return results
    if [ $errors -eq 0 ]; then
        echo "  PASS: Document verification successful"
        return 0
    else
        echo "  FAIL: Document has $errors errors"
        return 1
    fi
}

# Verify based on input type
if [ ! -z "$FILE" ]; then
    # Verify single file
    verify_file "$FILE"
    exit $?
elif [ ! -z "$DIRECTORY" ]; then
    # Verify all markdown files in directory recursively
    if [ ! -d "$DIRECTORY" ]; then
        echo "Error: Directory $DIRECTORY does not exist"
        exit 1
    fi
    
    echo "Verifying all documents in $DIRECTORY..."
    
    # Find all markdown files
    FILES=$(find "$DIRECTORY" -name "*.md")
    
    # Count variables
    total=0
    passed=0
    failed=0
    
    # Verify each file
    for file in $FILES; do
        total=$((total+1))
        if verify_file "$file"; then
            passed=$((passed+1))
        else
            failed=$((failed+1))
        fi
    done
    
    # Summary
    echo ""
    echo "Verification Summary:"
    echo "  Total files: $total"
    echo "  Passed: $passed"
    echo "  Failed: $failed"
    
    if [ $failed -eq 0 ]; then
        echo "All documents verified successfully!"
        exit 0
    else
        echo "Some documents failed verification."
        exit 1
    fi
else
    show_help
fi
