#!/bin/bash
# Streaming implementation deployment script

# Exit on error
set -e

# Define directories
SRC_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl"
DEST_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
BACKUP_DIR="${DEST_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

# Create backup of production environment
echo "Creating backup of production environment..."
mkdir -p "$BACKUP_DIR"
cp -r "$DEST_DIR"/* "$BACKUP_DIR/"
find "$BACKUP_DIR" -type f | sort > "$BACKUP_DIR/manifest.txt"
echo "Backup created at: $BACKUP_DIR"

# Create directory structure in production
echo "Creating directory structure in production..."
mkdir -p "$DEST_DIR/dc_impl"
mkdir -p "$DEST_DIR/dc_impl/models"
mkdir -p "$DEST_DIR/dc_impl/registry"
mkdir -p "$DEST_DIR/dc_impl/tools"
mkdir -p "$DEST_DIR/dc_impl/logs"
mkdir -p "$DEST_DIR/dc_impl/tests"

# Copy streaming implementation files
echo "Copying streaming implementation files..."
cp "$SRC_DIR/dc_streaming_agent_loop.py" "$DEST_DIR/dc_impl/"
cp "$SRC_DIR/dc_setup.py" "$DEST_DIR/dc_impl/"
cp "$SRC_DIR/dc_executor.py" "$DEST_DIR/dc_impl/"
cp "$SRC_DIR/models/dc_models.py" "$DEST_DIR/dc_impl/models/"
cp "$SRC_DIR/registry/dc_registry.py" "$DEST_DIR/dc_impl/registry/"
cp "$SRC_DIR/tools/dc_bash.py" "$DEST_DIR/dc_impl/tools/"
cp "$SRC_DIR/tools/dc_edit.py" "$DEST_DIR/dc_impl/tools/"
cp "$SRC_DIR/tools/dc_adapters.py" "$DEST_DIR/dc_impl/tools/"
cp "$SRC_DIR/tools/dc_real_adapters.py" "$DEST_DIR/dc_impl/tools/"

# Create adapter script in production
cat > "$DEST_DIR/streaming_adapter.py" << 'EOL'
"""
Adapter module for integrating streaming functionality.
"""

import asyncio
import os
import sys
from typing import Dict, Any, List, Optional, Callable
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streaming_adapter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("streaming_adapter")

# Try to import the streaming agent loop
try:
    from dc_impl.dc_streaming_agent_loop import dc_streaming_agent_loop, DcStreamingSession
    streaming_available = True
    logger.info("Streaming implementation available")
except ImportError as e:
    streaming_available = False
    logger.error(f"Failed to import streaming implementation: {str(e)}")

# Feature flag from environment or config
USE_STREAMING = os.environ.get("USE_STREAMING", "false").lower() == "true"
logger.info(f"Streaming feature flag: {USE_STREAMING}")

# Define path to original agent loop for fallback
# The exact import will depend on your environment
def get_original_agent_loop():
    try:
        # This should point to your existing agent loop implementation
        # Adjust as needed for your specific environment
        from loop import agent_loop as original_agent_loop
        return original_agent_loop
    except ImportError as e:
        logger.error(f"Failed to import original agent loop: {str(e)}")
        raise

async def agent_loop(
    user_input: str, 
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    **kwargs
):
    """
    Adapter function that supports both streaming and non-streaming.
    Uses the streaming implementation if available and enabled.
    """
    # Check if streaming is available and enabled
    if streaming_available and USE_STREAMING:
        try:
            logger.info(f"Using streaming implementation for: {user_input[:30]}...")
            # Use streaming implementation
            return await dc_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}, falling back to non-streaming")
            # Fall back to non-streaming if streaming fails
            original_agent_loop = get_original_agent_loop()
            return await original_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
    else:
        logger.info(f"Using non-streaming implementation for: {user_input[:30]}...")
        # Use existing implementation
        original_agent_loop = get_original_agent_loop()
        return await original_agent_loop(
            user_input=user_input,
            conversation_history=conversation_history,
            **kwargs
        )
EOL

# Create initialization files
cat > "$DEST_DIR/dc_impl/__init__.py" << 'EOL'
"""
DC Implementation with streaming support.
"""
EOL

cat > "$DEST_DIR/dc_impl/models/__init__.py" << 'EOL'
"""
DC model definitions.
"""
EOL

cat > "$DEST_DIR/dc_impl/registry/__init__.py" << 'EOL'
"""
DC tool registry.
"""
EOL

cat > "$DEST_DIR/dc_impl/tools/__init__.py" << 'EOL'
"""
DC tool implementations.
"""
EOL

# Create a simple test script
cat > "$DEST_DIR/test_streaming.py" << 'EOL'
#!/usr/bin/env python3
"""
Test script for the streaming implementation.
"""

import os
import asyncio
import argparse

async def test_streaming():
    """Test the streaming implementation."""
    try:
        # Import the streaming adapter
        from streaming_adapter import agent_loop, streaming_available, USE_STREAMING
        
        print(f"Streaming available: {streaming_available}")
        print(f"Streaming enabled: {USE_STREAMING}")
        
        # Set streaming flag temporarily for testing
        os.environ["USE_STREAMING"] = "true"
        
        # Simple test query
        user_input = "Hello, can you test the streaming implementation by running 'ls -la'?"
        
        # Run the agent loop
        conversation_history = await agent_loop(
            user_input=user_input,
            conversation_history=[]
        )
        
        print("\nTest completed successfully")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test streaming implementation")
    args = parser.parse_args()
    
    # Run the test
    asyncio.run(test_streaming())
EOL

# Make test script executable
chmod +x "$DEST_DIR/test_streaming.py"

echo "Deployment completed. To enable streaming, set USE_STREAMING=true in the environment."
echo "To test the implementation, run: python $DEST_DIR/test_streaming.py"