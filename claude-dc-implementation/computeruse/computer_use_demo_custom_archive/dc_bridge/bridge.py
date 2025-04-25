"""
Bridge module to access DC Custom Implementation.
This module provides access to the custom implementation without directly
modifying production code.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dc_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dc_bridge")

# Add GitHub directory to path
GITHUB_DIR = Path("/home/computeruse/github/palios-taey-nova")
if str(GITHUB_DIR) not in sys.path:
    sys.path.insert(0, str(GITHUB_DIR))
    logger.info(f"Added {GITHUB_DIR} to sys.path")

# Import from custom implementation
try:
    # Add the dc_custom directory to the path
    DC_CUSTOM_DIR = Path("/home/computeruse/computer_use_demo/dc_custom")
    if str(DC_CUSTOM_DIR) not in sys.path:
        sys.path.insert(0, str(DC_CUSTOM_DIR))
        logger.info(f"Added {DC_CUSTOM_DIR} to sys.path")
    
    # Import directly
    from dc_setup import dc_initialize
    from dc_executor import dc_execute_tool
    
    # Initialize the implementation
    dc_initialize()
    logger.info("Successfully imported and initialized DC Custom Implementation")
    DC_CUSTOM_AVAILABLE = True
except Exception as e:
    logger.error(f"Error importing DC Custom Implementation: {str(e)}")
    DC_CUSTOM_AVAILABLE = False

async def execute_tool(tool_name, tool_input):
    """
    Execute a tool using the custom implementation.
    Falls back to mock implementation if real tools are unavailable.
    """
    if not DC_CUSTOM_AVAILABLE:
        logger.warning("DC Custom Implementation unavailable, using mock implementation")
        # Return a mock result
        return {"output": f"Mock execution of {tool_name} with input {tool_input}"}
    
    try:
        # Execute the tool using the custom implementation
        result = await dc_execute_tool(tool_name, tool_input)
        
        # Convert to the format expected by production
        return {
            "output": result.output,
            "error": result.error,
            "base64_image": result.base64_image
        }
    except Exception as e:
        logger.error(f"Error executing tool with custom implementation: {str(e)}")
        # Return an error result
        return {"error": f"Error: {str(e)}"}
