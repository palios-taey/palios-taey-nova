"""Collection classes for managing multiple tools."""

from typing import Any

from anthropic.types.beta import BetaToolUnionParam

from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)


class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        """Run a tool with the given name and input."""
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            # Handle bash tool specially - extract 'command' from the input dict
            if name == "bash" and isinstance(tool_input, dict):
                # Extract command from input dict if it exists
                command = tool_input.get("command")
                if command is not None:
                    return await tool(command=command)
                # Handle restart flag
                restart = tool_input.get("restart")
                if restart is not None and restart:
                    return await tool(restart=True)
                return ToolFailure(error="Bash tool requires a 'command' parameter. Example: {\"command\": \"ls -la\"}")
            # For other tools, pass the input dict as-is
            return await tool(**tool_input)
        except ToolError as e:
            return ToolFailure(error=e.message)
