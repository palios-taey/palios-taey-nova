"""
Tool implementations for Claude Computer Use.
"""
from enum import Enum, StrEnum
from typing import Optional

# Import from base module
from .base import ToolResult

# Tool version enum
class ToolVersion(str, Enum):
    COMPUTER_USE_20241022 = "computer_use_20241022"
    COMPUTER_USE_20250124 = "computer_use_20250124"

from .bash import execute_bash_tool
from .computer import execute_computer_tool
from .edit import execute_edit_tool

__all__ = ["execute_bash_tool", "execute_computer_tool", "execute_edit_tool", "ToolResult", "ToolVersion"]