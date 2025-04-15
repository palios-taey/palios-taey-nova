"""
Token Management Module

Provides comprehensive token usage tracking and rate limit management for API calls.
Implements sliding window approach for precise input token rate limiting.
"""

import time
import logging
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/token_manager.log'
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """
    Manages API token usage to prevent rate limit errors
    """
    
    def __init__(self):
        # Token tracking
        self.calls_made = 0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        
        # Input token rate limit tracking (40K per minute)
        self.input_token_timestamps = []  # List of (timestamp, token_count) tuples
        self.input_tokens_per_minute = 0
        self.org_input_limit = 40000  # Organization limit of 40K input tokens per minute
        self.input_token_warning_threshold = 0.8  # 80% of input limit
        
        # Output token rate limit (16K per minute)
        self.output_token_timestamps = []
        self.output_tokens_per_minute = 0
        self.org_output_limit = 16000
        
        # Budget tracking (1M token budget)
        self.token_budget = 1000000
        self.remaining_budget = self.token_budget
        
        # Settings for safe token usage
        self.safe_max_tokens = 20000  # Below 21,333 to avoid streaming validation error
        self.safe_thinking_budget = 4000
        
        # Beta flags
        self.extended_output_beta = True
        
        logger.info("Token manager initialized with sliding window approach for rate limiting")
    
    def check_input_rate_limit(self, input_tokens: int) -> Tuple[bool, float]:
        """
        Check if we're approaching the organization input token rate limit
        
        Args:
            input_tokens: Number of input tokens in the current request
            
        Returns:
            Tuple of (should_delay: bool, delay_time: float)
        """
        current_time = time.time()
        
        # Add this request to our sliding window
        self.input_token_timestamps.append((current_time, input_tokens))
        
        # Remove timestamps older than 1 minute
        one_minute_ago = current_time - 60
        self.input_token_timestamps = [
            (ts, tokens) for ts, tokens in self.input_token_timestamps 
            if ts >= one_minute_ago
        ]
        
        # Calculate current input tokens per minute
        self.input_tokens_per_minute = sum(tokens for _, tokens in self.input_token_timestamps)
        
        logger.info(f"Input tokens per minute: {self.input_tokens_per_minute}/{self.org_input_limit}")
        
        # Check if we're approaching the limit (80% of 40K = 32K)
        if self.input_tokens_per_minute >= self.org_input_limit * self.input_token_warning_threshold:
            # Calculate how long we need to wait for the oldest request to drop off
            if self.input_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.input_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                
                # Add a 1 second safety buffer
                delay = max(seconds_to_wait, 0) + 1
                
                logger.warning(f"Approaching input token rate limit - need to wait {delay:.2f} seconds")
                print(f"⚠️ Input token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        
        return False, 0
    
    def check_output_rate_limit(self, output_tokens: int) -> Tuple[bool, float]:
        """
        Check if we're approaching the organization output token rate limit
        
        Args:
            output_tokens: Number of output tokens in the current request
            
        Returns:
            Tuple of (should_delay: bool, delay_time: float)
        """
        current_time = time.time()
        
        # Add this request to our sliding window
        self.output_token_timestamps.append((current_time, output_tokens))
        
        # Remove timestamps older than 1 minute
        one_minute_ago = current_time - 60
        self.output_token_timestamps = [
            (ts, tokens) for ts, tokens in self.output_token_timestamps 
            if ts >= one_minute_ago
        ]
        
        # Calculate current output tokens per minute
        self.output_tokens_per_minute = sum(tokens for _, tokens in self.output_token_timestamps)
        
        logger.info(f"Output tokens per minute: {self.output_tokens_per_minute}/{self.org_output_limit}")
        
        # Check if we're approaching the limit (80% of 16K = 12.8K)
        if self.output_tokens_per_minute >= self.org_output_limit * 0.8:
            # Calculate how long we need to wait for the oldest request to drop off
            if self.output_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.output_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                
                # Add a 1 second safety buffer
                delay = max(seconds_to_wait, 0) + 1
                
                logger.warning(f"Approaching output token rate limit - need to wait {delay:.2f} seconds")
                print(f"\u26a0\ufe0f Output token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        
        return False, 0
    
    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """
        Process API response headers to track token usage
        
        Args:
            headers: Response headers from API call
        """
        self.calls_made += 1
        
        # Helper function to safely extract integers from headers
        def get_header_int(key: str, default: int = 0) -> int:
            try:
                return int(headers.get(key, default))
            except (ValueError, TypeError):
                return default
        
        # Extract token usage from headers
        input_tokens = get_header_int('anthropic-input-tokens')
        output_tokens = get_header_int('anthropic-output-tokens')
        
        # Update token usage
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens
        self.remaining_budget = self.token_budget - self.output_tokens_used
        
        # Log token usage
        logger.info(f"API call used {input_tokens} input tokens and {output_tokens} output tokens")
        logger.info(f"Total: {self.input_tokens_used} input, {self.output_tokens_used} output tokens")
        logger.info(f"Remaining budget: {self.remaining_budget} tokens")
        
        # Extract rate limit information
        input_remaining = get_header_int('anthropic-ratelimit-input-tokens-remaining')
        input_limit = get_header_int('anthropic-ratelimit-input-tokens-limit', 40000)
        output_remaining = get_header_int('anthropic-ratelimit-output-tokens-remaining')
        output_limit = get_header_int('anthropic-ratelimit-output-tokens-limit', 16000)
        
        logger.info(f"Input token status: {input_remaining}/{input_limit}")
        logger.info(f"Output token status: {output_remaining}/{output_limit}")
        
        # Update sliding window tracking
        self.check_input_rate_limit(input_tokens)
        self.check_output_rate_limit(output_tokens)
    
    def get_safe_limits(self) -> Dict[str, int]:
        """
        Get safe token limits that avoid streaming validation errors
        
        Returns:
            Dictionary with max_tokens and thinking_budget settings
        """
        return {
            "max_tokens": self.safe_max_tokens,
            "thinking_budget": self.safe_thinking_budget
        }
    
    def delay_if_needed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> None:
        """
        Check if a delay is needed before making a request and delay if necessary
        
        Args:
            estimated_input_tokens: Estimated input tokens for the upcoming request
            estimated_output_tokens: Estimated output tokens for the upcoming request
        """
        # Check input tokens first
        should_delay_input, delay_time_input = self.check_input_rate_limit(estimated_input_tokens)
        
        # Check output tokens
        should_delay_output, delay_time_output = self.check_output_rate_limit(estimated_output_tokens)
        
        # Use the longer delay if both are needed
        if should_delay_input or should_delay_output:
            delay_time = max(delay_time_input, delay_time_output)
            
            logger.info(f"Delaying for {delay_time:.2f} seconds to avoid rate limit")
            print(f"🕒 Delaying for {delay_time:.2f} seconds to avoid rate limit...")
            time.sleep(delay_time)
            print("✅ Resuming after delay")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return current usage statistics"""
        return {
            "calls_made": self.calls_made,
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "input_tokens_per_minute": self.input_tokens_per_minute,
            "output_tokens_per_minute": self.output_tokens_per_minute,
            "remaining_budget": self.remaining_budget,
            "extended_output_beta": self.extended_output_beta
        }

# Create a singleton instance
token_manager = TokenManager()