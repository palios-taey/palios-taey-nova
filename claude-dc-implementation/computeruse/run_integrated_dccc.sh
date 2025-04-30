#!/bin/bash
# Script to launch the integrated DCCC environment

# Check if container ID is provided
if [ -z "$1" ]; then
  echo "Please provide the Docker container ID or name"
  echo "Usage: $0 <container_id>"
  exit 1
fi

CONTAINER_ID=$1
INTEGRATION_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse"
CONTAINER_TARGET="/home/computeruse"

echo "Starting DCCC Integration with container $CONTAINER_ID"

# Step 1: Create custom implementation directory in container
echo "Creating custom implementation directory in container..."
docker exec $CONTAINER_ID mkdir -p $CONTAINER_TARGET/computer_use_demo_custom

# Step 2: Copy integration files to the container
echo "Copying integration files to container..."
docker cp $INTEGRATION_DIR/integration_framework.py $CONTAINER_ID:$CONTAINER_TARGET/
docker cp $INTEGRATION_DIR/integrated_streamlit.py $CONTAINER_ID:$CONTAINER_TARGET/
docker cp $INTEGRATION_DIR/README_INTEGRATION.md $CONTAINER_ID:$CONTAINER_TARGET/

# Step 3: Copy custom implementation files to the container
echo "Copying custom implementation files to container..."
# First check if the custom directory exists
if [ -d "$INTEGRATION_DIR/computer_use_demo_custom" ]; then
  docker cp $INTEGRATION_DIR/computer_use_demo_custom/. $CONTAINER_ID:$CONTAINER_TARGET/computer_use_demo_custom/
else
  echo "Warning: Custom implementation directory not found. Only copying integration framework."
fi

# Step 4: Create an entry for the ROSETTA STONE protocol
echo "Creating ROSETTA STONE protocol module..."
docker exec $CONTAINER_ID bash -c "cat > $CONTAINER_TARGET/rosetta_stone.py << 'EOF'
\"\"\"
ROSETTA STONE Protocol for AI-to-AI Communication

This module implements the ROSETTA STONE protocol for efficient communication
between Claude DC, Claude Code, and Claude Chat.
\"\"\"

import re
from typing import Dict, List, Any, Tuple, Optional

def format_message(sender: str, topic: str, message: str) -> str:
    \"\"\"
    Format a message using the ROSETTA STONE protocol.
    
    Args:
        sender: The sender identifier
        topic: The message topic
        message: The message content
        
    Returns:
        Formatted message string
    \"\"\"
    # Count tokens (rough approximation)
    word_count = len(message.split())
    token_count = word_count * 1.3  # Rough estimate: 1.3 tokens per word
    
    # Format with protocol
    formatted = f\"[{sender}][{topic}][{message}] [TOKENS:{int(token_count)}]\"
    return formatted

def parse_message(formatted_message: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    \"\"\"
    Parse a message formatted with the ROSETTA STONE protocol.
    
    Args:
        formatted_message: The formatted message string
        
    Returns:
        Tuple of (sender, topic, message, token_count)
    \"\"\"
    pattern = r'\\[(.*?)\\]\\[(.*?)\\]\\[(.*?)\\](?: \\[TOKENS:(\\d+)\\])?'
    match = re.match(pattern, formatted_message)
    
    if match:
        sender = match.group(1)
        topic = match.group(2)
        message = match.group(3)
        token_count = int(match.group(4)) if match.group(4) else None
        return sender, topic, message, token_count
    
    # If not in protocol format, return the original message as content
    return None, None, formatted_message, None

# Example usage
if __name__ == \"__main__\":
    # Format a message
    formatted = format_message(
        \"DCCC\",
        \"IMPLEMENTATION\",
        \"Identified streaming API issue. Beta flags incorrectly passed via extra_body. Solution: pass directly as parameters.\"
    )
    print(formatted)
    
    # Parse a message
    sender, topic, message, tokens = parse_message(formatted)
    print(f\"Sender: {sender}\")
    print(f\"Topic: {topic}\")
    print(f\"Message: {message}\")
    print(f\"Tokens: {tokens}\")
EOF"

# Step 5: Create continuity module
echo "Creating continuity module..."
docker exec $CONTAINER_ID bash -c "cat > $CONTAINER_TARGET/continuity.py << 'EOF'
\"\"\"
Streamlit Continuity Module

This module provides functionality to maintain Streamlit state across reloads.
\"\"\"

import os
import json
import logging
import tempfile
from typing import Dict, Any, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("streamlit_continuity")

# Path for state storage
STATE_DIR = os.path.join(tempfile.gettempdir(), "streamlit_state")
os.makedirs(STATE_DIR, exist_ok=True)
STATE_FILE = os.path.join(STATE_DIR, "session_state.json")

def save_state(session_state: Dict[str, Any]) -> bool:
    \"\"\"
    Save Streamlit session state to a temporary file.
    
    Args:
        session_state: The Streamlit session state to save
        
    Returns:
        True if successful, False otherwise
    \"\"\"
    try:
        # Create a serializable copy of the state
        serializable_state = {}
        
        # Filter only serializable content
        for key, value in session_state.items():
            # Skip non-serializable types
            if key in ["_fixed_height", "_is_running", "widget_states", "initialized"]:
                continue
                
            try:
                # Test if it's JSON serializable
                json.dumps({key: value})
                serializable_state[key] = value
            except (TypeError, OverflowError):
                logger.warning(f"Skipping non-serializable state item: {key}")
        
        # Save to file with timestamp
        state_with_metadata = {
            "timestamp": time.time(),
            "state": serializable_state
        }
        
        with open(STATE_FILE, "w") as f:
            json.dump(state_with_metadata, f)
            
        logger.info(f"State saved to {STATE_FILE}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving state: {str(e)}")
        return False

def restore_state(session_state: Dict[str, Any]) -> bool:
    \"\"\"
    Restore Streamlit session state from a temporary file.
    
    Args:
        session_state: The Streamlit session state to update
        
    Returns:
        True if successful, False otherwise
    \"\"\"
    try:
        # Check if state file exists
        if not os.path.exists(STATE_FILE):
            logger.info("No saved state found")
            return False
        
        # Load state from file
        with open(STATE_FILE, "r") as f:
            state_data = json.load(f)
        
        saved_state = state_data.get("state", {})
        timestamp = state_data.get("timestamp", 0)
        
        # Check if state is recent enough (within 5 minutes)
        if time.time() - timestamp > 300:
            logger.info("Saved state is too old, not restoring")
            return False
        
        # Update session state with saved values
        for key, value in saved_state.items():
            session_state[key] = value
        
        logger.info(f"State restored from {STATE_FILE}")
        return True
    
    except Exception as e:
        logger.error(f"Error restoring state: {str(e)}")
        return False

# Example usage
if __name__ == \"__main__\":
    # Mock session state
    mock_state = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "conversation_mode": "chat"
    }
    
    # Save and restore
    save_state(mock_state)
    restored = {}
    restore_state(restored)
    
    print("Restored state:", restored)
EOF"

# Step 6: Launch the integrated UI
echo "Launching integrated UI..."
docker exec -d $CONTAINER_ID bash -c "cd $CONTAINER_TARGET && streamlit run integrated_streamlit.py"

echo "DCCC Integration launched!"
echo "Access the UI at: http://localhost:8501"
echo ""
echo "For VNC access: http://localhost:6080"
echo "For Regular UI: http://localhost:8080"