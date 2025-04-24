"""
Setup script for the DC implementation.
This registers all available tools with the registry.
"""

import logging

# Import from our namespace-isolated modules
from .registry.dc_registry import (
    DC_COMPUTER_TOOL,
    DC_BASH_TOOL,
    dc_register_tool
)
from .tools.dc_adapters import (
    dc_execute_computer_tool,
    dc_execute_bash_tool,
    dc_validate_computer_parameters,
    dc_validate_bash_parameters
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_setup")

def dc_initialize():
    """
    Initialize the DC implementation by registering all tools.
    Uses namespace isolation to avoid conflicts.
    """
    logger.info("Initializing DC implementation")
    
    # Register the computer tool
    dc_register_tool(
        name="dc_computer",
        definition=DC_COMPUTER_TOOL,
        executor=dc_execute_computer_tool,
        validator=dc_validate_computer_parameters
    )
    logger.info("Registered DC computer tool")
    
    # Register the bash tool
    dc_register_tool(
        name="dc_bash",
        definition=DC_BASH_TOOL,
        executor=dc_execute_bash_tool,
        validator=dc_validate_bash_parameters
    )
    logger.info("Registered DC bash tool")
    
    logger.info("DC implementation initialized successfully")