"""
Setup script for the DC implementation.
This registers all available tools with the registry.
"""

import logging
import os
import sys
from pathlib import Path

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    from registry.dc_registry import (
        DC_COMPUTER_TOOL,
        DC_BASH_TOOL,
        DC_EDIT_TOOL,
        dc_register_tool
    )
    from tools.dc_adapters import (
        dc_execute_computer_tool,
        dc_execute_bash_tool,
        dc_validate_computer_parameters,
        dc_validate_bash_parameters
    )
    # Import edit tool
    try:
        from tools.dc_edit import (
            dc_execute_edit_tool,
            dc_validate_edit_parameters
        )
        edit_tool_available = True
    except ImportError:
        edit_tool_available = False
    # Try to import real adapters if available
    try:
        from tools.dc_real_adapters import (
            dc_execute_computer_tool_real,
            dc_execute_bash_tool_real,
            dc_execute_edit_tool_real
        )
        real_adapters_available = True
    except ImportError:
        real_adapters_available = False
except ImportError:
    # When imported as a package
    from .registry.dc_registry import (
        DC_COMPUTER_TOOL,
        DC_BASH_TOOL,
        DC_EDIT_TOOL,
        dc_register_tool
    )
    from .tools.dc_adapters import (
        dc_execute_computer_tool,
        dc_execute_bash_tool,
        dc_validate_computer_parameters,
        dc_validate_bash_parameters
    )
    # Import edit tool
    try:
        from .tools.dc_edit import (
            dc_execute_edit_tool,
            dc_validate_edit_parameters
        )
        edit_tool_available = True
    except ImportError:
        edit_tool_available = False
    # Try to import real adapters if available
    try:
        from .tools.dc_real_adapters import (
            dc_execute_computer_tool_real,
            dc_execute_bash_tool_real,
            dc_execute_edit_tool_real
        )
        real_adapters_available = True
    except ImportError:
        real_adapters_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_setup")

def dc_initialize(use_real_adapters=False):
    """
    Initialize the DC implementation by registering all tools.
    Uses namespace isolation to avoid conflicts.
    
    Args:
        use_real_adapters: Whether to use real adapters or mock implementations
    """
    logger.info(f"Initializing DC implementation (use_real_adapters={use_real_adapters})")
    
    # Check if real adapters were requested but aren't available
    if use_real_adapters and not real_adapters_available:
        logger.warning("Real adapters requested but not available, falling back to mock implementations")
        use_real_adapters = False
    
    # Select the appropriate computer tool adapter
    computer_executor = dc_execute_computer_tool_real if use_real_adapters else dc_execute_computer_tool
    
    # Register the computer tool
    dc_register_tool(
        name="dc_computer",
        definition=DC_COMPUTER_TOOL,
        executor=computer_executor,
        validator=dc_validate_computer_parameters
    )
    logger.info(f"Registered DC computer tool with {'real' if use_real_adapters else 'mock'} implementation")
    
    # Select the appropriate bash tool adapter
    bash_executor = dc_execute_bash_tool_real if use_real_adapters else dc_execute_bash_tool
    
    # Register the bash tool
    dc_register_tool(
        name="dc_bash",
        definition=DC_BASH_TOOL,
        executor=bash_executor,
        validator=dc_validate_bash_parameters
    )
    logger.info(f"Registered DC bash tool with {'real' if use_real_adapters else 'mock'} implementation")
    
    # Register the edit tool
    if edit_tool_available:
        # Use custom streaming edit tool implementation
        edit_executor = dc_execute_edit_tool_real if (use_real_adapters and real_adapters_available) else dc_execute_edit_tool
        
        # Register the edit tool
        dc_register_tool(
            name="dc_str_replace_editor",
            definition=DC_EDIT_TOOL,
            executor=edit_executor,
            validator=dc_validate_edit_parameters
        )
        logger.info(f"Registered DC edit tool with {'real' if use_real_adapters else 'streaming'} implementation")
    else:
        # Fallback if edit tool is not available
        logger.warning("Edit tool not available, file operations will not be supported")
    
    logger.info("DC implementation initialized successfully")