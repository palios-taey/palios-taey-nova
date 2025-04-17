# computer_use_demo/token_manager.py
"""
Token Manager module for Claude Computer Use.

This module implements token usage tracking, rate limiting, and stream management
to ensure Claude can operate continuously without hitting API rate limits.
"""

import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from functools import wraps
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("token_manager")

# Constants for rate limiting
DEFAULT_INPUT_TOKEN_LIMIT = 40000  # per minute
DEFAULT_OUTPUT_TOKEN_LIMIT = 8000  # per minute
DEFAULT_SLIDING_WINDOW = 60  # seconds
MAX_RETRY_ATTEMPTS = 5
MAX_TOKENS_PER_REQUEST = 128000  # for Claude 3.7 Sonnet
RATE_LIMIT_SAFETY_BUFFER = 0.95  # Use only 95% of the limit to be safe

# File size estimation
CHARS_PER_TOKEN_APPROX = 4  # Average characters per token
MAX_FILE_SIZE_CHARS = DEFAULT_INPUT_TOKEN_LIMIT * CHARS_PER_TOKEN_APPROX / 2  # Per operation

@dataclass
class TokenUsage:
    """Tracks token usage with timestamps for sliding window calculation"""
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: float = field(default_factory=time.time)


class TokenBucketRateLimiter:
    """
    Implements token bucket algorithm for rate limiting API requests.
    Uses a sliding window to track token usage over time.
    """
    def __init__(
        self,
        input_token_limit: int = DEFAULT_INPUT_TOKEN_LIMIT,
        output_token_limit: int = DEFAULT_OUTPUT_TOKEN_LIMIT,
        window_size: int = DEFAULT_SLIDING_WINDOW
    ):
        self.input_token_limit = input_token_limit
        self.output_token_limit = output_token_limit
        self.window_size = window_size  # in seconds
        self.usage_history: List[TokenUsage] = []
        self.lock = threading.RLock()
        self.last_warning_time = 0
        logger.info(f"Initialized TokenBucketRateLimiter with input limit: {input_token_limit}, "
                   f"output limit: {output_token_limit}, window: {window_size}s")

    def _prune_history(self) -> None:
        """Remove token usage records older than the sliding window"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_size
            self.usage_history = [
                usage for usage in self.usage_history 
                if usage.timestamp >= cutoff_time
            ]

    def get_current_usage(self) -> Tuple[int, int]:
        """
        Calculate the current token usage within the sliding window.
        Returns (input_tokens, output_tokens) tuple.
        """
        self._prune_history()
        with self.lock:
            input_sum = sum(usage.input_tokens for usage in self.usage_history)
            output_sum = sum(usage.output_tokens for usage in self.usage_history)
            return input_sum, output_sum

    def get_available_tokens(self) -> Tuple[int, int]:
        """Calculate how many tokens are available before hitting rate limits"""
        input_used, output_used = self.get_current_usage()
        safe_input_limit = int(self.input_token_limit * RATE_LIMIT_SAFETY_BUFFER)
        safe_output_limit = int(self.output_token_limit * RATE_LIMIT_SAFETY_BUFFER)
        
        available_input = max(0, safe_input_limit - input_used)
        available_output = max(0, safe_output_limit - output_used)
        
        return available_input, available_output

    def can_process(self, input_tokens: int, output_tokens: int = 0) -> bool:
        """Check if there's enough capacity to process the specified tokens"""
        available_input, available_output = self.get_available_tokens()
        return input_tokens <= available_input and output_tokens <= available_output

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage with current timestamp"""
        with self.lock:
            self.usage_history.append(
                TokenUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    timestamp=time.time()
                )
            )
            input_used, output_used = self.get_current_usage()
            input_pct = input_used / self.input_token_limit * 100
            output_pct = output_used / self.output_token_limit * 100
            
            # Log if usage is getting high (only log once per 5 seconds to avoid spam)
            current_time = time.time()
            if (input_pct > 80 or output_pct > 80) and current_time - self.last_warning_time > 5:
                logger.warning(f"High token usage: {input_pct:.1f}% of input limit, "
                              f"{output_pct:.1f}% of output limit")
                self.last_warning_time = current_time

    async def wait_for_capacity(self, input_tokens: int, output_tokens: int = 0) -> None:
        """
        Wait until there's enough capacity to process the specified tokens.
        Uses exponential backoff with jitter for retries.
        """
        base_delay = 1.0
        max_delay = 60.0  # Maximum wait time in seconds
        attempt = 0
        
        while not self.can_process(input_tokens, output_tokens):
            attempt += 1
            if attempt > MAX_RETRY_ATTEMPTS:
                raise Exception(f"Failed to get token capacity after {MAX_RETRY_ATTEMPTS} attempts")
            
            # Calculate delay with exponential backoff and jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = delay * 0.1  # 10% jitter
            actual_delay = delay + (jitter * (2 * (0.5 - (time.time() % 1))))
            
            input_used, output_used = self.get_current_usage()
            logger.info(f"Waiting {actual_delay:.2f}s for token capacity. "
                        f"Using {input_used}/{self.input_token_limit} input, "
                        f"{output_used}/{self.output_token_limit} output tokens")
            
            await asyncio.sleep(actual_delay)
            self._prune_history()


class FileTokenEstimator:
    """Estimates token usage for file operations based on size and content"""
    
    @staticmethod
    def estimate_tokens_from_size(size_bytes: int) -> int:
        """Estimate tokens based on file size"""
        # Approximate using chars per token ratio
        return int(size_bytes / CHARS_PER_TOKEN_APPROX)
    
    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """Estimate tokens from text content"""
        # Basic estimation, should be replaced with actual tokenizer if available
        return int(len(text) / CHARS_PER_TOKEN_APPROX)
    
    @staticmethod
    def chunk_text(text: str, max_tokens: int) -> List[str]:
        """Split text into chunks that respect token limits"""
        if not text:
            return []
            
        # Approximate token count based on character count
        estimated_chars = max_tokens * CHARS_PER_TOKEN_APPROX
        
        # If text is already small enough, return it as is
        if len(text) <= estimated_chars:
            return [text]
            
        # Otherwise, chunk it
        chunks = []
        for i in range(0, len(text), estimated_chars):
            chunks.append(text[i:i + estimated_chars])
            
        return chunks


# Global instance for application-wide use
token_rate_limiter = TokenBucketRateLimiter()


def with_token_limiting(
    input_token_estimator: Callable[[Any], int],
    output_token_estimator: Optional[Callable[[Any], int]] = None
):
    """
    Decorator for functions that need token rate limiting.
    Waits for token capacity before executing the function.
    
    Args:
        input_token_estimator: Function that estimates input tokens from function args
        output_token_estimator: Function that estimates output tokens from function result
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Estimate input tokens
            input_tokens = input_token_estimator(*args, **kwargs)
            
            # Wait for token capacity
            await token_rate_limiter.wait_for_capacity(input_tokens)
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Estimate and record output tokens if output_token_estimator is provided
            output_tokens = 0
            if output_token_estimator:
                output_tokens = output_token_estimator(result)
            
            # Record token usage
            token_rate_limiter.record_usage(input_tokens, output_tokens)
            
            return result
        return wrapper
    return decorator


class StreamManager:
    """
    Manages streaming responses for large outputs.
    Handles buffering and backpressure to maintain rate limits.
    """
    def __init__(self, token_limiter: TokenBucketRateLimiter = token_rate_limiter):
        self.token_limiter = token_limiter
        
    async def process_stream(
        self, 
        stream_generator: Any, 
        token_estimator: Callable[[Any], int],
        processor: Callable[[Any], Any]
    ) -> Any:
        """
        Process a stream of data with token rate limiting.
        
        Args:
            stream_generator: Async generator producing stream chunks
            token_estimator: Function to estimate tokens from a chunk
            processor: Function to process each chunk
            
        Returns:
            The combined result from all processed chunks
        """
        results = []
        
        async for chunk in stream_generator:
            # Estimate tokens in this chunk
            tokens = token_estimator(chunk)
            
            # Wait for capacity if needed
            await self.token_limiter.wait_for_capacity(0, tokens)
            
            # Process the chunk
            processed = processor(chunk)
            results.append(processed)
            
            # Record token usage (0 input, only output)
            self.token_limiter.record_usage(0, tokens)
            
        return results


# Utility functions for common operations

def estimate_message_tokens(messages: List[Dict]) -> int:
    """Estimate tokens in a message object for Claude API"""
    # Very rough estimation - ideally use an actual tokenizer
    total_chars = 0
    
    for message in messages:
        role = message.get("role", "")
        total_chars += len(role)
        
        content = message.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    total_chars += len(item_type)
                    
                    if item_type == "text":
                        total_chars += len(item.get("text", ""))
    
    return int(total_chars / CHARS_PER_TOKEN_APPROX)
