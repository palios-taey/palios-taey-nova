from typing import Any, Literal
import asyncio
from computer_use_demo.tools.base import BaseAnthropicTool
from computer_use_demo.types import ToolResult, CLIResult, ToolError
from computer_use_demo.token_manager import token_manager  # token manager provides token counting & chunking

# Internal helper class to manage an interactive Bash session
class _BashSession:
    def __init__(self):
        self._process = None

    async def start(self):
        """Start a persistent bash subprocess for the session."""
        # Launch an interactive bash shell
        self._process = await asyncio.create_subprocess_exec(
            "/bin/bash", "-i",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # Small delay to allow shell to initialize
        await asyncio.sleep(0.1)
        # Clear any initial output
        if self._process.stdout:
            try:
                await asyncio.wait_for(self._process.stdout.read(100), timeout=0.1)
            except asyncio.TimeoutError:
                pass

    async def run(self, command: str, timeout: float = 5.0) -> ToolResult:
        """Run a single bash command in the session and return its output as a ToolResult."""
        if not self._process:
            raise ToolError("Bash session is not started.")
        # Write the command to the shell
        cmd = command.strip() + "\n"
        assert self._process.stdin is not None
        self._process.stdin.write(cmd.encode())
        await self._process.stdin.drain()

        # Collect output until newline (for simplicity, we read line by line with a timeout)
        output_lines: list[str] = []
        error_lines: list[str] = []
        try:
            # Wait for command completion or timeout
            # We will continuously read until there's no new output for a short period
            while True:
                # Use asyncio.wait_for to enforce the timeout for each read
                stdout_task = asyncio.create_task(self._process.stdout.readline())
                stderr_task = asyncio.create_task(self._process.stderr.readline())
                done, _ = await asyncio.wait({stdout_task, stderr_task}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
                if not done:
                    # Command timed out (no output within timeout interval)
                    stdout_task.cancel()
                    stderr_task.cancel()
                    raise ToolError(f"Command timed out after {timeout} seconds.")
                # Check which task completed
                if stdout_task in done:
                    line = (await stdout_task).decode(errors="ignore")
                    if line == "":  # EOF or no more output
                        break
                    output_lines.append(line)
                if stderr_task in done:
                    err_line = (await stderr_task).decode(errors="ignore")
                    if err_line:
                        error_lines.append(err_line)
                # Continue loop to gather more output until shell indicates command finished
                # (In an interactive shell, end of output might be signaled by a new prompt, but for simplicity 
                # we'll break when both stdout and stderr yields are empty.)
                if stdout_task in done and stderr_task in done:
                    if not line and not err_line:
                        break
        except Exception as e:
            # If any exception (like ToolError for timeout), stop reading further
            pass

        # Combine lines
        output_text = "".join(output_lines).strip()
        error_text = "".join(error_lines).strip()

        # If output is extremely large, it will be chunked by the caller (BashTool)
        # Here we just return a ToolResult for the whole output; chunking logic is handled above.
        return CLIResult(output=output_text if output_text else None,
                         error=error_text if error_text else None)

    def stop(self):
        """Terminate the bash subprocess."""
        if self._process:
            self._process.kill()
            self._process = None

class BashTool20250124(BaseAnthropicTool):
    """A tool that allows the agent to run bash commands and get output."""
    _session: _BashSession | None = None

    api_type: Literal["bash_20250124"] = "bash_20250124"
    name:    Literal["bash"] = "bash"

    def __init__(self):
        self._session = None
        super().__init__()

    def to_params(self) -> Any:
        # Define this tool for the Anthropic API (type and name)
        return {"type": self.api_type, "name": self.name}

    async def __call__(self, command: str | None = None, restart: bool = False, **kwargs) -> Any:
        # Handle optional "restart" parameter to reset the shell session
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()
            return ToolResult(system="tool has been restarted.")

        # Ensure session is started
        if self._session is None:
            self._session = _BashSession()
            await self._session.start()

        # If no command provided, that's an error
        if command is None:
            raise ToolError("no command provided.")

        # Run the command in the bash session
        result: ToolResult = await self._session.run(command)
        # If the output is too large, split it into chunks using the token manager
        if isinstance(result, ToolResult) and result.output:
            # Estimate token count of output text
            output_tokens = token_manager.count_tokens(result.output)
            max_tokens = token_manager.max_output_tokens  # maximum tokens allowed in one output block
            if output_tokens > max_tokens:
                # Split the output text into chunks within the token limit
                chunks = token_manager.chunk_content(result.output, max_tokens=max_tokens)
                # Create a list of CLIResult objects for each chunk
                chunk_results: list[ToolResult] = []
                for i, chunk_text in enumerate(chunks):
                    # For each chunk, create a CLIResult. Only attach error on the last chunk.
                    if i == len(chunks) - 1:
                        chunk_results.append(CLIResult(output=chunk_text, error=result.error))
                    else:
                        chunk_results.append(CLIResult(output=chunk_text))
                return chunk_results  # return list of ToolResult chunks for streaming
        return result  # return single ToolResult if no chunking was needed

# Legacy tool class for older version (20241022), reusing the new implementation
class BashTool20241022(BashTool20250124):
    api_type: Literal["bash_20241022"] = "bash_20241022"

