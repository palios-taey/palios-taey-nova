"""Tool package initializer: defines tool collections and tool sets by version."""
from enum import StrEnum
from computer_use_demo.tools.base import BaseAnthropicTool
from computer_use_demo.tools.bash import BashTool20241022
from computer_use_demo.tools.computer import ComputerTool20241022
from computer_use_demo.types import ToolResult, ToolFailure, ToolError

# Define tool classes for future version (2025-01-24) by subclassing current implementations
class BashTool20250124(BashTool20241022):
    """Tool implementation for bash (2025-01-24 version)."""
    def to_params(self) -> dict:
        params = super().to_params()
        params["type"] = "bash_20250124"
        return params

class ComputerTool20250124(ComputerTool20241022):
    """Tool implementation for computer control (2025-01-24 version)."""
    api_type = "computer_20250124"
    def to_params(self) -> dict:
        params = super().to_params()
        params["type"] = "computer_20250124"
        return params

class ToolVersion(StrEnum):
    V20241022 = "2024-10-22"
    V20250124 = "2025-01-24"

class ToolCollection:
    """A collection of tools, with methods to get definitions and execute by name."""
    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = list(tools)
        self.tool_map = {tool.to_params().get("name"): tool for tool in self.tools}

    def to_params(self):
        # Return list of tool definitions (for model registration)
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool '{name}' is not available")
        try:
            result = await tool(**tool_input)
            # Ensure we return a ToolResult instance
            return result if isinstance(result, ToolResult) else ToolResult()
        except ToolError as e:
            return ToolFailure(error=e.message)

# Instantiate tool sets for each supported version
TOOLS_20241022 = ToolCollection(BashTool20241022(), ComputerTool20241022())
TOOLS_20250124 = ToolCollection(BashTool20250124(), ComputerTool20250124())

# Default tool set (use latest version by default)
DEFAULT_TOOLS = TOOLS_20250124

# Map each version to its ToolCollection
TOOL_GROUPS_BY_VERSION = {
    ToolVersion.V20241022: TOOLS_20241022,
    ToolVersion.V20250124: TOOLS_20250124
}

