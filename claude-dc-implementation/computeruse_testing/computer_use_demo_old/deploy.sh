#!/bin/bash
# Deployment script for the custom production environment

# Exit on error
set -e

# Define paths
SOURCE_DIR="/home/computeruse/production_replacement"
TARGET_DIR="/home/computeruse/computer_use_demo"
BACKUP_DIR="/home/computeruse/computer_use_demo_backup_$(date +%Y%m%d_%H%M%S)"

# Parse arguments
VALIDATE_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--validate-only] [--force]"
            exit 1
            ;;
    esac
done

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory $TARGET_DIR does not exist"
    exit 1
fi

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

# Perform validation
echo "Validating implementation..."

# 1. Check Python syntax
echo "Checking Python syntax..."
python_files=$(find "$SOURCE_DIR" -name "*.py")
for file in $python_files; do
    echo "  Checking $file"
    python -m py_compile "$file" || {
        echo "Error: Syntax error in $file"
        exit 1
    }
done

# 2. Check for imports
echo "Checking imports..."
if ! python -c "import sys; sys.path.append('$SOURCE_DIR'); import loop; import claude_ui; from models import tool_models; from tools import registry, bash, edit, computer; from utils import streaming, error_handling"; then
    echo "Error: Import check failed"
    exit 1
fi

# 3. Run tests if they exist
if [ -d "$SOURCE_DIR/tests" ]; then
    echo "Running tests..."
    pushd "$SOURCE_DIR" > /dev/null
    PYTHONPATH="$SOURCE_DIR" python -m unittest discover -s tests || {
        echo "Error: Tests failed"
        if [ "$FORCE" != "true" ]; then
            echo "Use --force to deploy anyway"
            exit 1
        fi
        echo "Continuing deployment despite test failures (--force)"
    }
    popd > /dev/null
fi

# Exit if validation only
if [ "$VALIDATE_ONLY" = "true" ]; then
    echo "Validation successful. Exiting without deployment."
    exit 0
fi

# Create backup of current production
echo "Creating backup at $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp -r "$TARGET_DIR"/* "$BACKUP_DIR/"
find "$BACKUP_DIR" -type f | sort > "$BACKUP_DIR/manifest.txt"
echo "Backup created with $(wc -l < "$BACKUP_DIR/manifest.txt") files"

# Deploy the new implementation
echo "Deploying to $TARGET_DIR..."

# Clean the target directory
echo "Cleaning target directory..."
rm -rf "$TARGET_DIR"/*

# Copy the files
echo "Copying files..."
cp -r "$SOURCE_DIR"/* "$TARGET_DIR/"

# Ensure permissions are correct
echo "Setting permissions..."
chmod -R 755 "$TARGET_DIR"

# Ensure execute permissions for scripts
find "$TARGET_DIR" -name "*.sh" -exec chmod +x {} \;

# Create a deployment marker
echo "Creating deployment marker..."
echo "Deployed on $(date)" > "$TARGET_DIR/deployment.txt"
echo "Source: $SOURCE_DIR" >> "$TARGET_DIR/deployment.txt"
echo "Backup: $BACKUP_DIR" >> "$TARGET_DIR/deployment.txt"

echo "Deployment completed successfully."
echo "To verify, run: cd $TARGET_DIR && python -c 'import loop; import claude_ui; print(\"Import check passed\")'"
echo "To run the application: cd $TARGET_DIR && streamlit run claude_ui.py"
echo "To restore from backup if needed: cp -r $BACKUP_DIR/* $TARGET_DIR/"