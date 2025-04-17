# Expose tool classes and results at package level for convenience
from .types import ToolResult, CLIResult, ToolFailure, ToolError
from .bash import BashTool20250124 as BashTool
from .computer import ComputerTool20250124 as ComputerTool
from .groups import ToolCollection, TOOLS_20250124, TOOLS_20241022, DEFAULT_TOOLS

# This allows external code to import e.g. ComputerTool or BashTool without specifying version.
# It also makes ToolResult and related classes directly accessible via computer_use_demo.tools.

