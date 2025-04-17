import asyncio
import os
import shlex
from typing import Any, Literal
import logging

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .token_manager import (
    with_token_limiting, 
    FileTokenEstimator,
    token_rate_limiter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bash_tool")

# Constants for file size limits 
MAX_OUTPUT_SIZE = 1_000_000  # 1MB, we'll chunk anything larger

class _BashSession:
    """A session of a bash shell."""

    _started: bool
    _process: asyncio.subprocess.Process

    command: str = "/bin/bash"
    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    def __init__(self):
        self._started = False
        self._timed_out = False

    async def start(self):
        if self._started:
            return

        self._process = await asyncio.create_subprocess_shell(
            self.command,
            preexec_fn=os.setsid,
            shell=True,
            bufsize=0,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._started = True

    def stop(self):
        """Terminate the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return
        self._process.terminate()

    async def run(self, command: str):
        """Execute a command in the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return ToolResult(
                system="tool must be restarted",
                error=f"bash has exited with returncode {self._process.returncode}",
            )
        if self._timed_out:
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            )

        # we know these are not None because we created the process with PIPEs
        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr

        # Token tracking for command
        estimated_command_tokens = len(command) // 4  # Rough estimation
        await token_rate_limiter.wait_for_capacity(estimated_command_tokens)
        token_rate_limiter.record_usage(estimated_command_tokens, 0)

        # send command to the process
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            async with asyncio.timeout(self._timeout):
                while True:
                    await asyncio.sleep(self._output_delay)
                    # if we read directly from stdout/stderr, it will wait forever for
                    # EOF. use the StreamReader buffer directly instead.
                    output = self._process.stdout._buffer.decode()  # pyright: ignore[reportAttributeAccessIssue]
                    if self._sentinel in output:
                        # strip the sentinel and break
                        output = output[: output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            self._timed_out = True
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        error = self._process.stderr._buffer.decode()  # pyright: ignore[reportAttributeAccessIssue]
        if error.endswith("\n"):
            error = error[:-1]

        # clear the buffers so that the next output can be read correctly
        self._process.stdout._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]
        self._process.stderr._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]

        # Check if output is too large and needs chunking
        if len(output) > MAX_OUTPUT_SIZE:
            logger.warning(f"Large output detected: {len(output)} bytes. Chunking output.")
            return self._handle_large_output(output, error)
            
        # Token tracking for response
        estimated_output_tokens = (len(output) + len(error)) // 4
        token_rate_limiter.record_usage(0, estimated_output_tokens)

        return CLIResult(output=output, error=error)
    
    def _handle_large_output(self, output: str, error: str) -> CLIResult:
        """Handle large output by summarizing and chunking"""
        # Summarize the output
        summary = f"Command generated a large output: {len(output)} bytes.\n"
        summary += "Output has been truncated to prevent token limit issues.\n"
        summary += "Consider redirecting large output to a file and using grep or other tools to examine it."
        
        # First few lines and last few lines
        head_lines = "\n".join(output.split("\n")[:10])
        tail_lines = "\n".join(output.split("\n")[-10:])
        
        truncated_output = f"{summary}\n\n--- First 10 lines ---\n{head_lines}\n\n... (output truncated) ...\n\n--- Last 10 lines ---\n{tail_lines}"
        
        # Token tracking for response
        estimated_output_tokens = (len(truncated_output) + len(error)) // 4
        token_rate_limiter.record_usage(0, estimated_output_tokens)
        
        return CLIResult(output=truncated_output, error=error)


def estimate_bash_input_tokens(command: str = None, restart: bool = False, **kwargs) -> int:
    """Estimate token usage for bash commands"""
    if restart:
        return 10  # Token estimation for restart operation
    if command:
        return len(command) // 4 + 20  # Rough estimation
    return 20  # Default token cost


def estimate_bash_output_tokens(result: ToolResult) -> int:
    """Estimate token usage for bash command output"""
    total_length = 0
    if result.output:
        total_length += len(result.output)
    if result.error:
        total_length += len(result.error)
    if result.system:
        total_length += len(result.system)
    # Base64 image is not counted in token usage
    
    return total_length // 4  # Rough estimation


class BashTool20250124(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands.
    The tool parameters are defined by Anthropic and are not editable.
    Enhanced with token management.
    """

    _session: _BashSession | None

    api_type: Literal["bash_20250124"] = "bash_20250124"
    name: Literal["bash"] = "bash"

    def __init__(self):
        self._session = None
        super().__init__()

    def to_params(self) -> Any:
        return {
            "type": self.api_type,
            "name": self.name,
        }

    @with_token_limiting(
        input_token_estimator=estimate_bash_input_tokens,
        output_token_estimator=estimate_bash_output_tokens
    )
    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            self._session = _BashSession()
            await self._session.start()

        if command is not None:
            # Check for commands that might generate very large outputs
            if self._is_potentially_token_heavy(command):
                logger.warning(f"Potentially token-heavy command detected: {command}")
                warning = (
                    "This command might generate a large amount of output, potentially exceeding token limits. "
                    "Consider redirecting output to a file and then examining it selectively with grep or head/tail."
                )
                if not self._has_redirection(command):
                    suggested_cmd = self._suggest_redirection(command)
                    warning += f"\nSuggested command: {suggested_cmd}"
                    return ToolResult(
                        system=warning,
                        error="Command not executed due to potential token limit issues. See system message for suggestions."
                    )
            
            return await self._session.run(command)

        raise ToolError("no command provided.")
    
    def _is_potentially_token_heavy(self, command: str) -> bool:
        """Check if a command might generate a lot of tokens"""
        token_heavy_commands = [
            "cat", "find", "grep -r", "ls -la", "ps aux", "df -h",
            "du -sh", "history", "netstat", "journalctl"
        ]
        return any(cmd in command for cmd in token_heavy_commands) and not self._has_redirection(command)
    
    def _has_redirection(self, command: str) -> bool:
        """Check if command already redirects output"""
        redirections = [" > ", " >> ", " | ", " 2> ", " 2>> ", " &> "]
        return any(redirect in command for redirect in redirections)
    
    def _suggest_redirection(self, command: str) -> str:
        """Suggest a redirected command"""
        # Parse the command to get the main executable
        parts = shlex.split(command)
        if not parts:
            return command
            
        main_cmd = parts[0]
        
        # For listing commands, suggest piping to grep
        if main_cmd == "ls":
            return f"{command} > /tmp/ls_output.txt && head -20 /tmp/ls_output.txt"
        # For cat, suggest using head/tail or grep
        elif main_cmd == "cat":
            return f"head -20 {' '.join(parts[1:])}"
        # For large outputs from other commands
        else:
            return f"{command} > /tmp/command_output.txt && head -20 /tmp/command_output.txt"


class BashTool20241022(BashTool20250124):
    api_type: Literal["bash_20241022"] = "bash_20241022"  # pyright: ignore[reportIncompatibleVariableOverride]
