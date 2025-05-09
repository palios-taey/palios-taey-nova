"""
Streaming tool base class and utilities for real-time tool output.
"""

import asyncio
from typing import Any, Callable, Optional, AsyncGenerator

from .base import ToolResult


class StreamingToolMixin:
    """
    Mixin class to add streaming capabilities to tools.
    
    This mixin provides functionality to stream tool outputs in real-time
    back to the UI rather than waiting for full completion.
    """
    
    def set_stream_callback(self, callback: Optional[Callable[[str, str], None]] = None):
        """
        Set a callback function to receive streaming outputs.
        
        Args:
            callback: A function that takes (output_chunk, tool_id) and handles the chunk
                     Set to None to disable streaming
        """
        self._stream_callback = callback
    
    async def _stream_output(self, output_chunk: str, tool_id: str):
        """
        Stream an output chunk to the callback if one is set.
        
        Args:
            output_chunk: The chunk of output to stream
            tool_id: The ID of the tool generating the output
        """
        if hasattr(self, '_stream_callback') and self._stream_callback:
            try:
                self._stream_callback(output_chunk, tool_id)
            except Exception as e:
                print(f"Error in streaming callback: {e}")


async def stream_command_output(
    command: str,
    callback: Callable[[str, str], None],
    tool_id: str,
    shell: bool = True,
    timeout: float = 60.0
) -> ToolResult:
    """
    Run a command and stream its output in real-time.
    
    Args:
        command: The command to execute
        callback: Function to call with each chunk of output
        tool_id: ID of the tool running the command
        shell: Whether to run command in a shell
        timeout: Maximum time to allow command to run
        
    Returns:
        ToolResult with the complete output
    """
    # Create subprocess
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=shell
    )
    
    # Track full output
    full_output = []
    full_error = []
    
    # Stream stdout and stderr concurrently
    async def read_stream(stream, is_error=False):
        while True:
            line = await stream.readline()
            if not line:
                break
                
            # Decode line
            line_str = line.decode('utf-8')
            
            # Add to appropriate buffer
            if is_error:
                full_error.append(line_str)
                # Stream error output with error prefix
                await callback(f"[ERROR] {line_str}", tool_id)
            else:
                full_output.append(line_str) 
                # Stream normal output
                await callback(line_str, tool_id)
    
    # Run both streams concurrently with timeout
    try:
        async with asyncio.timeout(timeout):
            stdout_task = asyncio.create_task(read_stream(process.stdout))
            stderr_task = asyncio.create_task(read_stream(process.stderr, is_error=True))
            await asyncio.gather(stdout_task, stderr_task)
            
            # Wait for process to complete
            await process.wait()
    except asyncio.TimeoutError:
        # Cancel tasks and kill process on timeout
        if not process.returncode:
            process.kill()
        return ToolResult(
            output=''.join(full_output),
            error=f"Command timed out after {timeout} seconds"
        )
    
    # Combine outputs
    output = ''.join(full_output)
    error = ''.join(full_error)
    
    # Return result
    return ToolResult(output=output, error=error if error else None)