from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any

from anthropic.types.beta import BetaToolUnionParam
from computer_use_demo.types import ToolResult

class BaseAnthropicTool(metaclass=ABCMeta):
    """Abstract base class for Anthropic-defined tools."""
    @abstractmethod
    def __call__(self, **kwargs) -> Any:
        """Executes the tool with the given arguments."""
        ...

    @abstractmethod
    def to_params(self) -> BetaToolUnionParam:
        raise NotImplementedError

# The ToolResult class is imported from computer_use_demo.types

class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""
    # Inherits all behavior from ToolResult (frozen dataclass).

class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""
    # Inherits all behavior from ToolResult.

class ToolError(Exception):
    """Raised when a tool encounters an error."""
    def __init__(self, message: str):
        self.message = message

