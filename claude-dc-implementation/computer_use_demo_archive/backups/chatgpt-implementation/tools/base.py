"""Base classes for tools in Claude DC."""
from abc import ABCMeta, abstractmethod
from typing import Any

try:
    from anthropic.types.beta import BetaToolUnionParam
except ImportError:
    BetaToolUnionParam = dict  # fallback if Anthropics SDK types are not available

class BaseAnthropicTool(metaclass=ABCMeta):
    """Abstract base class for Anthropic-defined tools."""
    @abstractmethod
    async def __call__(self, **kwargs) -> Any:
        """Executes the tool with the given arguments."""
        raise NotImplementedError

    @abstractmethod
    def to_params(self) -> Any:
        """Returns the tool's definition parameters for registration."""
        raise NotImplementedError

