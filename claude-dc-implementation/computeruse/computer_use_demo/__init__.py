"""
Computer Use Demo package for Claude.

This package provides the necessary tools and infrastructure for Claude 
to interact with a computer environment, including bash commands,
file editing, and desktop interaction capabilities.
"""

# Package version
__version__ = "0.1.0"

# Ensure proper imports from the package
from .tools import (
    ToolResult,
    ToolFailure,
    CLIResult,
    ToolCollection,
    ToolVersion,
    TOOL_GROUPS_BY_VERSION,
    BashTool20241022,
    BashTool20250124,
    ComputerTool20241022,
    ComputerTool20250124,
    EditTool20241022,
    EditTool20250124,
)
