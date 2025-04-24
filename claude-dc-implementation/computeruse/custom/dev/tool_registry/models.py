"""
Models for the Claude DC Tools Registry.

This module defines the core data structures used in the tool registry system,
providing type definitions for tool results, tool information, and the registry itself.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable, Awaitable, Union

@dataclass
class ToolResult:
    """
    Represents the result of a tool execution.
    
    Attributes:
        output: Text output from the tool, if any
        error: Error message from the tool, if any
        base64_image: Base64-encoded image data, if any
    """
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    
    def __bool__(self):
        """Returns True if any result field is populated."""
        return any([self.output, self.error, self.base64_image])
        
    def has_error(self) -> bool:
        """Returns True if the result contains an error."""
        return self.error is not None and len(self.error) > 0
        
    def has_output(self) -> bool:
        """Returns True if the result contains output."""
        return self.output is not None and len(self.output) > 0
        
    def has_image(self) -> bool:
        """Returns True if the result contains an image."""
        return self.base64_image is not None and len(self.base64_image) > 0


# Type definition for tool validator function
ToolValidator = Callable[[Dict[str, Any]], tuple[bool, str]]

# Type definition for tool executor function
ToolExecutor = Callable[[Dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class ToolInfo:
    """
    Information about a tool in the registry.
    
    Attributes:
        definition: The tool definition for the Anthropic API
        executor: Function that executes the tool
        validator: Function that validates tool parameters
        name: The name of the tool
        description: A human-readable description of the tool
    """
    definition: Dict[str, Any]
    executor: ToolExecutor
    validator: ToolValidator
    name: str
    description: str = ""
    
    def __post_init__(self):
        """Set name and description from definition if not provided."""
        if not self.name and "name" in self.definition:
            self.name = self.definition["name"]
        if not self.description and "description" in self.definition:
            self.description = self.definition["description"]

# Type alias for the tool registry
ToolRegistry = Dict[str, ToolInfo]