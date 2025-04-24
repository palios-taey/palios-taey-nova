"""
Models for the Claude DC Tools implementation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable, Awaitable

@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    
    def __bool__(self):
        """Returns True if any result field is populated."""
        return any([self.output, self.error, self.base64_image])

@dataclass
class ToolInfo:
    """Information about a tool in the registry."""
    definition: Dict[str, Any]
    executor: Callable[[Dict[str, Any]], Awaitable[ToolResult]]
    validator: Callable[[Dict[str, Any]], tuple[bool, str]]

# Type alias for the tool registry
ToolRegistry = Dict[str, ToolInfo]