"""
Streaming Client Module

Provides streaming support for API operations with large token sizes.
Integrates with token management for rate limiting.
"""

import os
import time
import logging
import inspect
from typing import Dict, List, Tuple, Optional, Callable, Any, Iterator
from anthropic import Anthropic
from anthropic import __version__ as anthropic_version

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/streaming_client.log'
)
logger = logging.getLogger("streaming_client")

# Import token manager if available
try:
    import sys
    sys.path.append('/home/computeruse/computer_use_demo')
    from token_management import token_manager
    has_token_manager = True
    logger.info("Token manager found and imported")
except ImportError:
    has_token_manager = False
    logger.warning("Token manager not found, proceeding without token management")

class StreamingClient:
    """
    Client for handling streaming API calls with token management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the streaming client
        
        Args:
            api_key: API key for Anthropic (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        
        # Check if this version of Anthropic SDK supports betas parameter
        # Inspect the create message method to see if it supports betas
        self.supports_betas = False
        try:
            sig = inspect.signature(self.client.messages.create)
            self.supports_betas = 'betas' in sig.parameters
        except (AttributeError, TypeError):
            pass
        
        logger.info(f"StreamingClient initialized with Anthropic SDK version {anthropic_version}")
        logger.info(f"Betas support: {self.supports_betas}")
    
    def calculate_streaming_requirement(self, max_tokens: int, thinking_budget: Optional[int] = None) -> bool:
        """
        Determine if streaming is required based on token sizes
        
        Args:
            max_tokens: Maximum tokens for the response
            thinking_budget: Thinking budget (if any)
            
        Returns:
            True if streaming is required, False otherwise
        """
        # Streaming is required for operations with max_tokens > 21,333
        # But we'll enable it for operations with max_tokens > 4096 for efficiency
        return max_tokens > 4096 or (thinking_budget is not None and thinking_budget > 4096)
    
    def get_safe_token_limits(self) -> Dict[str, int]:
        """
        Get safe token limits from token manager or use defaults
        
        Returns:
            Dictionary with max_tokens and thinking_budget
        """
        if has_token_manager:
            return token_manager.get_safe_limits()
        else:
            # Default safe limits
            return {
                "max_tokens": 20000,
                "thinking_budget": 4000
            }
    
    def delay_if_needed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> None:
        """
        Delay if needed to avoid rate limits
        
        Args:
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
        """
        if has_token_manager:
            token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
    
    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """
        Process response headers to update token usage
        
        Args:
            headers: Response headers from API call
        """
        if has_token_manager:
            token_manager.process_response_headers(headers)
    
    def create_message(self, 
                      messages: List[Dict[str, str]],
                      model: str = "claude-3-7-sonnet-20250219",
                      system: Optional[Dict[str, str]] = None,
                      max_tokens: Optional[int] = None,
                      thinking_budget: Optional[int] = None,
                      temperature: float = 1.0,
                      stream_callback: Optional[Callable[[str], None]] = None,
                      beta_headers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a message with streaming support and token management
        
        Args:
            messages: List of message objects
            model: Model to use
            system: System message
            max_tokens: Maximum tokens in response
            thinking_budget: Thinking budget
            temperature: Temperature for sampling
            stream_callback: Callback for streaming chunks
            beta_headers: Beta headers to include
            
        Returns:
            Response object or aggregated content from streaming response
        """
        # Get safe token limits if not specified
        if max_tokens is None or thinking_budget is None:
            limits = self.get_safe_token_limits()
            max_tokens = max_tokens or limits["max_tokens"]
            thinking_budget = thinking_budget or limits["thinking_budget"]
            
        # Ensure thinking_budget is less than max_tokens to avoid API error
        if thinking_budget is not None and thinking_budget >= max_tokens:
            thinking_budget = max(0, max_tokens - 100)  # Ensure at least 100 tokens for output
            logger.warning(f"Reduced thinking budget to {thinking_budget} to be less than max_tokens={max_tokens}")
        
        # Determine if streaming is required
        use_streaming = self.calculate_streaming_requirement(max_tokens, thinking_budget)
        
        # Prepare beta headers
        if beta_headers is None:
            beta_headers = ["output-128k-2025-02-19"]
        
        # Estimate input tokens (rough approximation)
        estimated_input_tokens = sum(len(msg.get("content", "")) // 4 for msg in messages)
        if system and "text" in system:
            estimated_input_tokens += len(system["text"]) // 4
        
        # Estimate output tokens (use max_tokens as upper bound)
        estimated_output_tokens = max_tokens
        
        # Check if delay needed
        self.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
        
        logger.info(f"Creating message with streaming={use_streaming}, max_tokens={max_tokens}")
        
        try:
            if use_streaming:
                logger.info("Using streaming for large token operation")
                
                # Set up thinking if thinking budget is provided
                thinking = None
                if thinking_budget is not None and thinking_budget > 0:
                    thinking = {"type": "enabled", "budget_tokens": thinking_budget}
                
                # Make streaming API call
                if self.supports_betas:
                    # Newer version with betas parameter
                    # Format system parameter correctly
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": True,
                        "betas": beta_headers
                    }
                    
                    # Add system and thinking if provided
                    if system is not None:
                        kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                    
                    if thinking is not None:
                        kwargs["thinking"] = thinking
                    
                    response = self.client.messages.create(**kwargs)
                else:
                    # Older version without betas parameter
                    # Format system parameter correctly
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": True
                    }
                    
                    # Add system and thinking if provided
                    if system is not None:
                        kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                    
                    if thinking is not None:
                        kwargs["thinking"] = thinking
                    
                    response = self.client.messages.create(**kwargs)
                
                # Process streaming response
                full_content = ""
                try:
                    for chunk in response:
                        # Log the chunk type to debug
                        chunk_type = type(chunk).__name__
                        logger.debug(f"Received chunk of type {chunk_type}")
                        
                        # Extract content based on chunk type
                        content = None
                        
                        # Check for different types of chunks based on Anthropic API version
                        if hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                            # New-style chunks (Anthropic API v0.4+)
                            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                                content = chunk.delta.text
                        elif hasattr(chunk, 'completion'):
                            # Old-style chunks (before content blocks)
                            content = chunk.completion
                        elif hasattr(chunk, 'delta'):
                            # Another variant of chunks
                            if hasattr(chunk.delta, 'text'):
                                content = chunk.delta.text
                        elif hasattr(chunk, 'text'):
                            # Direct text chunk
                            content = chunk.text
                        
                        # Process content if extracted
                        if content:
                            full_content += content
                            # Call stream callback if provided
                            if stream_callback:
                                stream_callback(content)
                except Exception as e:
                    logger.error(f"Error processing stream: {e}")
                
                # Mock headers for token tracking
                mock_headers = {
                    'anthropic-input-tokens': str(estimated_input_tokens),
                    'anthropic-output-tokens': str(len(full_content) // 4)  # Rough approximation
                }
                self.process_response_headers(mock_headers)
                
                # Return object similar to non-streaming response
                return {
                    "content": [{"type": "text", "text": full_content}],
                    "model": model,
                    "role": "assistant"
                }
            else:
                # Non-streaming API call
                logger.info("Using non-streaming for small token operation")
                
                # Set up thinking if thinking budget is provided
                thinking = None
                if thinking_budget is not None and thinking_budget > 0:
                    thinking = {"type": "enabled", "budget_tokens": thinking_budget}
                
                # Make API call
                if self.supports_betas:
                    # Newer version with betas parameter
                    # Format system parameter correctly
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False,
                        "betas": beta_headers
                    }
                    
                    # Add system and thinking if provided
                    if system is not None:
                        kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                    
                    if thinking is not None:
                        kwargs["thinking"] = thinking
                    
                    response = self.client.messages.create(**kwargs)
                else:
                    # Older version without betas parameter
                    # Format system parameter correctly
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    }
                    
                    # Add system and thinking if provided
                    if system is not None:
                        kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                    
                    if thinking is not None:
                        kwargs["thinking"] = thinking
                    
                    response = self.client.messages.create(**kwargs)
                
                # Handle response format differences between API versions
                output_text = ""
                try:
                    if hasattr(response, 'content') and len(response.content) > 0:
                        if hasattr(response.content[0], 'text'):
                            output_text = response.content[0].text
                    elif hasattr(response, 'completion'):
                        output_text = response.completion
                    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                        if len(response.message.content) > 0 and hasattr(response.message.content[0], 'text'):
                            output_text = response.message.content[0].text
                except (AttributeError, IndexError) as e:
                    logger.warning(f"Couldn't extract response text: {e}")
                
                # Mock headers for token tracking
                mock_headers = {
                    'anthropic-input-tokens': str(estimated_input_tokens),
                    'anthropic-output-tokens': str(len(output_text) // 4)  # Rough approximation
                }
                self.process_response_headers(mock_headers)
                
                return response
                
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            # Return an error response
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "model": model,
                "role": "assistant"
            }

# Create singleton instance
streaming_client = StreamingClient()