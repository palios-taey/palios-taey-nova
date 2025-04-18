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
            # Special handling for bash tool
            if name == "bash":
                # If empty input or missing command parameter, return a meaningful error
                if not tool_input or "command" not in tool_input:
                    return ToolFailure(error="Bash tool requires a 'command' parameter. Example: {\"command\": \"ls -la\"}")
                
                # Extract command parameter and call the tool
                command = tool_input.get("command")
                restart = tool_input.get("restart", False)
                
                # If restart flag is True, call with restart=True
                if restart:
                    return await tool(restart=True)
                # Otherwise call with the command
                elif command:
                    return await tool(command=command)
                else:
                    return ToolFailure(error=f"Invalid input for bash tool: {tool_input}")
        
        # For other tools, pass the input dict as-is
        return await tool(**tool_input)
    except ToolError as e:
        return ToolFailure(error=e.message)
    except Exception as e:
        # Better error handling for any other exceptions
        return ToolFailure(error=f"Error running tool {name}: {str(e)}")
            
            # For other tools, pass the input dict as-is
            return await tool(**tool_input)
        except ToolError as e:
            return ToolFailure(error=e.message)
        except Exception as e:
            # Better error handling for any other exceptions
            return ToolFailure(error=f"Error running tool {name}: {str(e)}")
