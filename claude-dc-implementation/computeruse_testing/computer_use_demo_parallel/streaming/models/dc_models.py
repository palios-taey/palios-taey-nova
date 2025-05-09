"""
Custom models for Claude DC implementation with namespace isolation.
These model classes use unique names to avoid conflicts with production code.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable, Awaitable

@dataclass
class DCToolResult:
    """Represents the result of a tool execution with namespace isolation."""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    
    def __bool__(self):
        """Returns True if any result field is populated."""
        return any([self.output, self.error, self.base64_image])

@dataclass
class DCToolInfo:
    """Information about a tool in the registry with namespace isolation."""
    definition: Dict[str, Any]
    executor: Callable[[Dict[str, Any]], Awaitable[DCToolResult]]
    validator: Callable[[Dict[str, Any]], tuple[bool, str]]

# Type alias for the tool registry with namespace isolation
DCToolRegistry = Dict[str, DCToolInfo]