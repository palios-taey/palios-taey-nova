"""
Token Management Module for Claude DC
-------------------------------------
Prevents API rate limit errors by monitoring token usage and introducing delays.
Supports 128K output beta and sliding-window rate limiting.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Any, List

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/token_manager.log'), logging.StreamHandler()]
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manages API token usage to prevent rate limit errors (40k/min input, 16k/min output)."""
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
        # Organization default limits per minute
        self.org_input_limit = 40000    # 40K input tokens per minute
        self.org_output_limit = 16000   # 16K output tokens per minute
        # Warning thresholds (80% of limit by default)
        self.input_token_warning_threshold = 0.8
        self.output_token_warning_threshold = 0.8
        # Overall token budget (for tracking total usage, e.g. 1M tokens)
        self.token_budget = 1000000
        self.remaining_budget = self.token_budget
        # Safe limits for model calls (avoid validation errors)
        self.safe_max_tokens = 20000       # safe max output tokens to request
        self.safe_thinking_budget = 4000   # safe max "thinking" budget tokens
        # Extended output beta usage
        self.extended_output_beta = True
        logger.info("Token manager initialized with sliding window rate limiting")

    def _parse_reset_time(self, reset_time_str: str) -> datetime:
        """Parse ISO format reset time from API headers."""
        try:
            return datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Error parsing reset time '{reset_time_str}': {e}")
            return datetime.now(timezone.utc) + timedelta(seconds=60)

    def _calculate_delay(self, reset_time: Optional[datetime], used_quota: float) -> float:
        """Calculate necessary delay based on quota usage and time until reset."""
        if reset_time is None:
            # If no exact reset timestamp, apply progressive backoff when over threshold
            if used_quota > self.input_token_warning_threshold:
                backoff_factor = [1, 1, 2, 3, 5, 8, 13][0]  # simplified backoff (first element)
                delay = backoff_factor * (used_quota - self.input_token_warning_threshold) * 5
                return max(delay, 0.1)
            return 0.1
        now = datetime.now(timezone.utc)
        if reset_time > now:
            time_to_reset = (reset_time - now).total_seconds()
            if used_quota > self.input_token_warning_threshold:
                backoff_factor = [1, 1, 2, 3, 5, 8, 13][0]
                delay = time_to_reset * (used_quota - self.input_token_warning_threshold) * backoff_factor
                return max(delay, 0.1)
        return 0.0

    def check_input_rate_limit(self, input_tokens: int) -> Tuple[bool, float]:
        """Check input token rate limit window and determine if a delay is needed."""
        current_time = time.time()
        # Record this request in the sliding window
        self.input_token_timestamps.append((current_time, input_tokens))
        # Remove entries older than 60 seconds
        one_minute_ago = current_time - 60
        self.input_token_timestamps = [(ts, tok) for ts, tok in self.input_token_timestamps if ts >= one_minute_ago]
        self.input_tokens_per_minute = sum(tok for _, tok in self.input_token_timestamps)
        logger.info(f"Input tokens per minute: {self.input_tokens_per_minute}/{self.org_input_limit}")
        if self.input_tokens_per_minute >= self.org_input_limit * self.input_token_warning_threshold:
            # Oldest request in window
            if self.input_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.input_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                delay = max(seconds_to_wait, 0) + 1
                logger.warning(f"Approaching input token rate limit - need to wait {delay:.2f} seconds")
                print(f"⚠️ Input token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        return False, 0

    def check_output_rate_limit(self, output_tokens: int) -> Tuple[bool, float]:
        """Check output token rate limit window and determine if a delay is needed."""
        current_time = time.time()
        self.output_token_timestamps.append((current_time, output_tokens))
        one_minute_ago = current_time - 60
        self.output_token_timestamps = [(ts, tok) for ts, tok in self.output_token_timestamps if ts >= one_minute_ago]
        self.output_tokens_per_minute = sum(tok for _, tok in self.output_token_timestamps)
        logger.info(f"Output tokens per minute: {self.output_tokens_per_minute}/{self.org_output_limit}")
        if self.output_tokens_per_minute >= self.org_output_limit * self.output_token_warning_threshold:
            if self.output_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.output_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                delay = max(seconds_to_wait, 0) + 1
                logger.warning(f"Approaching output token rate limit - need to wait {delay:.2f} seconds")
                print(f"⚠️ Output token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        return False, 0

    def get_safe_limits(self) -> Dict[str, int]:
        """Get safe token limits for max_tokens and thinking_budget."""
        return {
            "max_tokens": self.safe_max_tokens,
            "thinking_budget": self.safe_thinking_budget
        }

    def delay_if_needed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> None:
        """Delay execution if needed to avoid hitting token rate limits."""
        should_delay_input, delay_time_input = self.check_input_rate_limit(estimated_input_tokens)
        should_delay_output, delay_time_output = self.check_output_rate_limit(estimated_output_tokens)
        if should_delay_input or should_delay_output:
            delay_time = max(delay_time_input, delay_time_output)
            logger.info(f"Delaying for {delay_time:.2f} seconds to avoid rate limit")
            print(f"🕒 Delaying for {delay_time:.2f} seconds to avoid rate limit.")
            time.sleep(delay_time)
            print("✅ Resuming after delay")

    def get_stats(self) -> Dict[str, Any]:
        """Return current usage statistics."""
        return {
            "calls_made": self.calls_made,
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "input_tokens_per_minute": self.input_tokens_per_minute,
            "output_tokens_per_minute": self.output_tokens_per_minute,
            "remaining_budget": self.remaining_budget,
            "extended_output_beta": self.extended_output_beta
        }

    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """Process API response headers to track token usage."""
        self.calls_made += 1
        def get_header_int(key: str, default: int = 0) -> int:
            try:
                return int(headers.get(key, default))
            except (ValueError, TypeError):
                return default
        # Update usage from headers if present
        input_tokens = get_header_int('anthropic-input-tokens')
        output_tokens = get_header_int('anthropic-output-tokens')
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens
        self.remaining_budget = self.token_budget - self.output_tokens_used
        logger.info(f"API call used {input_tokens} input tokens and {output_tokens} output tokens")
        logger.info(f"Total so far: {self.input_tokens_used} input, {self.output_tokens_used} output; Remaining budget: {self.remaining_budget}")
        input_limit = get_header_int('anthropic-ratelimit-input-tokens-limit', 40000)
        output_limit = get_header_int('anthropic-ratelimit-output-tokens-limit', 16000)
        # (We rely on our own limits; just logging any header-provided limits)
        logger.info(f"Anthropic reported limits: {input_limit} input/min, {output_limit} output/min")

# Create a singleton instance for convenience
token_manager = TokenManager()
