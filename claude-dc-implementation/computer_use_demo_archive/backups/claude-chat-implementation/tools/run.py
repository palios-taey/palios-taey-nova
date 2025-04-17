# computer_use_demo/tools/run.py
"""Utility to run shell commands asynchronously with a timeout."""

import asyncio
import logging
from computer_use_demo.token_manager import token_rate_limiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_utility")

TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"
MAX_RESPONSE_LEN: int = 16000


def maybe_truncate(content: str, truncate_after: int | None = MAX_RESPONSE_LEN):
    """Truncate content and append a notice if content exceeds the specified length."""
    if not content:
        return content
        
    if not truncate_after or len(content) <= truncate_after:
        return content
        
    # Track token usage for truncation
    estimated_tokens = len(content) // 4
    truncated_tokens = truncate_after // 4
    token_savings = estimated_tokens - truncated_tokens
    
    logger.info(f"Truncating response, saving approximately {token_savings} tokens")
    
    return content[:truncate_after] + TRUNCATED_MESSAGE


async def run(
    cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN,
):
    """Run a shell command asynchronously with a timeout."""
    # Track token usage for command
    input_tokens = len(cmd) // 4
    await token_rate_limiter.wait_for_capacity(input_tokens)
    token_rate_limiter.record_usage(input_tokens, 0)
    
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout_text = stdout.decode()
        stderr_text = stderr.decode()
        
        # Track token usage for response
        output_tokens = (len(stdout_text) + len(stderr_text)) // 4
        token_rate_limiter.record_usage(0, output_tokens)
        
        return (
            process.returncode or 0,
            maybe_truncate(stdout_text, truncate_after=truncate_after),
            maybe_truncate(stderr_text, truncate_after=truncate_after),
        )
    except asyncio.TimeoutError as exc:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        raise TimeoutError(
            f"Command '{cmd}' timed out after {timeout} seconds"
        ) from exc
