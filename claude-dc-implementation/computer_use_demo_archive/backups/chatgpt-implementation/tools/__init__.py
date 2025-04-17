# Expose tool classes and results at package level for convenience
from computer_use_demo.types import ToolResult, CLIResult, ToolFailure, ToolError
from computer_use_demo.tools.bash import BashTool20250124 as BashTool
from computer_use_demo.tools.computer import ComputerTool20250124 as ComputerTool
from computer_use_demo.tools.groups import (
    ToolCollection,
    TOOLS_20250124,
    TOOLS_20241022,
    DEFAULT_TOOLS
)

# Provide tool version alias and grouping for easy reference in external code
from typing import Literal
ToolVersion = Literal["20241022", "20250124"]
TOOL_GROUPS_BY_VERSION = {
    "20241022": TOOLS_20241022,
    "20250124": TOOLS_20250124,
}

# This allows external code to import e.g. ComputerTool or BashTool without specifying version.
# It also makes ToolResult (and related classes) and tool version mappings directly accessible via computer_use_demo.tools.

