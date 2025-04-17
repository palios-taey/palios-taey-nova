# token_manager.py
import time
import math
import logging
from typing import Dict, List, Tuple, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/token_manager.log"), logging.StreamHandler()]
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manage token usage and enforce rate limits (e.g. 40K input tokens/minute)."""
    def __init__(self):
        # Cumulative usage
        self.calls_made = 0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        # Sliding window (last 60s) usage tracking
        self.input_token_timestamps: List[Tuple[float, int]] = []
        self.output_token_timestamps: List[Tuple[float, int]] = []
        # Rate limits per minute
        self.input_tokens_per_minute = 40000
        self.output_tokens_per_minute = 100000  # hypothetical output limit
        # Organization limits (from API headers, if provided)
        self.org_input_limit_per_min = None
        self.org_output_limit_per_min = None
        self.org_req_limit_per_min = None
        # Extended output mode flag
        self.extended_output_beta = True
        # Safe token limits for outputs and chain-of-thought
        self.safe_max_tokens = 8000
        self.safe_thinking_budget = 2000
        # Token bucket for input rate limiting
        self.capacity = self.input_tokens_per_minute
        self.tokens = self.capacity
        self.refill_rate = self.input_tokens_per_minute / 60.0
        self.last_refill_time = time.time()
        # Delay stats
        self.delays_required = 0
        self.total_delay_time = 0.0
        # Storage for leftover output chunks (for large file outputs)
        self.leftover_chunks: Dict[str, str] = {}

    def estimate_tokens_from_bytes(self, num_bytes: int) -> int:
        """Estimate token count for a given byte length of text (approx 4 chars per token)."""
        return num_bytes // 4

    def _refill_tokens(self, current_time: float):
        # Refill token bucket based on elapsed time since last check
        elapsed = current_time - self.last_refill_time
        if elapsed > 0:
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill_time = current_time

    def consume_tokens(self, num_input_tokens: int, num_output_tokens: int = 0) -> bool:
        """Consume tokens for a request (input and output), delaying if input rate limit exceeded."""
        now = time.time()
        self._refill_tokens(now)
        if num_input_tokens > self.tokens:
            # Need to delay to respect input rate limit
            deficit = num_input_tokens - self.tokens
            delay_seconds = math.ceil(deficit / self.refill_rate)
            logger.warning(f"Input token rate exceeded, sleeping for {delay_seconds}s")
            time.sleep(delay_seconds)
            self.delays_required += 1
            self.total_delay_time += delay_seconds
            # Reset bucket after delay
            now = time.time()
            self.last_refill_time = now
            self.tokens = self.capacity - num_input_tokens if num_input_tokens < self.capacity else 0
        else:
            self.tokens -= num_input_tokens
        # Record usage
        self.calls_made += 1
        self.input_tokens_used += num_input_tokens
        self.output_tokens_used += num_output_tokens
        self.input_token_timestamps.append((now, num_input_tokens))
        self.output_token_timestamps.append((now, num_output_tokens))
        return True

    def can_send(self, num_tokens: int) -> bool:
        """Check if the given number of input tokens can be sent now without delay."""
        self._refill_tokens(time.time())
        return self.tokens >= num_tokens

    def manage_request(self, headers: Dict[str, Any]) -> None:
        """Update internal counters based on API response headers (Anthropic rate-limit info)."""
        try:
            if 'anthropic-ratelimit-input-tokens-limit' in headers:
                self.org_input_limit_per_min = int(headers['anthropic-ratelimit-input-tokens-limit'])
            if 'anthropic-ratelimit-input-tokens-remaining' in headers and self.org_input_limit_per_min is not None:
                remaining = int(headers['anthropic-ratelimit-input-tokens-remaining'])
                used_total = self.org_input_limit_per_min - remaining
                # Calculate tokens used in this request (difference from previous total)
                used_now = used_total - (self.input_tokens_used if used_total >= self.input_tokens_used else 0)
                self.input_tokens_used = used_total
                if used_now > 0:
                    self.input_token_timestamps.append((time.time(), used_now))
            if 'anthropic-ratelimit-output-tokens-limit' in headers:
                self.org_output_limit_per_min = int(headers['anthropic-ratelimit-output-tokens-limit'])
            if 'anthropic-ratelimit-output-tokens-remaining' in headers and self.org_output_limit_per_min is not None:
                remaining_out = int(headers['anthropic-ratelimit-output-tokens-remaining'])
                used_total_out = self.org_output_limit_per_min - remaining_out
                used_now_out = used_total_out - (self.output_tokens_used if used_total_out >= self.output_tokens_used else 0)
                self.output_tokens_used = used_total_out
                if used_now_out > 0:
                    self.output_token_timestamps.append((time.time(), used_now_out))
            if 'anthropic-ratelimit-requests-limit' in headers:
                self.org_req_limit_per_min = int(headers['anthropic-ratelimit-requests-limit'])
        except Exception as e:
            logger.warning(f"Error parsing rate-limit headers: {e}")
        return

    def get_safe_limits(self) -> Dict[str, int]:
        """Return safe maximum tokens for outputs and thinking."""
        return {"max_tokens": self.safe_max_tokens, "thinking_budget": self.safe_thinking_budget}

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage and rate-limit status."""
        # Trim entries older than 60 seconds
        cutoff = time.time() - 60
        while self.input_token_timestamps and self.input_token_timestamps[0][0] < cutoff:
            self.input_token_timestamps.pop(0)
        while self.output_token_timestamps and self.output_token_timestamps[0][0] < cutoff:
            self.output_token_timestamps.pop(0)
        input_last_min = sum(t for (_ts, t) in self.input_token_timestamps)
        output_last_min = sum(t for (_ts, t) in self.output_token_timestamps)
        return {
            "calls_made": self.calls_made,
            "delays_required": self.delays_required,
            "total_delay_time": round(self.total_delay_time, 2),
            "input_tokens_used_total": self.input_tokens_used,
            "output_tokens_used_total": self.output_tokens_used,
            "input_tokens_last_minute": input_last_min,
            "output_tokens_last_minute": output_last_min,
            "extended_output_beta": self.extended_output_beta,
            "safe_max_tokens": self.safe_max_tokens,
            "safe_thinking_budget": self.safe_thinking_budget,
            "rate_limits": {
                "input_tokens_per_minute": self.input_tokens_per_minute,
                "output_tokens_per_minute": self.output_tokens_per_minute,
                "org_input_limit_per_min": self.org_input_limit_per_min,
                "org_output_limit_per_min": self.org_output_limit_per_min,
                "org_request_limit_per_min": self.org_req_limit_per_min,
            }
        }

# Create a singleton TokenManager for use across the app
token_manager = TokenManager()

