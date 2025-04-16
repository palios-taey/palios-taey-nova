from pathlib import Path
from typing import Any, Literal

from computer_use_demo.tools.base import BaseAnthropicTool, CLIResult, ToolError, ToolResult

class CatMoreTool20250124(BaseAnthropicTool):
    """
    A tool for viewing the next chunk of output from a previously chunked command.
    """
    
    api_type: Literal["cat_more_20250124"] = "cat_more_20250124"
    name: Literal["cat_more"] = "cat_more"
    
    def __init__(self):
        super().__init__()
    
    def to_params(self) -> Any:
        return {
            "name": self.name,
            "type": self.api_type,
            "description": "Show the next chunk of output from a previously chunked command or file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {
                        "type": "string",
                        "description": "Reference ID for the chunked output (usually a hash provided when output was truncated)"
                    }
                },
                "required": ["reference"]
            }
        }
    
    async def __call__(self, *, reference: str, **kwargs):
        try:
            # Try to access the cat_more function from builtins
            import builtins
            if hasattr(builtins, 'cat_more'):
                result = builtins.cat_more(reference)
                return CLIResult(output=result)
            else:
                # Fall back to checking the interceptor directly
                from computer_use_demo.safe_file_operations import interceptor
                
                # Check if this is a file path
                if Path(reference).exists():
                    result = interceptor.get_next_chunk(reference)
                    return CLIResult(output=result)
                
                # Otherwise, assume it's a command hash
                import subprocess
                if hasattr(subprocess, 'run') and hasattr(subprocess.run, '__wrapped__'):
                    wrapper = subprocess.run.__globals__.get('subprocess_wrapper')
                    if wrapper and hasattr(wrapper, 'get_next_chunk'):
                        result = wrapper.get_next_chunk(reference)
                        return CLIResult(output=result)
                
                return ToolResult(error=f"No chunked content found for reference: {reference}")
        
        except Exception as e:
            return ToolResult(error=f"Error retrieving next chunk: {e}")
