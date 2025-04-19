"""Collection classes for managing multiple tools."""

import logging
from typing import Any, Callable, Optional

from anthropic.types.beta import BetaToolUnionParam

from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)

logger = logging.getLogger('claude_dc.tools')

class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}
        self._stream_callback = None

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self.tools]
        
    def set_stream_callback(self, callback: Optional[Callable[[str, str], None]] = None):
        """
        Set a callback function to receive streaming outputs from tools.
        
        Args:
            callback: A function that takes (output_chunk, tool_id) and handles the chunk
                     Set to None to disable streaming
        """
        self._stream_callback = callback
        
        # Apply to all tools that support streaming
        for tool in self.tools:
            if hasattr(tool, 'set_stream_callback'):
                tool.set_stream_callback(callback)
                logger.info(f"Set streaming callback for tool: {tool.name}")

    async def run(self, *, name: str, tool_input: dict[str, Any], streaming: bool = True) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
            
        # Add tool_id to input if streaming is supported
        if hasattr(tool, 'set_stream_callback') and 'tool_id' not in tool_input:
            tool_input['tool_id'] = name
            logger.info(f"Running tool with streaming: {name}")
            
        try:
            # Make sure streaming callback is set
            if streaming and self._stream_callback and hasattr(tool, 'set_stream_callback'):
                tool.set_stream_callback(self._stream_callback)
                
            # Run the tool
            return await tool(**tool_input)
        except ToolError as e:
            logger.error(f"Tool error: {e.message}")
            return ToolFailure(error=e.message)
        except Exception as e:
            logger.error(f"Unexpected error in tool {name}: {str(e)}")
            return ToolFailure(error=f"Unexpected error: {str(e)}")
