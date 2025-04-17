"""
Token Management Module for Claude DC
-------------------------------------
Enforces API token rate limits to prevent 429 errors by throttling input tokens to the model.
Applies a strict per-minute input token limit (default 40,000 tokens/min) to both user prompts and tool outputs.
Implements a token bucket rate limiter (a proven strategy used by companies like Stripe&#8203;:contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}) 
to allow bursts while maintaining the average rate. This prevents Claude from exceeding input limits.
Optionally, supports an extended output mode (128K token beta) which raises allowable output token thresholds (logged for observability 
but not enforcing output limits yet).
 
References:
 - Stripe recommends client-side token bucket rate limiting&#8203;:contentReference[oaicite:2]{index=2}.
 - Cloudflare uses sliding window algorithms for strict rate limits&#8203;:contentReference[oaicite:3]{index=3}.
"""
import time
from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Any, Deque, Tuple
from collections import deque

# Configure logging to both file and console for transparency
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/token_manager.log'), logging.StreamHandler()]
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manages API token usage and enforces rate limits (40k/min input, optional extended output)."""
    def __init__(self, input_rate_limit: int = 40000, extended_output: bool = False):
        """
        Initialize the TokenManager.
        Args:
            input_rate_limit: Maximum input tokens per minute (default 40000, i.e. Claude's limit).
            extended_output: True if 128K output beta is enabled, to adjust output thresholds.
        """
        # Rate limit settings
        self.input_rate_limit = input_rate_limit             # tokens per minute allowed
        self._tokens_per_second = input_rate_limit / 60.0    # refill rate (tokens per second)
        self._bucket_capacity = input_rate_limit             # max tokens bucket can hold (strict per-minute capacity)
        self._tokens_available = input_rate_limit            # start full so initial messages can send immediately up to limit
        self._last_refill_time = time.time()                 # last time tokens were refilled
        # Extended output mode
        self.extended_output = extended_output
        # Set output token threshold for logging (do not enforce output rate limit yet)
        self.output_token_threshold = 128000 if extended_output else 16000
        # Usage statistics and tracking
        self.calls_made = 0
        self.delays_required = 0
        self.total_delay_time = 0.0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        # Track recent input and output usage events for observability (sliding window of 60s)
        self._input_history: Deque[Tuple[float,int]] = deque()    # (timestamp, tokens) for each input token batch
        self._output_history: Deque[Tuple[float,int]] = deque()   # (timestamp, tokens) for each output batch (per API response)
        logger.info(f"TokenManager initialized (rate={input_rate_limit}/min, extended_output={extended_output})")

    def _refill_tokens(self) -> None:
        """Refill the token bucket based on time elapsed since last refill."""
        now = time.time()
        if now > self._last_refill_time:
            # add tokens based on elapsed time
            elapsed = now - self._last_refill_time
            added_tokens = elapsed * self._tokens_per_second
            if added_tokens > 0:
                self._tokens_available = min(self._bucket_capacity, self._tokens_available + added_tokens)
                self._last_refill_time = now
        # Note: We don't allow tokens to accumulate beyond capacity

    def delay_if_needed(self, input_tokens: int) -> None:
        """
        Block (sleep) if necessary to ensure adding `input_tokens` does not exceed the rate limit.
        This should be called before injecting a user prompt or any content into Claude's context.
        """
        needed = input_tokens
        # Throttle as needed using token bucket: consume available tokens, then wait for refills if required
        while needed > 0:
            # Refill tokens according to time passed
            self._refill_tokens()
            if self._tokens_available > 0:
                # Use as many tokens as possible from the bucket
                take = min(self._tokens_available, needed)
                self._tokens_available -= take
                needed -= take
                # Record this consumption
                self.input_tokens_used += take
                self._input_history.append((time.time(), take))
                # Trim old usage beyond 60 seconds for stats
                self._trim_history(self._input_history, 60)
            # If more tokens are still needed, bucket is now empty (or not enough tokens yet)
            if needed > 0:
                # Determine how many tokens we should wait for: either a full bucket or just the remainder needed
                tokens_to_wait_for = min(needed, self._bucket_capacity)
                # Calculate how long to wait to accumulate that many tokens
                wait_seconds = (tokens_to_wait_for - self._tokens_available) / self._tokens_per_second
                wait_seconds = max(wait_seconds, 0.0)
                # Log and perform the delay
                self.delays_required += 1
                self.total_delay_time += wait_seconds
                logger.info(f"Throttling input: sleeping {wait_seconds:.2f}s to respect token rate limit")
                time.sleep(wait_seconds)
                # Loop will refill tokens after this sleep and continue consumption
                # Note: We do not directly consume in this step; consumption happens in the next iteration after refill.
            else:
                break  # no more tokens needed
        # All required tokens have been accounted; it is now safe to proceed
        return None

    def record_tool_output(self, input_tokens: int) -> None:
        """
        Record tokens produced by a tool (to be appended to the prompt) and throttle if needed.
        Tool outputs count towards the input token rate limit just like user input.
        """
        # We treat tool output as additional input to the model context.
        logger.debug(f"Recording tool output of {input_tokens} tokens")
        # Use the same logic as user input for rate limiting
        self.delay_if_needed(input_tokens)
        return None

    def process_response_headers(self, headers: Dict[str, Any]) -> None:
        """
        Process the API response headers after streaming a model response to update token usage stats.
        This should be called once a Claude API response has completed.
        """
        self.calls_made += 1
        # If the API provided usage info in headers, update stats accordingly
        # e.g., 'x-usage-prompt-tokens' or 'x-usage-completion-tokens' (if available from provider)
        try:
            # Some APIs might return header keys in different cases or as ints; handle gracefully
            prompt_tokens = int(headers.get("x-usage-prompt-tokens") or headers.get("prompt-tokens") or headers.get("x-prompts-consumed") or 0)
            completion_tokens = int(headers.get("x-usage-completion-tokens") or headers.get("completion-tokens") or headers.get("x-tokens-generated") or 0)
        except Exception as e:
            prompt_tokens = 0
            completion_tokens = 0
        if prompt_tokens > 0:
            # Adjust input token usage if actual usage is reported
            diff = prompt_tokens - 0  # We could subtract what we counted for this call if tracked per-call
            # For simplicity, just ensure our total input_tokens_used reflects at least this value
            if prompt_tokens > 0 and prompt_tokens > self.input_tokens_used:
                self.input_tokens_used = prompt_tokens
        if completion_tokens > 0:
            self.output_tokens_used += completion_tokens
            # Track output token event for observability (per-minute rate, etc.)
            self._output_history.append((time.time(), completion_tokens))
            self._trim_history(self._output_history, 60)
        # Check for any rate limit reset or retry-after headers to possibly adjust behavior
        reset_time = None
        if "x-ratelimit-reset" in headers or "anthropic-ratelimit-reset" in headers:
            reset_str = headers.get("x-ratelimit-reset") or headers.get("anthropic-ratelimit-reset")
            try:
                reset_time = datetime.fromisoformat(str(reset_str).replace('Z', '+00:00'))
            except Exception as e:
                logger.debug(f"Could not parse reset time: {reset_str} ({e})")
        if reset_time:
            # If we know when the limit window resets, we might use it in future (not strictly needed with token bucket approach).
            pass  # (Optional: could store next reset target)
        # If Retry-After is provided (in seconds), we can delay further calls accordingly
        if "retry-after" in headers:
            try:
                ra_value = headers.get("retry-after")
                delay_sec = float(ra_value)
            except Exception:
                try:
                    delay_sec = (float(headers.get("retry-after-ms", 0)) / 1000.0)
                except Exception:
                    delay_sec = None
            if delay_sec:
                # Log and enforce the suggested delay
                self.delays_required += 1
                self.total_delay_time += delay_sec
                logger.warning(f"Rate limit hit, sleeping for Retry-After: {delay_sec:.2f}s")
                time.sleep(delay_sec)
        # Log output token info if it exceeds thresholds (observability for extended output)
        if completion_tokens > 0:
            if not self.extended_output and completion_tokens > self.output_token_threshold:
                logger.info(f"Output tokens ({completion_tokens}) exceeded normal threshold ({self.output_token_threshold}). Consider enabling 128K output beta for long responses.")
            elif self.extended_output and completion_tokens > self.output_token_threshold:
                logger.info(f"Output tokens ({completion_tokens}) exceeded extended output threshold ({self.output_token_threshold}).")
        return None

    def _trim_history(self, history: Deque[Tuple[float,int]], interval: float) -> None:
        """Trim old entries from a usage history deque beyond a given time interval (seconds)."""
        cutoff = time.time() - interval
        while history and history[0][0] < cutoff:
            history.popleft()
        # no return needed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about token usage and rate limiting.
        Returns a dictionary with keys:
         - calls_made: number of API calls completed
         - delays_required: how many times a delay was performed to throttle
         - total_delay_time: total time (seconds) spent in delays
         - input_tokens_used: total input tokens sent so far
         - output_tokens_used: total output tokens received so far
         - input_tokens_last_minute: approximate input tokens used in the last 60 seconds
         - output_tokens_last_minute: approximate output tokens in the last 60 seconds
         - extended_output_enabled: whether extended output mode is enabled
         - input_rate_limit: configured input token rate limit per minute
         - output_token_threshold: current output token threshold for logging
        """
        # Calculate tokens in last 60 seconds from history
        self._trim_history(self._input_history, 60)
        self._trim_history(self._output_history, 60)
        input_last_minute = sum(toks for (_t, toks) in self._input_history)
        output_last_minute = sum(toks for (_t, toks) in self._output_history)
        return {
            "calls_made": self.calls_made,
            "delays_required": self.delays_required,
            "total_delay_time": round(self.total_delay_time, 3),
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "input_tokens_last_minute": input_last_minute,
            "output_tokens_last_minute": output_last_minute,
            "extended_output_enabled": self.extended_output,
            "input_rate_limit": self.input_rate_limit,
            "output_token_threshold": self.output_token_threshold
        }

# Create a singleton instance for convenient use across the application
token_manager = TokenManager()

