"""
API Provider definitions for Claude Computer Use implementation.
"""
from enum import StrEnum


class APIProvider(StrEnum):
    """Enum for different API providers"""
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"