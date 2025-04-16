"""
Universal token manager for Claude DC that handles rate limits.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/token_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('token_manager')

class TokenManager:
    """Manages token rate limits to prevent 429 errors."""
    
    def __init__(self):
        self.org_input_limit = 40000  # 40K input tokens per minute default
        self.org_output_limit = 8000  # 8K output tokens per minute default
        self.org_req_limit = 1000    # 1000 requests per minute default
        
        # Current usage tracking
        self.input_tokens_used = 0
        self.output_tokens_used = 0 
        self.req_count = 0
        
        # Reset times
        self.input_reset_time = None
        self.output_reset_time = None
        self.req_reset_time = None
        
        # Safety buffer - only use 80% of the limit by default
        self.buffer_percent = 0.6
        
        # Fibonacci backoff for rate limit approach
        self.backoff_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        self.backoff_index = 0
        
        # Minimum delay between operations
        self.min_delay = 0.1  # seconds
        
        logger.info("TokenManager initialized with %d ITPM, %d OTPM limits", 
                   self.org_input_limit, self.org_output_limit)
    
    def _parse_reset_time(self, reset_time_str: str) -> datetime:
        """Parse ISO format reset time from API headers."""
        try:
            return datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Error parsing reset time '{reset_time_str}': {e}")
            # Default to 60 seconds from now if parsing fails
            return datetime.now(timezone.utc) + timedelta(seconds=60)
    
    def _calculate_delay(self, reset_time: Optional[datetime], used_quota: float) -> float:
        """Calculate necessary delay based on quota used and reset time."""
        if reset_time is None:
            # Default to a proportional wait if we don't have a reset time
            if used_quota > self.buffer_percent:
                # Apply progressive backoff as we get closer to limits
                backoff_factor = self.backoff_sequence[min(self.backoff_index, len(self.backoff_sequence)-1)]
                delay = backoff_factor * (used_quota - self.buffer_percent) * 5  # Scale by how close to limit
                return max(delay, self.min_delay)
            return self.min_delay
            
        now = datetime.now(timezone.utc)
        if reset_time > now:
            time_to_reset = (reset_time - now).total_seconds()
            # If we're over buffer threshold, add delay proportional to usage
            if used_quota > self.buffer_percent:
                # Apply progressive backoff as we get closer to limits
                backoff_factor = self.backoff_sequence[min(self.backoff_index, len(self.backoff_sequence)-1)]
                # Scale delay by both time until reset and how much over buffer we are
                delay = time_to_reset * (used_quota - self.buffer_percent) * backoff_factor
                return max(delay, self.min_delay)
        
        # If reset time is in the past or we're under buffer, just add minimum delay
        return self.min_delay
    
    def manage_request(self, headers: Dict[str, str], 
                      input_tokens: int = 0, 
                      output_tokens: int = 0) -> float:
        """
        Process API response headers to track token usage and calculate necessary delays.
        Returns the delay needed (in seconds) before next request.
        """
        delay = 0.0
        
        # Update limits and usage from headers
        # Input tokens
        if 'anthropic-ratelimit-input-tokens-limit' in headers:
            self.org_input_limit = int(headers['anthropic-ratelimit-input-tokens-limit'])
        
        if 'anthropic-ratelimit-input-tokens-remaining' in headers:
            remaining = int(headers['anthropic-ratelimit-input-tokens-remaining']) 
            self.input_tokens_used = self.org_input_limit - remaining
            
        if 'anthropic-ratelimit-input-tokens-reset' in headers:
            self.input_reset_time = self._parse_reset_time(headers['anthropic-ratelimit-input-tokens-reset'])
        
        # Output tokens
        if 'anthropic-ratelimit-output-tokens-limit' in headers:
            self.org_output_limit = int(headers['anthropic-ratelimit-output-tokens-limit'])
            
        if 'anthropic-ratelimit-output-tokens-remaining' in headers:
            remaining = int(headers['anthropic-ratelimit-output-tokens-remaining'])
            self.output_tokens_used = self.org_output_limit - remaining
            
        if 'anthropic-ratelimit-output-tokens-reset' in headers:
            self.output_reset_time = self._parse_reset_time(headers['anthropic-ratelimit-output-tokens-reset'])
        
        # Request limits
        if 'anthropic-ratelimit-requests-limit' in headers:
            self.org_req_limit = int(headers['anthropic-ratelimit-requests-limit'])
            
        if 'anthropic-ratelimit-requests-remaining' in headers:
            remaining = int(headers['anthropic-ratelimit-requests-remaining'])
            self.req_count = self.org_req_limit - remaining
            
        if 'anthropic-ratelimit-requests-reset' in headers:
            self.req_reset_time = self._parse_reset_time(headers['anthropic-ratelimit-requests-reset'])
        
        # Calculate token usage percentages
        input_used_pct = self.input_tokens_used / self.org_input_limit if self.org_input_limit > 0 else 0
        output_used_pct = self.output_tokens_used / self.org_output_limit if self.org_output_limit > 0 else 0
        req_used_pct = self.req_count / self.org_req_limit if self.org_req_limit > 0 else 0
        
        # If we're over the buffer threshold, adjust backoff
        max_used_pct = max(input_used_pct, output_used_pct, req_used_pct)
        if max_used_pct > self.buffer_percent:
            # Increase backoff index as we get closer to limits
            self.backoff_index = min(self.backoff_index + 1, len(self.backoff_sequence) - 1)
        else:
            # Slowly reduce backoff when usage is low
            self.backoff_index = max(self.backoff_index - 1, 0)
        
        # Calculate delays based on each limit
        input_delay = self._calculate_delay(self.input_reset_time, input_used_pct)
        output_delay = self._calculate_delay(self.output_reset_time, output_used_pct)
        req_delay = self._calculate_delay(self.req_reset_time, req_used_pct)
        
        # Use the maximum delay
        delay = max(input_delay, output_delay, req_delay, self.min_delay)
        
        logger.info(f"Token usage: Input {self.input_tokens_used}/{self.org_input_limit} " 
                   f"({input_used_pct:.1%}), Output {self.output_tokens_used}/{self.org_output_limit} "
                   f"({output_used_pct:.1%}), Requests {self.req_count}/{self.org_req_limit} ({req_used_pct:.1%})")
        
        if delay > self.min_delay:
            logger.info(f"Rate limit approaching: Delaying next request by {delay:.2f}s "
                       f"(backoff_index={self.backoff_index})")
        
        # Add current operation to our counts
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens
        self.req_count += 1
        
        return delay
    
    def delay_if_needed(self, input_tokens: int = 0, output_tokens_est: Optional[int] = None) -> float:
        """
        Check if we need to delay before a new operation based on token estimates.
        
        Args:
            input_tokens: Estimated input tokens for the upcoming operation
            output_tokens_est: Estimated output tokens (default: 20% of input)
            
        Returns:
            The delay applied in seconds
        """
        # Default output tokens to 20% of input if not specified
        if output_tokens_est is None:
            output_tokens_est = int(input_tokens * 0.2)
        
        # Calculate what percent of limits this would use
        new_input_pct = (self.input_tokens_used + input_tokens) / self.org_input_limit
        new_output_pct = (self.output_tokens_used + output_tokens_est) / self.org_output_limit
        new_req_pct = (self.req_count + 1) / self.org_req_limit
        
        max_pct = max(new_input_pct, new_output_pct, new_req_pct)
        
        if max_pct > self.buffer_percent:
            # Calculate base delay - how long until we're below buffer threshold again
            delay = self._calculate_delay(
                self.input_reset_time if new_input_pct > self.buffer_percent else None,
                new_input_pct
            )
            
            if delay > 0:
                logger.info(f"Delaying operation with {input_tokens} input tokens, "
                           f"{output_tokens_est} est. output tokens for {delay:.2f}s "
                           f"(at {max_pct:.1%} of limit)")
                time.sleep(delay)
                return delay
        
        # Always add a small random delay to avoid request bunching
        min_delay = self.min_delay
        time.sleep(min_delay)
        return min_delay
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        if not text:
            return 0
        # Simple approximation: 1 token ≈ 4 characters
        # Use a slightly more conservative 3.5 chars per token for safety
        return max(1, int(len(text) / 3.5))
    
    def reset_counters(self):
        """Reset usage counters (useful for testing)."""
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        self.req_count = 0
        self.backoff_index = 0
        logger.info("Token usage counters reset")

# Singleton instance
token_manager = TokenManager()
