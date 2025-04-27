#!/bin/bash
# Deployment script for Claude DC Computer Use implementation
# This script safely deploys the custom implementation to the production environment

set -e  # Exit on error

# Configuration - adjust these paths for your environment
SOURCE_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom"
TARGET_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
BACKUP_DIR="${TARGET_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

# Log file
LOG_FILE="deploy.log"

# Function to log a message
log() {
  echo "$(date "+%Y-%m-%d %H:%M:%S") - $1" | tee -a $LOG_FILE
}

# Function to check for required tools
check_dependencies() {
  log "Checking dependencies..."
  
  # Check Python
  if ! command -v python3 &> /dev/null; then
    log "Error: Python 3 is required but not installed."
    exit 1
  fi
  
  # Check required Python packages
  python3 -c "import sys; packages = ['anthropic', 'streamlit', 'nest_asyncio', 'PIL']; missing = [p for p in packages if p not in sys.modules and not __import__(p, fromlist=[''])]; exit(1 if missing else 0)" 2>/dev/null
  
  if [ $? -ne 0 ]; then
    log "Warning: Some required Python packages are not installed."
    log "Installing dependencies from requirements.txt..."
    pip install -r "$SOURCE_DIR/requirements.txt"
  fi
  
  log "Dependency check complete."
}

# Function to create a backup of the current production environment
create_backup() {
  log "Creating backup of current production environment..."
  
  if [ ! -d "$TARGET_DIR" ]; then
    log "Warning: Target directory does not exist, creating it."
    mkdir -p "$TARGET_DIR"
    return
  fi
  
  # Create backup directory
  mkdir -p "$BACKUP_DIR"
  
  # Copy all files from target directory to backup
  cp -r "$TARGET_DIR"/* "$BACKUP_DIR"/ 2>/dev/null || true
  
  # Create a manifest file
  find "$BACKUP_DIR" -type f -not -path "*/\.*" | sort > "$BACKUP_DIR/manifest.txt"
  
  log "Backup created at $BACKUP_DIR"
}

# Function to deploy the implementation
deploy_implementation() {
  log "Deploying implementation to production environment..."
  
  # Create target directory if it doesn't exist
  mkdir -p "$TARGET_DIR"
  
  # Copy core files
  cp "$SOURCE_DIR/loop.py" "$TARGET_DIR/loop.py"
  cp "$SOURCE_DIR/streamlit.py" "$TARGET_DIR/streamlit.py"
  cp "$SOURCE_DIR/requirements.txt" "$TARGET_DIR/requirements.txt"
  
  # Create and copy tools directory
  mkdir -p "$TARGET_DIR/tools"
  cp "$SOURCE_DIR/tools/__init__.py" "$TARGET_DIR/tools/__init__.py"
  cp "$SOURCE_DIR/tools/bash.py" "$TARGET_DIR/tools/bash.py"
  cp "$SOURCE_DIR/tools/computer.py" "$TARGET_DIR/tools/computer.py"
  
  # Create __init__.py file in root directory
  touch "$TARGET_DIR/__init__.py"
  
  # Create README file
  cat > "$TARGET_DIR/README.md" << EOF
# Claude Computer Use Implementation

This is a custom implementation of the Computer Use functionality with the following features:

- Streaming responses with token-by-token output
- Tool use integrated with streaming
- Thinking token budget management
- Extended output support (128K)
- Prompt caching

## Usage

Run the Streamlit UI:
\`\`\`bash
streamlit run streamlit.py
\`\`\`

Run the command-line interface:
\`\`\`bash
python loop.py
\`\`\`

## Configuration

Configuration options can be set in the Streamlit UI or via environment variables:

- ANTHROPIC_API_KEY: Your Claude API key
- MODEL: The Claude model to use (default: claude-3-7-sonnet-20250219)
- MAX_TOKENS: Maximum tokens in the response (default: 16000)
- THINKING_BUDGET: Budget for thinking tokens (default: 4000)

## Key Features

1. **Fixed Beta Flags Implementation**
   - Corrected issues with beta flag format and usage
   - Implemented a dictionary-based approach for clarity and maintainability

2. **Thinking Capability Fix**
   - Correctly implemented thinking as a parameter in the request body, not as a beta flag
   - Set proper minimum budget of 1024 tokens

3. **Streaming Implementation**
   - Implemented proper event handling for different chunk types
   - Added state tracking for content blocks

4. **Tool Integration**
   - Added comprehensive parameter validation
   - Implemented type checking for parameters
   - Added required parameter verification

5. **Error Handling**
   - Specific exception types for different error scenarios
   - Detailed error messages for debugging
   - Recovery mechanisms for API errors
EOF

  log "Implementation deployed to $TARGET_DIR"
}

# Function to verify the deployment
verify_deployment() {
  log "Verifying deployment..."
  
  # Check if core files exist
  if [ ! -f "$TARGET_DIR/loop.py" ] || [ ! -f "$TARGET_DIR/streamlit.py" ]; then
    log "Error: Core files are missing after deployment."
    revert_to_backup
    exit 1
  fi
  
  # Check if Python files are valid
  if ! python3 -m py_compile "$TARGET_DIR/loop.py" 2>/dev/null; then
    log "Error: loop.py contains syntax errors."
    revert_to_backup
    exit 1
  fi
  
  if ! python3 -m py_compile "$TARGET_DIR/streamlit.py" 2>/dev/null; then
    log "Error: streamlit.py contains syntax errors."
    revert_to_backup
    exit 1
  fi
  
  log "Deployment verification complete. All files appear to be valid."
}

# Function to revert to backup
revert_to_backup() {
  log "Reverting to backup..."
  
  if [ ! -d "$BACKUP_DIR" ]; then
    log "Error: Backup directory does not exist, cannot revert."
    exit 1
  fi
  
  # Remove current files
  rm -rf "$TARGET_DIR"/*
  
  # Copy from backup
  cp -r "$BACKUP_DIR"/* "$TARGET_DIR"/ 2>/dev/null || true
  
  log "Reverted to backup from $BACKUP_DIR"
}

# Function to print deployment success message
print_success() {
  cat << EOF

=====================================
  Deployment Completed Successfully
=====================================

The Claude DC Computer Use implementation has been deployed to:
$TARGET_DIR

To run the Streamlit UI:
cd $TARGET_DIR && streamlit run streamlit.py

To run the command-line interface:
cd $TARGET_DIR && python3 loop.py

A backup of the previous implementation is available at:
$BACKUP_DIR

EOF
}

# Main deployment process
main() {
  log "Starting deployment process..."
  
  # Check dependencies
  check_dependencies
  
  # Create backup
  create_backup
  
  # Deploy implementation
  deploy_implementation
  
  # Verify deployment
  verify_deployment
  
  # Print success message
  print_success
  
  log "Deployment completed successfully."
}

# Run the deployment
main