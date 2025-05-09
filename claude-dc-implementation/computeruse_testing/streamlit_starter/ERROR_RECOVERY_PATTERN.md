# Error Recovery Pattern with Fibonacci Backoff

## Core Principle

The Error Recovery Pattern implements structured error handling with Fibonacci sequence backoff for retry attempts. This natural pattern creates harmonious recovery flows that match optimal growth patterns found in nature.

## Implementation Details

```python
from typing import TypeVar, Callable, Awaitable, Optional, Any, List
import asyncio
import time
import logging

T = TypeVar('T')

# Fibonacci sequence for backoff delays
FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21]

async def with_fibonacci_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 5,
    error_types: List[type] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any
) -> T:
    """
    Execute an async function with Fibonacci backoff retry pattern.
    
    Args:
        func: The async function to execute
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        error_types: List of exception types to catch and retry
        logger: Optional logger for recording retry attempts
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function execution
        
    Raises:
        Exception: If all retry attempts fail
    """
    if error_types is None:
        error_types = (Exception,)
    
    if logger is None:
        logger = logging.getLogger("fibonacci_retry")
    
    attempt = 0
    last_exception = None
    
    while attempt <= max_retries:
        try:
            return await func(*args, **kwargs)
        except error_types as e:
            last_exception = e
            attempt += 1
            
            if attempt > max_retries:
                break
            
            # Get the Fibonacci delay, cap at the end of our sequence
            delay = FIBONACCI_SEQUENCE[min(attempt - 1, len(FIBONACCI_SEQUENCE) - 1)]
            
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed with error: {str(e)}. "
                f"Retrying in {delay} seconds..."
            )
            
            await asyncio.sleep(delay)
    
    # If we get here, all retries failed
    logger.error(f"All {max_retries} retry attempts failed")
    raise last_exception
```

## Integration with Streaming Agent Loop

```python
async def agent_loop_with_recovery(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    # ... other parameters ...
):
    """Agent loop with error recovery."""
    try:
        # Main API call with retry
        stream = await with_fibonacci_retry(
            client.messages.create,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            tools=tools,
            stream=True,
            **extra_body,
            max_retries=5,
            error_types=[APIError, APIStatusError, APIResponseValidationError]
        )
        
        # Process streaming response...
        
    except Exception as e:
        # Handle unrecoverable errors
        logger.error(f"Unrecoverable error: {e}")
        output_callback({
            "type": "error",
            "message": f"Unrecoverable error: {e}"
        })
        return messages
```

## Tool Execution with Recovery

```python
async def execute_tool_with_recovery(
    tool_name: str, 
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """Execute tool with error recovery."""
    try:
        # First validate parameters
        is_valid, error_message = validate_tool_parameters(tool_name, tool_input)
        if not is_valid:
            return ToolResult(error=error_message)
        
        # Execute with recovery pattern
        if tool_name == "computer":
            result = await with_fibonacci_retry(
                execute_computer_tool,
                tool_input,
                progress_callback,
                max_retries=5,
                error_types=[OSError, IOError, RuntimeError]
            )
            return result
        elif tool_name == "bash":
            result = await with_fibonacci_retry(
                execute_bash_tool,
                tool_input,
                progress_callback,
                max_retries=3,
                error_types=[OSError, subprocess.SubprocessError]
            )
            return result
        else:
            return ToolResult(error=f"Unknown tool: {tool_name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return ToolResult(error=f"Tool execution failed: {str(e)}")
```

## Error Classification

Implement error classification to determine proper recovery action:

```python
def classify_error(error: Exception) -> str:
    """
    Classify an error to determine recovery strategy.
    
    Returns:
        One of: "retry", "fail", "partial_success"
    """
    if isinstance(error, (APIStatusError, ConnectionError)):
        # Network or API errors can be retried
        return "retry"
    elif isinstance(error, APIResponseValidationError):
        # Invalid response from API, might succeed with retry
        return "retry"
    elif isinstance(error, ValueError):
        # Parameter validation errors should fail fast
        return "fail"
    elif isinstance(error, TimeoutError):
        # Timeouts can be retried with longer timeout
        return "retry"
    else:
        # Default to retry for unknown errors
        return "retry"
```

## Streaming-Specific Recovery

For streaming operations, implement partial content recovery:

```python
async def recover_streaming_context(
    stream_state: Dict[str, Any],
    recovery_point: str,
    client: AsyncAnthropic
) -> AsyncGenerator:
    """
    Recover a streaming context from failure point.
    
    Args:
        stream_state: The current state of the stream
        recovery_point: Identifier for where to resume
        client: Anthropic client
        
    Returns:
        A new stream starting from recovery point
    """
    # Prepare recovery parameters
    recovery_params = {
        "model": stream_state.get("model"),
        "messages": stream_state.get("messages", []),
        "system": stream_state.get("system"),
        "max_tokens": stream_state.get("max_tokens", 4096),
        "tools": stream_state.get("tools", []),
        "stream": True,
        "recovery_point": recovery_point,  # This is hypothetical, actual implementation may vary
    }
    
    # Resume stream from recovery point
    return await client.messages.create(**recovery_params)
```

## Benefits of Fibonacci Backoff

1. More natural delay progression than exponential backoff
2. Initial retries happen quickly with small intervals
3. Later retries have longer intervals to allow system recovery
4. Resonates with natural processes and optimal recovery patterns
5. Avoids aggressive retry storms that can exacerbate issues