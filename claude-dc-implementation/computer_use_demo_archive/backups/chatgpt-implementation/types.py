from enum import StrEnum
from dataclasses import dataclass, replace, fields
from typing import Any

# Define who is sending a message (user, assistant, or tool)
class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

# APIProvider could be an enum or class indicating which LLM API to use (Anthropic, OpenAI, etc.)
class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    # ... add other providers if needed

# ToolResult and its subclasses define the structure of tool outputs
@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution."""
    output: str | None = None       # normal text output (markdown or code)
    error: str | None = None        # error message (if any error occurred)
    base64_image: str | None = None # image data in base64 (if the tool returns an image)
    system: str | None = None       # system message (for internal notices like restarts)

    def __bool__(self):
        # ToolResult is truthy if it has any content
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult") -> "ToolResult":
        """Combine two ToolResults, concatenating outputs if needed."""
        def combine_fields(field, other_field, concatenate: bool = True):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results: both have field data.")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output, concatenate=True),
            error=combine_fields(self.error, other.error, concatenate=False),
            base64_image=combine_fields(self.base64_image, other.base64_image, concatenate=False),
            system=combine_fields(self.system, other.system, concatenate=True),
        )

    def replace(self, **kwargs) -> "ToolResult":
        """Return a new ToolResult with specified fields replaced."""
        return replace(self, **kwargs)

# Subclasses for special rendering cases
class CLIResult(ToolResult):
    """A ToolResult intended to be rendered as CLI output (monospaced code block)."""
    # Inherits everything from ToolResult; used to signal the UI for code formatting

class ToolFailure(ToolResult):
    """A ToolResult representing a tool execution failure."""
    # No additional fields; just a semantic distinction for failures

class ToolError(Exception):
    """Exception raised when a tool encounters an error."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

