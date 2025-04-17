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
        self.input_tokens_per_minute = 0
        self.output_tokens_per_minute = 0
        # Organization default limits per minute (if applicable)
        self.org_input_limit_per_min = None
        self.org_output_limit_per_min = None
        self.extended_output_beta = True  # Or True, depending on your default setting
        # Token bucket (client-side rate limiting) configuration
        self.token_bucket_capacity = 40000  # maximum input tokens per minute allowed
        self.token_bucket_refill_rate = 40000 / 60.0  # tokens per second (approx 667 tokens/sec)
        self.tokens_available = self.token_bucket_capacity  # start full
        self.last_refill_time = time.time()
        # Rate limiting delay stats
        self.delays_required = 0
        self.total_delay_time = 0.0

        # Determine safe default token limits based on model capacity
        if self.extended_output_beta:
            self.safe_max_tokens = 8192  # safe default output tokens for extended model (Claude 3.7)
            self.safe_thinking_budget = 4096  # safe default thinking budget (half of safe output)
        else:
            self.safe_max_tokens = 4096  # safe default output tokens for non-extended model
            self.safe_thinking_budget = 2048  # safe default thinking budget

        # Extended output beta usage (128K context)
        self.extended_output_beta = True
        logger.info("Token manager initialized with sliding window rate limit and extended output beta mode")

    def _refill_token_bucket(self):
        """Refill the token bucket based on time elapsed since last refill."""
        current_time = time.time()
        if current_time > self.last_refill_time:
            elapsed = current_time - self.last_refill_time
            added_tokens = elapsed * self.token_bucket_refill_rate
            # Add tokens to the bucket without exceeding capacity
            self.tokens_available = min(self.token_bucket_capacity, self.tokens_available + added_tokens)
            self.last_refill_time = current_time

    def delay_if_needed(self, input_tokens: int, output_tokens: int = 0) -> None:
        """
        Enforce the input token rate limit by delaying if adding `input_tokens` would exceed the limit.
        Logs output token usage (for observability) but does not enforce an output rate limit.
        """
        if output_tokens:
            logger.info(f"Processing {input_tokens} input tokens, {output_tokens} output tokens (output not throttled)")
        needed = input_tokens
        # Consume from token bucket and delay if needed
        while needed > 0:
            self._refill_token_bucket()
            if self.tokens_available > 0:
                take = min(self.tokens_available, needed)
                self.tokens_available -= take
                needed -= take
                # Record token consumption
                self.input_tokens_used += take
                self.input_token_timestamps.append((time.time(), take))
                # Trim history to last 60s for stats
                self._trim_history(self.input_token_timestamps, 60)
            if needed > 0:
                # Not enough tokens available; calculate wait time for remainder
                tokens_to_wait_for = min(needed, self.token_bucket_capacity)
                wait_seconds = (tokens_to_wait_for - self.tokens_available) / self.token_bucket_refill_rate
                wait_seconds = max(wait_seconds, 0.0)
                # Log and sleep
                self.delays_required += 1
                self.total_delay_time += wait_seconds
                logger.info(f"Throttling input: sleeping {wait_seconds:.2f}s to respect rate limit")
                time.sleep(wait_seconds)
            else:
                break
        # Rate limit satisfied; safe to proceed

    def get_safe_limits(self) -> Dict[str, int]:
        """Get safe token limits for max_tokens and thinking_budget."""
        return {
            "max_tokens": self.safe_max_tokens,
            "thinking_budget": self.safe_thinking_budget
        }

    def process_response_headers(self, headers: Dict[str, any]) -> None:
        """
        Process API response headers to update token usage statistics after a response.
        """
        self.calls_made += 1
        # Parse any provided header values for usage
        try:
            prompt_tokens = int(headers.get("x-usage-prompt-tokens") or headers.get("prompt-tokens") or headers.get("x-prompts-consumed") or 0)
            completion_tokens = int(headers.get("x-usage-completion-tokens") or headers.get("completion-tokens") or headers.get("x-tokens-generated") or 0)
        except Exception as e:
            prompt_tokens = 0
            completion_tokens = 0
        if prompt_tokens:
            # If actual prompt token count is reported and exceeds our current count, update
            if prompt_tokens > self.input_tokens_used:
                self.input_tokens_used = prompt_tokens
        if completion_tokens:
            self.output_tokens_used += completion_tokens
            # Track output tokens in a sliding window for observability
            self.output_token_timestamps.append((time.time(), completion_tokens))
            self._trim_history(self.output_token_timestamps, 60)
        # Handle any rate limit reset or retry-after headers
        reset_time = None
        if "x-ratelimit-reset" in headers or "anthropic-ratelimit-reset" in headers:
            reset_str = headers.get("x-ratelimit-reset") or headers.get("anthropic-ratelimit-reset")
            try:
                reset_time = datetime.fromisoformat(str(reset_str).replace('Z', '+00:00'))
            except Exception as e:
                logger.debug(f"Could not parse reset time: {reset_str} ({e})")
        if reset_time:
            # (Optional) We could use reset_time to inform future token budgeting if needed
            pass
        if "retry-after" in headers:
            try:
                delay_sec = float(headers.get("retry-after"))
            except Exception:
                try:
                    delay_sec = float(headers.get("retry-after-ms", 0)) / 1000.0
                except Exception:
                    delay_sec = None
            if delay_sec:
                self.delays_required += 1
                self.total_delay_time += delay_sec
                logger.warning(f"Rate limit hit, sleeping for Retry-After: {delay_sec:.2f}s")
                time.sleep(delay_sec)
        # Log if output tokens exceed normal thresholds
        if completion_tokens:
            if not self.extended_output_beta and completion_tokens > 16000:
                logger.info(f"Output tokens ({completion_tokens}) exceeded normal threshold (16000). Consider enabling extended output beta.")
            elif self.extended_output_beta and completion_tokens > 128000:
                logger.info(f"Output tokens ({completion_tokens}) exceeded extended output threshold (128000).")

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
            "safe_thinking_budget": self.safe_thinking_budget
        }

# Initialize a singleton token manager instance for the application
token_manager = TokenManager()

