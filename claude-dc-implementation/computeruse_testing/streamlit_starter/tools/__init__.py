"""
Tool implementations for Claude Computer Use.
"""

from .bash import execute_bash_tool
from .computer import execute_computer_tool
from .ToolVersion import ToolVersion
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Container for tool execution results"""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    
    def __str__(self):
        if self.error:
            return f"Error: {self.error}"
        return self.output or ""


__all__ = ["execute_bash_tool", "execute_computer_tool", "ToolResult", "ToolVersion"]