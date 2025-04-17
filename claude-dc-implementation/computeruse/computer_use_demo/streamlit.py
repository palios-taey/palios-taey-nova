"""
Streaming implementation for Anthropic Claude API requests.
Handles large token outputs and provides efficient token usage.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaContentBlockParam

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claude_streaming")

# Constants
STREAMING_THRESHOLD = 21333  # Use streaming for outputs larger than this
LARGE_OUTPUT_BETA = "output-128k-2025-02-19"  # Beta flag for 128K output tokens


async def stream_response(
    client: Any,
    model: str,
    messages: List[BetaMessageParam],
    system: List[Any],
    max_tokens: int,
    tools: List,
    betas: List[str],
    extra_body: Dict[str, Any] = None,
    callback: Optional[Callable[[str], None]] = None
) -> Tuple[Any, BetaMessage]:
    """
    Stream a response from the Claude API with proper error handling.
    
    Args:
        client: Anthropic API client
        model: Model name to use
        messages: List of message objects
        system: System prompt
        max_tokens: Maximum tokens to generate
        tools: Tool definitions
        betas: Beta flags
        extra_body: Additional parameters for the API request
        callback: Optional callback function for streaming updates
        
    Returns:
        Tuple of (http_response, parsed_message)
    """
    logger.info(f"Using streaming for response (max_tokens: {max_tokens})")
    
    # Ensure we have the extended output beta for large responses
    if max_tokens > 64000 and LARGE_OUTPUT_BETA not in betas:
        betas.append(LARGE_OUTPUT_BETA)
        logger.info(f"Added {LARGE_OUTPUT_BETA} beta flag for large output")
    
    # Default empty extra_body if None
    if extra_body is None:
        extra_body = {}
    
    try:
        stream = client.beta.messages.with_raw_response.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools,
            betas=betas,
            **extra_body
        )
        
        # Process the stream
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            
            if callback and hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                callback(chunk.delta.text)
                
        # Extract the final response and HTTP info
        if chunks:
            # For HTTP response info, use the first chunk
            http_response = chunks[0].http_response if chunks else None
            
            # The last chunk contains the complete response
            full_content = chunks[-1].parse()
            
            return http_response, full_content
        else:
            raise Exception("No content received from streaming API")
            
    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}")
        raise e


def should_use_streaming(max_tokens: int, model: str = None) -> bool:
    """Determine if streaming should be used based on output size and model."""
    # Always use streaming for large outputs
    if max_tokens > STREAMING_THRESHOLD:
        return True
        
    # Use streaming for Claude 3.7 models (they have higher token capacities)
    if model and "3-7" in model:
        return True
        
    return False
