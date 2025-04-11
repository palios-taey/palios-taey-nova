"""
Simple token management system with Fibonacci backoff for API rate limits.
"""

import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TokenManager:
    """
    Simple token manager that tracks token usage and introduces delays to prevent rate limits.
    Uses a Fibonacci backoff pattern for delays when approaching token limits.
    """
    
    def __init__(self):
        # Token tracking
        self.calls_made = 0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        
        # Budget settings
        self.max_budget = 1000000  # 1M token budget
        self.remaining_budget = self.max_budget
        self.warning_threshold = 0.2  # 20% of budget remaining
        
        # Delay tracking
        self.delays_required = 0
        self.total_delay_time = 0
        self.fibonacci_sequence = [1, 1, 2, 3, 5, 8, 13]  # Fibonacci sequence for backoff
        self.current_delay_index = 0
        
        # For statistics
        self.delay_percentage = 0
        self.average_delay = 0
        
        # Feature flags
        self.extended_output_beta = True
        
        # Last request timestamp
        self.last_request_time = None
        
        # Logger
        self.logger = logging.getLogger("TokenManager")
        self.logger.info("TokenManager initialized")
    
    def manage_request(self, response_headers):
        """
        Process an API response to track token usage and introduce delays if needed.
        
        Args:
            response_headers: Headers from the API response, containing token usage information
        """
        # Record current time
        current_time = datetime.now()
        
        # Track call
        self.calls_made += 1
        
        # Extract token usage from headers (implementation may vary based on API)
        input_tokens = int(response_headers.get("x-input-tokens", 0))
        output_tokens = int(response_headers.get("x-output-tokens", 0))
        
        # If no token information, use estimates
        if input_tokens == 0 and output_tokens == 0:
            self.logger.warning("No token usage information in headers, using estimates")
            input_tokens = 500  # Estimate
            output_tokens = 1000  # Estimate
        
        # Update token usage
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens
        self.remaining_budget -= (input_tokens + output_tokens)
        
        # Check if we need to apply a delay
        if self.remaining_budget / self.max_budget <= self.warning_threshold:
            delay_seconds = self._calculate_delay()
            self.delays_required += 1
            self.total_delay_time += delay_seconds
            
            self.logger.warning(
                f"🕒 Token limit approaching - waiting for {delay_seconds:.2f} seconds to avoid rate limits..."
            )
            
            # Apply delay
            time.sleep(delay_seconds)
            
            self.logger.info("✅ Resuming operations after delay")
        
        # Calculate statistics
        if self.delays_required > 0:
            self.average_delay = self.total_delay_time / self.delays_required
        
        if self.calls_made > 0:
            self.delay_percentage = (self.delays_required / self.calls_made) * 100
        
        # Track last request time
        self.last_request_time = current_time
        
        # Log status
        self.logger.info(
            f"Request processed: {input_tokens} input tokens, {output_tokens} output tokens, "
            f"{self.remaining_budget} budget remaining"
        )
    
    def _calculate_delay(self):
        """
        Calculate delay using Fibonacci backoff pattern.
        
        Returns:
            float: Delay in seconds
        """
        # Get current Fibonacci number
        current_fib = self.fibonacci_sequence[self.current_delay_index]
        
        # Calculate delay based on severity (lower budget = longer delay)
        budget_factor = max(0.1, min(1.5, 1.0 - (self.remaining_budget / self.max_budget)))
        delay = current_fib * budget_factor * 1.5
        
        # Move to next Fibonacci number, but don't exceed sequence length
        if self.current_delay_index < len(self.fibonacci_sequence) - 1:
            self.current_delay_index += 1
        
        return delay
    
    def reset(self):
        """Reset the token manager state."""
        self.__init__()
        self.logger.info("TokenManager reset")
    
    def get_heavy_task_settings(self):
        """
        Get settings for heavy tasks that require more tokens.
        
        Returns:
            dict: Settings for heavy tasks
        """
        if self.extended_output_beta:
            return {
                "max_tokens": 64000,
                "thinking_budget": 32000
            }
        else:
            return {
                "max_tokens": 4096,
                "thinking_budget": 2048
            }
    
    def get_statistics(self):
        """
        Get token usage statistics.
        
        Returns:
            dict: Token usage statistics
        """
        return {
            "calls_made": self.calls_made,
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "remaining_budget": self.remaining_budget,
            "delays_required": self.delays_required,
            "total_delay_time": self.total_delay_time,
            "average_delay": self.average_delay,
            "delay_percentage": self.delay_percentage,
            "extended_output_beta": self.extended_output_beta
        }

# Singleton instance
token_manager = TokenManager()
