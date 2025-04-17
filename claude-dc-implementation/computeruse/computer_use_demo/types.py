from enum import StrEnum
from dataclasses import dataclass, fields, replace

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution."""
    output: str | None = None
    error: str | None = None
    base64_image: str | None = None
    system: str | None = None

    def __bool__(self):
        # ToolResult is truthy if it has any content
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult"):
        def combine_fields(field: str | None, other_field: str | None, concatenate: bool = True):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, concatenate=False),
            system=combine_fields(self.system, other.system),
        )

    def replace(self, **kwargs) -> "ToolResult":
        """Return a new ToolResult with the given fields replaced."""
        return replace(self, **kwargs)

