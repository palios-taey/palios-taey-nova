"""
Tool Registry for Claude DC.

This package provides a centralized registry for all tools,
including their definitions, executors, and validators.
"""

import logging
import sys
from pathlib import Path

# Set up paths
DEV_DIR = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom")
ADAPTERS_DIR = DEV_DIR / "adapters"

# Add the adapters directory to the path
sys.path.append(str(ADAPTERS_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tool_registry")

# Import registry components
from .models import ToolResult, ToolInfo, ToolRegistry
from .registry import (
    register_tool,
    get_tool,
    get_all_tools,
    get_tool_definitions,
    is_tool_registered,
    COMPUTER_USE_TOOL,
    BASH_TOOL,
    TEXT_EDITOR_TOOL
)
from .validators import (
    validate_computer_parameters,
    validate_bash_parameters,
    validate_edit_parameters
)
from .executor import execute_tool, execute_with_fallback

# Import tool adapters
try:
    from tool_adapters import (
        execute_computer_tool_mock as execute_computer_tool,
        execute_bash_tool_mock as execute_bash_tool,
        execute_edit_tool_mock as execute_edit_tool
    )
    logger.info("Loaded mock tool implementations")
except ImportError as e:
    logger.warning(f"Failed to import tool adapters: {e}")
    # Define fallback adapters that return errors
    async def execute_computer_tool(tool_input):
        return ToolResult(error="Computer tool adapter not available")
    
    async def execute_bash_tool(tool_input):
        return ToolResult(error="Bash tool adapter not available")
    
    async def execute_edit_tool(tool_input):
        return ToolResult(error="Edit tool adapter not available")

# Initialize the registry
def init_registry():
    """Initialize the tool registry with all available tools."""
    logger.info("Initializing tool registry")
    
    # Register computer tool
    register_tool(
        name="computer",
        definition=COMPUTER_USE_TOOL,
        executor=execute_computer_tool,
        validator=validate_computer_parameters,
        description="Control a computer with mouse and keyboard actions"
    )
    
    # Register bash tool
    register_tool(
        name="bash",
        definition=BASH_TOOL,
        executor=execute_bash_tool,
        validator=validate_bash_parameters,
        description="Execute bash commands in the shell"
    )
    
    # Register edit tool
    register_tool(
        name="str_replace_editor",
        definition=TEXT_EDITOR_TOOL,
        executor=execute_edit_tool,
        validator=validate_edit_parameters,
        description="View, create, and edit files"
    )
    
    logger.info(f"Tool registry initialized with {len(get_all_tools())} tools")

# Initialize registry on import
init_registry()