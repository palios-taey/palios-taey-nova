from abc import ABCMeta, abstractmethod
from anthropic.types.beta import BetaToolUnionParam

class BaseAnthropicTool(metaclass=ABCMeta):
    """Abstract base class for Anthropic-defined tools."""
    # Each tool must define class attributes:
    #   name (the tool's name as recognized by Claude)
    #   api_type (the tool type string with version, e.g. "bash_20250124")
    # Tools may also maintain internal state as needed.

    @abstractmethod
    def to_params(self) -> BetaToolUnionParam:
        """Returns the tool's parameters for API registration."""
        raise NotImplementedError

    @abstractmethod
    async def __call__(self, **kwargs) -> Any:
        """Execute the tool with given arguments. Must return a ToolResult (or list of ToolResults)."""
        raise NotImplementedError

