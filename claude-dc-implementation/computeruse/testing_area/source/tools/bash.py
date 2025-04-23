import asyncio
import os
import logging
from typing import Any, Callable, Literal, Optional

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .streaming_tool import StreamingToolMixin, stream_command_output

logger = logging.getLogger('claude_dc.bash')


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

        return CLIResult(output=output, error=error)


class BashTool20250124(BaseAnthropicTool, StreamingToolMixin):
    """
    A tool that allows the agent to run bash commands.
    The tool parameters are defined by Anthropic and are not editable.
    Enhanced with real-time streaming of command output.
    """

    _session: _BashSession | None
    _tool_id: str = ""  # Current tool_id for streaming
    _stream_callback: Optional[Callable[[str, str], None]] = None

    api_type: Literal["bash_20250124"] = "bash_20250124"
    name: Literal["bash"] = "bash"

    def __init__(self):
        self._session = None
        super().__init__()

    def to_params(self) -> Any:
        """Return parameters for the bash tool in the format expected by the API."""
        return {
            "name": self.name,
            "type": "custom",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Bash command to execute"
                    },
                    "restart": {
                        "type": "boolean",
                        "description": "Whether to restart the bash session"
                    },
                    "stream": {
                        "type": "boolean",
                        "description": "Whether to stream output in real-time (default: true)"
                    }
                },
                "required": ["command"]
            },
            "description": "Execute bash commands in the system shell"
        }

    async def __call__(
        self, command: str | None = None, restart: bool = False, stream: bool = True, tool_id: str = "", **kwargs
    ):
        # Store tool_id for streaming
        self._tool_id = tool_id
        
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()
            logger.info("Bash session restarted")
            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            self._session = _BashSession()
            await self._session.start()
            logger.info("New bash session started")

        if command is not None:
            logger.info(f"Running bash command: {command}")
            
            # Use streaming if enabled and callback is set
            if stream and hasattr(self, '_stream_callback') and self._stream_callback:
                logger.info("Using streaming mode for bash command")
                return await stream_command_output(
                    command=command, 
                    callback=self._stream_output,
                    tool_id=self._tool_id
                )
            else:
                # Use traditional approach
                return await self._session.run(command)

        raise ToolError("no command provided.")


class BashTool20241022(BashTool20250124):
    api_type: Literal["bash_20241022"] = "bash_20241022"  # pyright: ignore[reportIncompatibleVariableOverride]
