#!/bin/bash
# Script to clean up and organize the DCCC directories

echo "Starting directory cleanup for DCCC..."

# Base paths
BASE_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse"
ARCHIVE_DIR="$BASE_DIR/archive"

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Move old documentation to archive
echo "Moving old documentation to archive..."
mkdir -p "$ARCHIVE_DIR/old_docs"

# List of files to archive
OLD_DOCS=(
  "$BASE_DIR/grok-anthropics-streaming.md"
  "$BASE_DIR/claude_chat_prompt.md"
  "$BASE_DIR/references/claude-optimization-research.md"
  "$BASE_DIR/references/claude-dc-errors.md"
  "$BASE_DIR/references/claude-code-claude-dc.md"
  "$BASE_DIR/references/not-yet/*"
  "$BASE_DIR/references/claude-chat-custom-computeruse.md"
  "$BASE_DIR/current_experiment/CLAUDE_CODE_TERMINAL_FIX.md"
  "$BASE_DIR/current_experiment/CLAUDE_DC_ONBOARDING.md"
  "$BASE_DIR/current_experiment/claude-example.md"
  "$BASE_DIR/current_experiment/encoding_fix/CLAUDE_CODE_ENCODING_FIX.md"
)

# Move each file to archive
for file in "${OLD_DOCS[@]}"; do
  if [ -f "$file" ]; then
    echo "Archiving $file"
    cp "$file" "$ARCHIVE_DIR/old_docs/"
    rm "$file"
  elif [ -d "$file" ]; then
    echo "Archiving directory $file"
    cp -r "$file"/* "$ARCHIVE_DIR/old_docs/"
    rm -rf "$file"
  fi
done

# Organize custom implementation directories
echo "Organizing custom implementation..."
mkdir -p "$BASE_DIR/custom_implementation"

# Copy current implementation files to organized directory
if [ -d "$BASE_DIR/computer_use_demo_custom" ]; then
  cp -r "$BASE_DIR/computer_use_demo_custom"/* "$BASE_DIR/custom_implementation/"
fi

# Move implementation files to archive if they exist in both places
if [ -d "$BASE_DIR/custom_implementation" ] && [ -d "$BASE_DIR/computer_use_demo_custom" ]; then
  mkdir -p "$ARCHIVE_DIR/old_implementation"
  cp -r "$BASE_DIR/computer_use_demo_custom" "$ARCHIVE_DIR/old_implementation/"
fi

# Create documentation directory
echo "Creating documentation directory..."
mkdir -p "$BASE_DIR/docs"

# Move new documentation to docs directory
cp "$BASE_DIR/DCCC_CLAUDE_DC_GUIDE.md" "$BASE_DIR/docs/"
cp "$BASE_DIR/DCCC_CLAUDE_CODE_GUIDE.md" "$BASE_DIR/docs/"
cp "$BASE_DIR/DCCC_INTEGRATION_PLAN.md" "$BASE_DIR/docs/"
cp "$BASE_DIR/DCCC_TECHNICAL_REFERENCE.md" "$BASE_DIR/docs/"

# Update reference documentation
echo "Updating reference documentation..."
cp "$BASE_DIR/references/claude-dc-setup-prompt-updated.md" "$BASE_DIR/references/claude-dc-setup-prompt.md"

# Create blank cache directory
mkdir -p "$BASE_DIR/cache"
touch "$BASE_DIR/cache/README.md"
echo "# Cache Directory\n\nThis directory is used for storing cached data during DCCC operations." > "$BASE_DIR/cache/README.md"

echo "Cleanup complete!"
echo "New documentation is in $BASE_DIR/docs/"
echo "Archived files are in $ARCHIVE_DIR/"
echo "Updated setup prompt is at $BASE_DIR/references/claude-dc-setup-prompt.md"