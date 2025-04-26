#!/bin/bash
# Enhanced launcher for Claude DC with automated environment setup

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file location
LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/claude_dc_launch.log"
DEBUG_LOG="$LOG_DIR/launcher_debug.log"

# Print a message to console and log it
log() {
  local message="$1"
  local level="$2"
  local color="$NC"
  
  case "$level" in
    "INFO") color="$BLUE" ;;
    "SUCCESS") color="$GREEN" ;;
    "WARNING") color="$YELLOW" ;;
    "ERROR") color="$RED" ;;
  esac
  
  echo -e "${color}${message}${NC}"
  echo "$(date '+%Y-%m-%d %H:%M:%S') [${level}] ${message}" >> "$LOG_FILE"
}

log "Starting Claude DC..." "INFO"
log "Logging to: $LOG_FILE" "INFO"

# Check for Python
if ! command -v python3 &> /dev/null; then
  log "Python not found! Please install Python 3.9 or later." "ERROR"
  exit 1
fi

# Check for Anthropic API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  log "WARNING: ANTHROPIC_API_KEY environment variable not set" "WARNING"
  log "You will need to enter your API key in the Claude DC interface" "WARNING"
fi

# Create initial API test (minimal_direct_claude.py)
if [ -f "$(dirname "$0")/minimal_direct_claude.py" ]; then
  log "Running API connectivity test..." "INFO"
  python "$(dirname "$0")/minimal_direct_claude.py" >> "$DEBUG_LOG" 2>&1
  if [ $? -eq 0 ]; then
    log "API connectivity test passed!" "SUCCESS"
  else
    log "API connectivity test had issues. Check $DEBUG_LOG for details." "WARNING"
    log "Continuing with launch anyway..." "INFO"
  fi
else
  log "API test script not found. Skipping API test." "WARNING"
fi

# Ensure requirements are installed
log "Checking requirements..." "INFO"
if [ -f "$(dirname "$0")/requirements.txt" ]; then
  pip install -r "$(dirname "$0")/requirements.txt" >> "$DEBUG_LOG" 2>&1
  if [ $? -eq 0 ]; then
    log "Dependencies installed successfully" "SUCCESS"
  else
    log "Warning: Some dependencies may not have installed correctly" "WARNING"
  fi
else
  log "No requirements.txt found. Skipping dependency check." "WARNING"
fi

# Change to the script directory
cd "$(dirname "$0")"

# Attempt to launch using launch_claude_dc.py if it exists
if [ -f "launch_claude_dc.py" ]; then
  log "Launching Claude DC with Python launcher..." "INFO"
  python launch_claude_dc.py >> "$DEBUG_LOG" 2>&1 &
  
  # Store the PID for later cleanup
  CLAUDE_PID=$!
  
  # Check if process started successfully
  if ps -p $CLAUDE_PID > /dev/null; then
    log "Claude DC started with PID: $CLAUDE_PID" "SUCCESS"
    log "Started a new Claude DC instance at: $(date)" "INFO"
  else
    log "Failed to start Claude DC with Python launcher" "ERROR"
    log "Falling back to direct Streamlit launch..." "INFO"
  fi
else
  # Fall back to direct Streamlit launch
  log "Launching Claude DC directly with Streamlit..." "INFO"
  streamlit run claude_ui.py >> "$DEBUG_LOG" 2>&1 &
  
  # Store the PID for later cleanup
  CLAUDE_PID=$!
  
  if ps -p $CLAUDE_PID > /dev/null; then
    log "Claude DC started with PID: $CLAUDE_PID" "SUCCESS"
    log "Started a new Claude DC instance at: $(date)" "INFO"
  else
    log "Failed to start Claude DC" "ERROR"
    exit 1
  fi
fi

# Print a nice welcome message
log "\n${GREEN}==================================================${NC}" "INFO"
log "${GREEN}    Claude DC is running on http://localhost:8501    ${NC}" "INFO"
log "${GREEN}==================================================${NC}" "INFO"
log "\nOpen your browser and go to http://localhost:8501 to access Claude DC" "INFO"
log "Press Ctrl+C to stop Claude DC" "INFO"

# Trap Ctrl+C to clean up
trap "log 'Stopping Claude DC...' 'INFO'; kill $CLAUDE_PID 2>/dev/null; log 'Claude DC stopped' 'SUCCESS'; exit 0" INT TERM

# Wait for the process to finish
wait $CLAUDE_PID