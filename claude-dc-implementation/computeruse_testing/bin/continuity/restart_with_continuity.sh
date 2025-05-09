#!/bin/bash
# Restart Streamlit with continuity
# This script saves the current conversation state, restarts Streamlit,
# and restores the conversation state for continuity.

# Configuration
STATE_FILE="/tmp/conversation_state.json"
STREAMLIT_CMD="streamlit run app.py"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -s, --state-file     Specify path to state file (default: $STATE_FILE)"
    echo "  -c, --streamlit-cmd  Specify Streamlit command (default: $STREAMLIT_CMD)"
    echo "  -d, --dry-run        Show what would be done without executing"
    exit 1
}

# Parse command line arguments
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            ;;
        -s|--state-file)
            STATE_FILE="$2"
            shift 2
            ;;
        -c|--streamlit-cmd)
            STREAMLIT_CMD="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Print configuration
echo "== Streamlit Continuity =="
echo "State file: $STATE_FILE"
echo "Streamlit command: $STREAMLIT_CMD"
echo "Script directory: $SCRIPT_DIR"
echo "========================="

# Check if we're doing a dry run
if [ $DRY_RUN -eq 1 ]; then
    echo "[DRY RUN] The following commands would be executed:"
    echo "1. python3 $SCRIPT_DIR/save_conversation_state.py --output $STATE_FILE"
    echo "2. pkill -f 'streamlit run'"
    echo "3. CONTINUE_FROM=$STATE_FILE $STREAMLIT_CMD"
    exit 0
fi

# Save current conversation state
echo "Saving conversation state..."
python3 "$SCRIPT_DIR/save_conversation_state.py" --output "$STATE_FILE"
if [ $? -ne 0 ]; then
    echo "Error: Failed to save conversation state"
    exit 1
fi
echo "Conversation state saved to $STATE_FILE"

# Stop current Streamlit
echo "Stopping Streamlit..."
pkill -f "streamlit run"

# Wait a moment for Streamlit to stop
echo "Waiting for Streamlit to stop..."
sleep 2

# Restart with continuation flag
echo "Restarting Streamlit with continuation..."
CONTINUE_FROM="$STATE_FILE" $STREAMLIT_CMD

# Done
echo "Streamlit restarted with continuity"
exit 0