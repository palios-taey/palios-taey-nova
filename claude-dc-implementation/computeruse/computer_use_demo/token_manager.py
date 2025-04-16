"""
Token manager for Claude DC that handles rate limits.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional

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
        
        # Current usage tracking
        self.input_tokens_used = 0
        self.output_tokens_used = 0 
        
        # Reset times
        self.input_reset_time = None
        self.output_reset_time = None
        
        # Safety buffer - only use 80% of the limit by default
        self.buffer_percent = 0.8
        
        logger.info("TokenManager initialized with %d ITPM, %d OTPM limits", 
                   self.org_input_limit, self.org_output_limit)
    
    def manage_request(self, headers: Dict[str, str], input_tokens: int = 0) -> None:
        """
        Process API response headers to track token usage.
        """
        # Update limits and usage from headers
        # Input tokens
        if 'anthropic-ratelimit-input-tokens-limit' in headers:
            self.org_input_limit = int(headers['anthropic-ratelimit-input-tokens-limit'])
        
        if 'anthropic-ratelimit-input-tokens-remaining' in headers:
            remaining = int(headers['anthropic-ratelimit-input-tokens-remaining']) 
            self.input_tokens_used = self.org_input_limit - remaining
            
        if 'anthropic-ratelimit-input-tokens-reset' in headers:
            try:
                reset_str = headers['anthropic-ratelimit-input-tokens-reset']
                self.input_reset_time = datetime.fromisoformat(reset_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Error parsing reset time: {e}")
        
        # Output tokens
        if 'anthropic-ratelimit-output-tokens-limit' in headers:
            self.org_output_limit = int(headers['anthropic-ratelimit-output-tokens-limit'])
            
        if 'anthropic-ratelimit-output-tokens-remaining' in headers:
            remaining = int(headers['anthropic-ratelimit-output-tokens-remaining'])
            self.output_tokens_used = self.org_output_limit - remaining
            
        if 'anthropic-ratelimit-output-tokens-reset' in headers:
            try:
                reset_str = headers['anthropic-ratelimit-output-tokens-reset']
                self.output_reset_time = datetime.fromisoformat(reset_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Error parsing reset time: {e}")
        
        # Add our current request to used counts
        self.input_tokens_used += input_tokens
        
        # Log current usage
        logger.info(f"Token usage: Input {self.input_tokens_used}/{self.org_input_limit} " 
                   f"({self.input_tokens_used/self.org_input_limit:.1%}), "
                   f"Output {self.output_tokens_used}/{self.org_output_limit} "
                   f"({self.output_tokens_used/self.org_output_limit:.1%})")
    
    def delay_if_needed(self, input_tokens: int) -> float:
        """
        Check if we need to delay before a new operation based on token estimates.
        Returns the delay applied in seconds.
        """
        # Check if this would put us over buffer threshold
        new_pct = (self.input_tokens_used + input_tokens) / self.org_input_limit
        
        if new_pct > self.buffer_percent and self.input_reset_time:
            now = datetime.now(timezone.utc)
            
            if self.input_reset_time > now:
                # Calculate delay needed
                time_to_reset = (self.input_reset_time - now).total_seconds()
                delay = time_to_reset * (new_pct - self.buffer_percent) * 2  # Scale by how much over buffer
                
                if delay > 0.1:  # Only delay if it's meaningful
                    logger.info(f"Delaying operation with {input_tokens} input tokens for {delay:.2f}s "
                               f"(at {new_pct:.1%} of limit)")
                    time.sleep(delay)
                    return delay
        
        return 0.0
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        if not text:
            return 0
        # Simple approximation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)

# Singleton instance
token_manager = TokenManager()
