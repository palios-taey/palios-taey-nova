# Streaming Implementation Deployment Guide

This guide provides step-by-step instructions for deploying the streaming implementation to Claude DC's production environment.

## Prerequisites

1. Ensure the custom implementation works in the current environment
2. Create a backup of the production environment
3. Have Claude DC available to assist with the deployment process

## Deployment Steps

### 1. Create Backup of Production Environment

```bash
# Create a timestamped backup directory
BACKUP_DIR="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy all files from the production environment
cp -r /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* "$BACKUP_DIR/"

# Create a manifest of backed up files
find "$BACKUP_DIR" -type f | sort > "$BACKUP_DIR/manifest.txt"

echo "Backup created at: $BACKUP_DIR"
```

### 2. Prepare Deployment Files

The following files need to be deployed to the production environment:

1. **Core Streaming Loop**: `dc_streaming_agent_loop.py`
2. **Streaming Tool Implementations**:
   - `tools/dc_bash.py` - Streaming bash tool
   - `tools/dc_edit.py` - Streaming edit tool
3. **Supporting Files**:
   - `models/dc_models.py` - Model definitions
   - `registry/dc_registry.py` - Tool registry
   - `dc_setup.py` - Initialization script

### 3. Integration with Production

For a phased approach, create an adapter layer in the production environment:

```python
# streaming_adapter.py - Place this in the production environment

import asyncio
import os
import sys
from typing import Dict, Any, List, Optional, Callable

# Import the streaming agent loop
try:
    # Adjust paths as needed for your environment
    from dc_impl.dc_streaming_agent_loop import dc_streaming_agent_loop, DcStreamingSession
    streaming_available = True
except ImportError:
    streaming_available = False

# Import the original agent loop for fallback
from existing_agent_loop import execute_agent_loop

# Feature flag from environment or config
USE_STREAMING = os.environ.get("USE_STREAMING", "false").lower() == "true"

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
            # Use streaming implementation
            return await dc_streaming_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
        except Exception as e:
            print(f"Streaming error: {str(e)}, falling back to non-streaming")
            # Fall back to non-streaming if streaming fails
            return await execute_agent_loop(
                user_input=user_input,
                conversation_history=conversation_history,
                **kwargs
            )
    else:
        # Use existing implementation
        return await execute_agent_loop(
            user_input=user_input,
            conversation_history=conversation_history,
            **kwargs
        )
```

### 4. Integration Script

Create a script to help Claude DC integrate the streaming implementation:

```bash
#!/bin/bash
# deploy_streaming.sh - Streaming deployment script

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

# Create initialization file
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
```

### 5. Deployment with Claude DC

Claude DC should deploy the streaming implementation with the following steps:

1. Review the implementation to ensure it meets requirements
2. Create a backup of the production environment
3. Run the deployment script to copy the files
4. Test the implementation with the test script
5. Integrate the adapter into the production loop

### 6. Verifying the Deployment

Claude DC should verify the deployment with these steps:

1. Run the test script to ensure streaming works
2. Test with a simple non-tool query to verify streaming text
3. Test with a tool-using query to verify tool integration
4. Check logs for any errors or issues
5. Verify that the fallback mechanism works

### 7. Enabling for Production

After successful testing, Claude DC can enable streaming for production:

```bash
# Set the environment variable to enable streaming
export USE_STREAMING=true

# Alternatively, add to the environment configuration
echo "USE_STREAMING=true" >> /home/jesse/projects/palios-taey-nova/.env
```

## Rollback Procedure

If issues are encountered, Claude DC can roll back the deployment:

```bash
# Disable streaming
export USE_STREAMING=false

# If needed, restore from backup
BACKUP_DIR="/path/to/backup/directory"  # From step 1
cp -r "$BACKUP_DIR"/* /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/
```

## Next Steps

After successful deployment, Claude DC can:

1. Monitor the streaming implementation for any issues
2. Gradually expand the streaming capabilities with additional tools
3. Implement prompt caching and extended output features
4. Explore UI enhancements to take advantage of streaming