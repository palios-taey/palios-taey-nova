"""
Simple Token Management System for Anthropic API
-------------------------------------------------
Prevents rate limit errors by monitoring token usage and introducing strategic delays.
This version works with standard API limits before enabling beta features.
"""

import time
import datetime
import logging
from typing import Dict, Optional, Any

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/token_manager.log'
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manages API token usage to prevent rate limit errors"""
    
    def __init__(self, threshold_percent: float = 20.0):
        """
        Initialize the token manager
        
        Args:
            threshold_percent: Percentage of remaining tokens that triggers delays (default: 20%)
        """
        self.threshold_percent = threshold_percent
        self.fib_sequence = [1, 1, 2, 3, 5, 8, 13]  # Fibonacci sequence for backoff
        self.delay_count = 0
        self.last_check_time = datetime.datetime.now(datetime.timezone.utc)
        self.stats = {
            "calls_made": 0,
            "delays_required": 0,
            "total_delay_time": 0,
            "input_tokens_used": 0,
            "output_tokens_used": 0,
        }
        
        # Default token limits (pre-beta)
        self.default_settings = {
            "max_tokens": 4096,
            "input_token_limit": 100000,
            "output_token_limit": 100000,
            "total_token_limit": 100000,
        }
    
    def parse_reset_time(self, reset_time_str: str) -> datetime.datetime:
        """Parse the reset time from ISO 8601 format"""
        try:
            return datetime.datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing reset time: {e}, using fallback")
            # Fallback: assume 60 seconds from now
            return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60)
    
    def calculate_delay(self, reset_time: datetime.datetime) -> float:
        """Calculate seconds to delay until reset time"""
        now = datetime.datetime.now(datetime.timezone.utc)
        delay = (reset_time - now).total_seconds()
        return max(delay, 0)
    
    def check_token_limits(self, headers: Dict[str, str]) -> tuple[bool, float]:
        """
        Check token usage against thresholds and determine if a delay is needed
        
        Args:
            headers: The API response headers with rate limit info
            
        Returns:
            Tuple of (should_delay: bool, delay_time: float)
        """
        self.stats["calls_made"] += 1
        
        # Safely extract header values with defaults
        def get_header_int(key: str, default: int = 100000) -> int:
            try:
                return int(headers.get(key, default))
            except (ValueError, TypeError):
                return default
        
        # Extract remaining tokens and limits
        input_remaining = get_header_int('anthropic-ratelimit-input-tokens-remaining', 100000)
        output_remaining = get_header_int('anthropic-ratelimit-output-tokens-remaining', 100000)
        tokens_remaining = get_header_int('anthropic-ratelimit-tokens-remaining', 100000)
        
        input_limit = get_header_int('anthropic-ratelimit-input-tokens-limit', 100000)
        output_limit = get_header_int('anthropic-ratelimit-output-tokens-limit', 100000)
        tokens_limit = get_header_int('anthropic-ratelimit-tokens-limit', 100000)
        
        # Track token usage for overall statistics
        if 'anthropic-input-tokens' in headers and 'anthropic-output-tokens' in headers:
            input_used = get_header_int('anthropic-input-tokens', 0)
            output_used = get_header_int('anthropic-output-tokens', 0)
            self.stats["input_tokens_used"] += input_used
            self.stats["output_tokens_used"] += output_used
            
            # Log token usage
            logger.info(f"API call used {input_used} input tokens and {output_used} output tokens")
            logger.info(f"Total usage: {self.stats['input_tokens_used']} input, {self.stats['output_tokens_used']} output")
        
        # Extract reset times with safe defaults
        input_reset = self.parse_reset_time(headers.get('anthropic-ratelimit-input-tokens-reset', ''))
        output_reset = self.parse_reset_time(headers.get('anthropic-ratelimit-output-tokens-reset', ''))
        tokens_reset = self.parse_reset_time(headers.get('anthropic-ratelimit-tokens-reset', ''))
        
        # Define thresholds based on configured percentage
        input_threshold = (self.threshold_percent / 100.0) * input_limit
        output_threshold = (self.threshold_percent / 100.0) * output_limit
        tokens_threshold = (self.threshold_percent / 100.0) * tokens_limit
        
        # Log current token status
        logger.info(f"Token status - Input: {input_remaining}/{input_limit}, Output: {output_remaining}/{output_limit}, Total: {tokens_remaining}/{tokens_limit}")
        
        # Check if any token type is below its threshold
        if input_remaining < input_threshold:
            delay = self.calculate_delay(input_reset)
            logger.warning(f"Input tokens low ({input_remaining}/{input_limit}). Base delay: {delay:.2f} seconds.")
            return True, delay
            
        if output_remaining < output_threshold:
            delay = self.calculate_delay(output_reset)
            logger.warning(f"Output tokens low ({output_remaining}/{output_limit}). Base delay: {delay:.2f} seconds.")
            return True, delay
            
        if tokens_remaining < tokens_threshold:
            delay = self.calculate_delay(tokens_reset)
            logger.warning(f"Total tokens low ({tokens_remaining}/{tokens_limit}). Base delay: {delay:.2f} seconds.")
            return True, delay
            
        # If we got here, no delay needed
        self.delay_count = 0  # Reset delay count if no delay needed
        return False, 0
    
    def apply_backoff_strategy(self, base_delay: float) -> float:
        """Apply Fibonacci backoff to the base delay time"""
        # Use the appropriate Fibonacci number based on consecutive delays
        if self.delay_count < len(self.fib_sequence):
            multiplier = self.fib_sequence[self.delay_count]
            self.delay_count += 1
        else:
            # Cap at the last Fibonacci number to avoid excessive delays
            multiplier = self.fib_sequence[-1]
        
        # Calculate final delay (minimum 1 second)
        final_delay = max(base_delay * multiplier / 8, 1)
        logger.info(f"Applied Fibonacci backoff (level {self.delay_count}): {final_delay:.2f} seconds")
        return final_delay
    
    def manage_request(self, response_headers: Dict[str, str]) -> None:
        """
        Check limits and delay if necessary
        
        Args:
            response_headers: Headers from the API response
        """
        # Check if we need to delay
        should_delay, base_delay = self.check_token_limits(response_headers)
        
        if should_delay:
            # Calculate final delay with backoff strategy
            final_delay = self.apply_backoff_strategy(base_delay)
            
            # Update stats
            self.stats["delays_required"] += 1
            self.stats["total_delay_time"] += final_delay
            
            # Perform the delay
            logger.info(f"Delaying for {final_delay:.2f} seconds...")
            print(f"🕒 Token limit approaching - waiting for {final_delay:.2f} seconds to avoid rate limits...")
            time.sleep(final_delay)
            print("✅ Resuming operations after delay")
        
        # Log the current time after handling
        self.last_check_time = datetime.datetime.now(datetime.timezone.utc)
    
    def get_stats(self) -> Dict[str, Any]:
        """Return current usage statistics"""
        return {
            **self.stats,
            "average_delay": (
                self.stats["total_delay_time"] / self.stats["delays_required"] 
                if self.stats["delays_required"] > 0 else 0
            ),
            "delay_percentage": (
                100 * self.stats["delays_required"] / self.stats["calls_made"]
                if self.stats["calls_made"] > 0 else 0
            ),
        }
    
    def get_recommended_settings(self) -> Dict[str, int]:
        """
        Get recommended settings based on standard limits
            
        Returns:
            Dictionary with max_tokens and other recommended settings
        """
        return self.default_settings


# Global instance that can be imported
token_manager = TokenManager()
