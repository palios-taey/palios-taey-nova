# Updated token_manager (copy).txt
"""
Token Management Module for Claude DC
-------------------------------------
Prevents API rate limit errors by monitoring token usage and introducing delays.
Supports 128K output beta and sliding window rate limiting for input tokens.
"""
import time
from datetime import datetime, timezone
import logging
from typing import Dict, List, Tuple

# Configure logging for transparency (both to file and console)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/token_manager.log'), logging.StreamHandler()]
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manages API token usage and enforces rate limits (e.g., 40k/min input). Also handles extended output mode."""
    def __init__(self):
        # Token usage cumulative stats
        self.calls_made = 0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        # Sliding window tracking for per-minute rate limiting
        self.input_token_timestamps: List[Tuple[float, int]] = []
        self.output_token_timestamps: List[Tuple[float, int]] = []
        self.input_tokens_per_minute = 40000 # Setting the input token limit
        self.output_tokens_per_minute = 100000 # Example output token limit
        # Organization default limits per minute (if applicable)
        self.org_input_limit_per_min = None
        self.org_output_limit_per_min = None
        self.extended_output_beta = True  # Or True, depending on your default setting
        # Token bucket (client-side rate limiting) configuration
        self.tokens = self.input_tokens_per_minute  # Initialize with max capacity
        self.capacity = self.input_tokens_per_minute
        self.refill_rate = self.input_tokens_per_minute / 60  # Tokens per second
        self.last_refill_time = time.time()
        self.delays_required = 0
        self.total_delay_time = 0
        self.safe_max_tokens = 8000 # Example safe max output tokens
        self.safe_thinking_budget = 2000 # Example safe thinking budget

    def estimate_tokens_from_bytes(self, file_size_bytes: int) -> int:
        """Estimate the number of tokens for a given file size (very rough estimate)."""
        # This is a very rough estimate and might need adjustment based on the actual content.
        # Assuming an average of 4 bytes per token.
        return file_size_bytes // 4

    def consume_tokens(self, num_input_tokens: int, num_output_tokens: int = 0):
        """Record token usage and enforce rate limits."""
        now = time.time()
        self._refill_tokens(now)

        if self.tokens >= num_input_tokens:
            self.tokens -= num_input_tokens
            self.input_tokens_used += num_input_tokens
            self.input_token_timestamps.append((now, num_input_tokens))
            self.calls_made += 1
            self.output_tokens_used += num_output_tokens
            self.output_token_timestamps.append((now, num_output_tokens))
            return True
        else:
            delay = math.ceil((num_input_tokens - self.tokens) / self.refill_rate)
            logger.warning(f"Input token limit exceeded. Delaying for {delay} seconds.")
            time.sleep(delay)
            self.total_delay_time += delay
            self.delays_required += 1
            self.tokens = 0 # Reset tokens after delay
            self.consume_tokens(num_input_tokens, num_output_tokens) # Try again after delay
            return True

    def can_send(self, num_tokens: int) -> bool:
        """Check if enough tokens are available without consuming."""
        now = time.time()
        self._refill_tokens(now)
        return self.tokens >= num_tokens

    def get_safe_limits(self) -> Dict[str, int]:
        """Return safe maximum token limits for output and thinking budget."""
        return {"max_tokens": self.safe_max_tokens, "thinking_budget": self.safe_thinking_budget}

    def _refill_tokens(self, current_time: float):
        """Refill the token bucket based on the elapsed time."""
        elapsed_time = current_time - self.last_refill_time
        tokens_to_add = elapsed_time * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = current_time

    def _trim_history(self, history: List[Tuple[float, int]], interval: float):
        """Trim old token usage records beyond the given time interval (seconds)."""
        cutoff = time.time() - interval
        # Remove entries older than cutoff
        while history and history[0][0] < cutoff:
            history.pop(0)

    def get_usage_stats(self) -> Dict[str, any]:
        """
        Return current token usage and rate limit stats.
        """
        # Compute tokens used in last minute from history
        self._trim_history(self.input_token_timestamps, 60)
        self._trim_history(self.output_token_timestamps, 60)
        input_last_minute = sum(t for (_t, t) in self.input_token_timestamps)
        output_last_minute = sum(t for (_t, t) in self.output_token_timestamps)
        return {
            "calls_made": self.calls_made,
            "delays_required": self.delays_required,
            "total_delay_time": round(self.total_delay_time, 3),
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "input_tokens_last_minute": input_last_minute,
            "output_tokens_last_minute": output_last_minute,
            "extended_output_enabled": self.extended_output_beta,
            "safe_max_tokens": self.safe_max_tokens,
            "safe_thinking_budget": self.safe_thinking_budget,
            "rate_limits": {
                "input_tokens_per_minute": self.input_tokens_per_minute,
                "output_tokens_per_minute": self.output_tokens_per_minute,
                "org_input_limit_per_min": self.org_input_limit_per_min,
                "org_output_limit_per_min": self.org_output_limit_per_min,
                "token_bucket": {
                    "tokens": self.tokens,
                    "last_refill_time": self.last_refill_time,
                    "refill_rate": self.refill_rate,
                    "capacity": self.capacity,
                }
            }
        }
