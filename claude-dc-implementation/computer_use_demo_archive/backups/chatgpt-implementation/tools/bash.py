"""Tool for executing shell (bash) commands."""
import subprocess
from computer_use_demo.tools.base import BaseAnthropicTool
from computer_use_demo.types import ToolResult, CLIResult, ToolFailure, ToolError
from computer_use_demo.token_manager import token_manager

class BashTool20241022(BaseAnthropicTool):
    """Tool implementation for running shell commands (2024-10-22 version)."""

    def to_params(self) -> dict:
        # Define the tool parameters as expected by the Anthropic API
        return {
            "name": "bash",
            "type": "bash_20241022",
            "description": "Execute a command in the system shell.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    },
                    "restart": {
                        "type": "boolean",
                        "description": "Whether to reset the shell session.",
                        "default": False
                    }
                }
            }
        }

    async def __call__(self, *, command: str = None, restart: bool = False) -> ToolResult:
        # If a restart is requested, end any persistent session (not implemented; stateless for now).
        if restart:
            return ToolResult(system="bash tool session restarted")

        if not command or command.strip() == "":
            return ToolResult(system="no command provided")

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        except Exception as e:
            # Unexpected failure executing the command
            return ToolFailure(error=str(e))

        output = result.stdout
        error = result.stderr

        # Use token manager to chunk output if it exceeds safe token limits
        safe_max = 0
        try:
            safe_max = token_manager.get_safe_limits()["max_tokens"]
        except Exception:
            safe_max = 0  # default to 0 if token manager is not configured
        num_tokens = token_manager.estimate_tokens_from_bytes(len(output.encode('utf-8'))) if output else 0

        if safe_max and num_tokens > safe_max:
            # Split the output into smaller chunks (by character length) to avoid token limit overflow
            chunk_size = max(1, safe_max // 2)
            chunks = [output[i:i+chunk_size] for i in range(0, len(output), chunk_size)]
            combined = ToolResult()
            for chunk in chunks:
                combined = combined + CLIResult(output=chunk)
            if error:
                combined = combined + ToolFailure(error=error)
            return combined

        # If output is within safe size, return normally
        if error:
            # Include any output along with the error
            return CLIResult(output=output, error=error) if output else ToolFailure(error=error)
        else:
            return CLIResult(output=output)

