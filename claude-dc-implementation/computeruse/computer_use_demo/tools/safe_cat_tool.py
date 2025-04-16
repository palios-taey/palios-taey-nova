"""
SafeCatTool - A tool for safely viewing file contents with token awareness.
"""

from pathlib import Path
from typing import Any, Literal

from computer_use_demo.tools.base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from computer_use_demo.token_manager import token_manager
from computer_use_demo.adaptive_client import create_adaptive_client
from computer_use_demo.safe_file_operations import safe_cat, safe_read_file

class SafeCatTool20250124(BaseAnthropicTool):
    """
    A tool for safely viewing file contents with token awareness.
    Automatically chunks large files and retrieves subsequent chunks.
    """
    
    api_type: Literal["safe_cat_20250124"] = "safe_cat_20250124"
    name: Literal["safe_cat"] = "safe_cat"
    
    def __init__(self):
        super().__init__()
    
    def to_params(self) -> Any:
        return {
            "name": self.name,
            "type": self.api_type,
            "description": "Safely view file contents with automatic chunking for large files. If a file has been chunked, this will retrieve the next chunk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    },
                    "metadata": {
                        "type": "boolean",
                        "description": "If true, returns metadata about the file instead of content"
                    }
                },
                "required": ["path"]
            }
        }
    
    async def __call__(self, *, path: str, metadata: bool = False, **kwargs):
        try:
            _path = Path(path)
            
            # Validate the path
            if not _path.is_absolute():
                suggested_path = Path("") / _path
                raise ToolError(
                    f"The path {_path} is not an absolute path, it should start with `/`. "
                    f"Maybe you meant {suggested_path}?"
                )
            
            if not _path.exists():
                raise ToolError(f"The path {_path} does not exist. Please provide a valid path.")
            
            if _path.is_dir():
                raise ToolError(f"The path {_path} is a directory. Please provide a path to a file.")
            
            if metadata:
                # Return metadata about the file
                meta = interceptor.get_file_metadata(path)
                return CLIResult(output=f"File metadata for {path}:\n\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()))
            
            # Get the file content (chunked if necessary)
            content = safe_cat(path)
            return CLIResult(output=content)
        
        except Exception as e:
            return ToolResult(error=f"Error reading file: {e}")
