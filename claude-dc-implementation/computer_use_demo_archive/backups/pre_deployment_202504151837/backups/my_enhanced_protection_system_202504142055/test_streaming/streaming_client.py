"""
Enhanced Streaming Client Module

Provides robust streaming support for API operations with large token sizes.
Specifically optimized for long-running operations (>10 minutes).
Tightly integrated with token management and safe file operations for rate limiting.
"""

import os
import time
import random
import logging
import threading
import inspect
from typing import Dict, List, Tuple, Optional, Callable, Any, Iterator, Union
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
    from token_management.token_manager import token_manager
    has_token_manager = True
    logger.info("Token manager found and imported")
except ImportError:
    has_token_manager = False
    logger.warning("Token manager not found, proceeding without token management")

# Import safe file operations if available
try:
    from safe_ops.safe_file_operations import safe_file_ops
    has_safe_ops = True
    logger.info("Safe file operations found and imported")
except ImportError:
    has_safe_ops = False
    logger.warning("Safe file operations not found, proceeding without safe file operations")

class StreamProgressTracker:
    """Track progress of streaming operations"""
    
    def __init__(self, estimated_total_tokens=None):
        """Initialize progress tracker
        
        Args:
            estimated_total_tokens: Estimated total tokens for the operation (optional)
        """
        self.start_time = time.time()
        self.tokens_received = 0
        self.chars_received = 0
        self.estimated_total = estimated_total_tokens
        self.last_update_time = self.start_time
        self.update_interval = 5  # seconds
        
    def update(self, new_content):
        """Update progress with newly received content
        
        Args:
            new_content: New content received from stream
        """
        # Roughly estimate tokens (4 chars per token is a rough approximation)
        new_chars = len(new_content)
        new_tokens = max(1, new_chars // 4)
        
        self.chars_received += new_chars
        self.tokens_received += new_tokens
        current_time = time.time()
        
        # Only log updates at certain intervals to avoid spam
        if current_time - self.last_update_time >= self.update_interval:
            elapsed = current_time - self.start_time
            tokens_per_second = self.tokens_received / elapsed if elapsed > 0 else 0
            
            if self.estimated_total:
                percent_complete = (self.tokens_received / self.estimated_total) * 100
                logger.info(f"Stream progress: {self.tokens_received}/{self.estimated_total} tokens "
                           f"({percent_complete:.1f}%) at {tokens_per_second:.1f} tokens/sec")
            else:
                logger.info(f"Stream progress: {self.tokens_received} tokens received "
                           f"at {tokens_per_second:.1f} tokens/sec")
            
            self.last_update_time = current_time
            
            # For very long operations, check if we need to log duration
            if elapsed > 60*5:  # 5 minutes
                minutes = elapsed // 60
                seconds = elapsed % 60
                logger.info(f"Long-running stream: {minutes:.0f}m {seconds:.0f}s elapsed")
        
        return new_tokens

class StreamingClient:
    """Enhanced client for handling streaming API calls with robust error handling"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the streaming client
        
        Args:
            api_key: API key for Anthropic (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        
        # Configure retry settings
        self.max_retries = 3
        self.base_retry_delay = 1.0
        
        # Track last token usage for reporting
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        
        # Check if this version of Anthropic SDK supports betas parameter
        # Inspect the create message method to see if it supports betas
        self.supports_betas = False
        try:
            sig = inspect.signature(self.client.messages.create)
            self.supports_betas = 'betas' in sig.parameters
        except (AttributeError, TypeError):
            pass
        
        logger.info(f"Enhanced StreamingClient initialized with Anthropic SDK version {anthropic_version}")
        logger.info(f"Betas support: {self.supports_betas}")
    
    def calculate_streaming_requirement(self, max_tokens: int, thinking_budget: Optional[int] = None) -> bool:
        """
        Determine if streaming is required based on token sizes
        ALWAYS uses streaming for operations exceeding 4096 tokens
        
        Args:
            max_tokens: Maximum tokens for the response
            thinking_budget: Thinking budget (if any)
            
        Returns:
            True if streaming is required, False otherwise
        """
        # ALWAYS use streaming for operations exceeding 4096 tokens
        # This is a lower threshold than before to ensure streaming for medium-large operations
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
    
    def check_token_limits(self, estimated_input_tokens: int, estimated_output_tokens: int) -> bool:
        """
        Check token limits and ensure we have capacity for operation
        
        Args:
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            True if operation can proceed, False if capacity is insufficient
        """
        if not has_token_manager:
            return True
            
        # Get current token usage
        input_tokens_per_minute = token_manager.input_tokens_per_minute
        input_limit = token_manager.org_input_limit
        
        # Calculate available capacity
        available_capacity = input_limit - input_tokens_per_minute
        
        # If estimated tokens would exceed capacity, we need to delay
        if estimated_input_tokens > available_capacity * 0.9:  # 90% of available capacity
            logger.warning(f"Operation requires {estimated_input_tokens} tokens but only {available_capacity} available")
            token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
            return self.check_token_limits(estimated_input_tokens, estimated_output_tokens)
        
        return True
    
    def delay_if_needed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> None:
        """
        Delay if needed to avoid rate limits
        
        Args:
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
        """
        if has_token_manager:
            # Check token limits to ensure we have capacity
            self.check_token_limits(estimated_input_tokens, estimated_output_tokens)
            # Also use token_manager's delay mechanism
            token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
    
    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """
        Process response headers to update token usage
        
        Args:
            headers: Response headers from API call
        """
        if has_token_manager:
            token_manager.process_response_headers(headers)
        
        # Helper function to safely extract integers from headers
        def get_header_int(key: str, default: int = 0) -> int:
            try:
                return int(headers.get(key, default))
            except (ValueError, TypeError):
                return default
        
        # Store last token usage for reporting
        self.last_input_tokens = get_header_int('anthropic-input-tokens', 0)
        self.last_output_tokens = get_header_int('anthropic-output-tokens', 0)
    
    def retry_with_exponential_backoff(self, operation_func, max_retries=None, base_delay=None):
        """
        Execute an operation with exponential backoff retries
        
        Args:
            operation_func: Function to execute
            max_retries: Maximum number of retries
            base_delay: Base delay for exponential backoff
            
        Returns:
            Result of the operation
        """
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_retry_delay
        retries = 0
        last_exception = None
        
        while True:
            try:
                return operation_func()
            except Exception as e:
                last_exception = e
                retries += 1
                if retries > max_retries:
                    logger.error(f"Failed after {retries} retries: {e}")
                    raise last_exception
                
                # Calculate delay with jitter (randomization)
                delay = base_delay * (2 ** (retries - 1)) * (0.5 + random.random())
                logger.warning(f"Retry {retries}/{max_retries} after error: {e}. Waiting {delay:.2f}s")
                print(f"⚠️ Connection error - retrying in {delay:.2f}s ({retries}/{max_retries})")
                time.sleep(delay)
    
    def maintain_stream_connection(self, stream_object, heartbeat_interval=60):
        """
        Maintain stream connection during long-running operations
        
        Args:
            stream_object: Stream object to maintain
            heartbeat_interval: Interval in seconds for heartbeat
            
        Returns:
            Thread handling the heartbeat
        """
        last_activity = time.time()
        
        def heartbeat_thread():
            nonlocal last_activity
            while not getattr(stream_object, '_closed', True):
                time_since_activity = time.time() - last_activity
                if time_since_activity > heartbeat_interval:
                    # Send heartbeat ping or no-op to keep connection alive
                    try:
                        # Implementation depends on specific stream type
                        # For most HTTP streaming connections, we can't send heartbeats
                        # but we can monitor and reconnect if needed
                        logger.debug(f"Monitoring stream connection: {time_since_activity:.2f}s since last activity")
                    except Exception as e:
                        logger.error(f"Heartbeat monitoring error: {e}")
                
                # Sleep for a shorter interval to be responsive
                time.sleep(min(10, heartbeat_interval / 3))
        
        thread = threading.Thread(target=heartbeat_thread, daemon=True)
        thread.start()
        return thread
    
    def process_streaming_chunk(self, chunk):
        """
        Process a streaming chunk and extract content
        
        Args:
            chunk: Chunk from streaming response
            
        Returns:
            Extracted content or None
        """
        # Extract content based on chunk type
        content = None
        chunk_type = type(chunk).__name__
        
        try:
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
            
            # Log chunk type if we couldn't extract content
            if content is None:
                logger.debug(f"Unknown chunk type: {chunk_type}, attributes: {dir(chunk)}")
        except Exception as e:
            logger.error(f"Error processing chunk of type {chunk_type}: {e}")
        
        return content
    
    def handle_streaming_response(self, response, stream_callback=None, estimated_total_tokens=None):
        """
        Handle streaming response with progress tracking and error recovery
        
        Args:
            response: Streaming response object
            stream_callback: Callback for streaming chunks
            estimated_total_tokens: Estimated total tokens (for progress tracking)
            
        Returns:
            Full content from streaming response
        """
        # Initialize progress tracker
        progress = StreamProgressTracker(estimated_total_tokens)
        
        # Set up connection monitoring for long-running operations
        monitor_thread = self.maintain_stream_connection(response)
        
        # Process streaming response
        full_content = ""
        last_exception = None
        retry_count = 0
        max_retries = self.max_retries
        
        try:
            # Wrap the streaming in a retry handler
            def process_stream():
                nonlocal full_content
                try:
                    for chunk in response:
                        # Process the chunk
                        content = self.process_streaming_chunk(chunk)
                        
                        # Update if we got content
                        if content:
                            full_content += content
                            progress.update(content)
                            
                            # Call stream callback if provided
                            if stream_callback:
                                stream_callback(content)
                    return True
                except Exception as e:
                    logger.error(f"Stream processing error: {e}")
                    # Save the exception for retrying
                    nonlocal last_exception
                    last_exception = e
                    return False
            
            # Use retry for the streaming process
            success = process_stream()
            
            # If streaming failed, attempt to retry from where we left off
            while not success and retry_count < max_retries:
                retry_count += 1
                delay = self.base_retry_delay * (2 ** retry_count) * (0.5 + random.random())
                
                logger.warning(f"Stream interrupted. Retrying ({retry_count}/{max_retries}) after {delay:.2f}s delay")
                print(f"⚠️ Stream interrupted. Retrying in {delay:.2f}s ({retry_count}/{max_retries})")
                time.sleep(delay)
                
                # TODO: In a real implementation, we would attempt to resume the stream
                # from where it left off. This requires API support for streaming resumption.
                # For now, we'll just log the error and continue with what we have.
                if retry_count >= max_retries:
                    logger.error(f"Failed to complete stream after {max_retries} retries")
                    print(f"⚠️ Failed to complete stream after {max_retries} retries")
                    break
                
                success = process_stream()
        
        except Exception as e:
            logger.error(f"Error in stream handler: {e}")
            print(f"⚠️ Stream error: {e}")
        finally:
            # Clean up monitoring thread
            if monitor_thread:
                monitor_thread.join(timeout=1.0)
        
        # If we have partial content but hit max retries, still return what we have
        if full_content and last_exception and retry_count >= max_retries:
            logger.warning(f"Returning partial content ({len(full_content)} chars) after max retries")
            print(f"⚠️ Returning partial content after max retries")
        
        return full_content
    
    def create_message(self, 
                      messages: List[Dict[str, str]],
                      model: str = "claude-3-7-sonnet-20250219",
                      system: Optional[Union[Dict[str, str], str]] = None,
                      max_tokens: Optional[int] = None,
                      thinking_budget: Optional[int] = None,
                      temperature: float = 1.0,
                      stream_callback: Optional[Callable[[str], None]] = None,
                      beta_headers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a message with robust streaming support and token management
        
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
            
        # Ensure thinking_budget is less than max_tokens and at least 1024 to avoid API error
        if thinking_budget is not None:
            if thinking_budget >= max_tokens:
                thinking_budget = max(1024, max_tokens - 100)  # Ensure at least 100 tokens for output
                logger.warning(f"Reduced thinking budget to {thinking_budget} to be less than max_tokens={max_tokens}")
            elif thinking_budget > 0 and thinking_budget < 1024:
                # The API requires at least 1024 tokens for thinking budget if enabled
                thinking_budget = 1024
                logger.warning(f"Increased thinking budget to minimum required value of 1024")
        
        # Determine if streaming is required - ALWAYS for large operations
        use_streaming = self.calculate_streaming_requirement(max_tokens, thinking_budget)
        
        # Enforce streaming for large operations regardless of user preference
        if max_tokens > 4096 or (thinking_budget is not None and thinking_budget > 4096):
            use_streaming = True
            logger.info("Enforcing streaming for large token operation")
        
        # Prepare beta headers for extended output
        if beta_headers is None:
            beta_headers = ["output-128k-2025-02-19"]
        
        # Estimate input tokens (more accurate than before)
        estimated_input_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            # Use tiktoken if available through safe_file_ops
            if has_safe_ops:
                estimated_input_tokens += safe_file_ops.estimate_tokens(content)
            else:
                # Fallback to rough approximation
                estimated_input_tokens += len(content) // 4
        
        # If system is provided, estimate its tokens too
        if system:
            system_text = system.get("text", "") if isinstance(system, dict) else system
            if has_safe_ops:
                estimated_input_tokens += safe_file_ops.estimate_tokens(system_text)
            else:
                estimated_input_tokens += len(system_text) // 4
        
        # Add some buffer to the estimate
        estimated_input_tokens = int(estimated_input_tokens * 1.1)  # 10% buffer
        
        # Estimate output tokens (use max_tokens as upper bound)
        estimated_output_tokens = max_tokens
        
        # Check token limits and delay if needed
        self.check_token_limits(estimated_input_tokens, estimated_output_tokens)
        self.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
        
        logger.info(f"Creating message with streaming={use_streaming}, max_tokens={max_tokens}, "
                  f"estimated_input={estimated_input_tokens}")
        
        # Define the operation function for retry mechanism
        def api_operation():
            if use_streaming:
                logger.info("Using streaming for large token operation")
                
                # Set up thinking if thinking budget is provided
                thinking = None
                if max_tokens >= 2048 and thinking_budget is not None and thinking_budget >= 1024:
                    thinking = {"type": "enabled", "budget_tokens": thinking_budget}
                
                # Prepare common parameters
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                }
                
                # Add system if provided (format correctly based on type)
                if system is not None:
                    kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                
                # Add thinking if provided
                if thinking is not None:
                    kwargs["thinking"] = thinking
                
                # Add beta headers if supported
                if self.supports_betas:
                    kwargs["betas"] = beta_headers
                
                # Make streaming API call
                response = self.client.messages.create(**kwargs)
                
                # Process streaming response with robust handling
                full_content = self.handle_streaming_response(
                    response, 
                    stream_callback=stream_callback,
                    estimated_total_tokens=max_tokens
                )
                
                # Create mock headers for token tracking
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
                if max_tokens >= 2048 and thinking_budget is not None and thinking_budget >= 1024:
                    thinking = {"type": "enabled", "budget_tokens": thinking_budget}
                
                # Prepare common parameters
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                # Add system if provided (format correctly based on type)
                if system is not None:
                    kwargs["system"] = system.get("text", "") if isinstance(system, dict) else system
                
                # Add thinking if provided
                if thinking is not None:
                    kwargs["thinking"] = thinking
                
                # Add beta headers if supported
                if self.supports_betas:
                    kwargs["betas"] = beta_headers
                
                # Make API call
                response = self.client.messages.create(**kwargs)
                
                # Extract token usage from response headers if available
                headers = getattr(response, 'headers', {})
                if headers:
                    self.process_response_headers(headers)
                else:
                    # Create mock headers for token tracking
                    mock_headers = {
                        'anthropic-input-tokens': str(estimated_input_tokens),
                        'anthropic-output-tokens': str(estimated_output_tokens // 2)  # Conservative estimate
                    }
                    self.process_response_headers(mock_headers)
                
                return response
        
        # Use retry mechanism for the operation
        try:
            return self.retry_with_exponential_backoff(api_operation)
        except Exception as e:
            logger.error(f"Error creating message after all retries: {e}")
            # Return an error response
            return {
                "content": [{"type": "text", "text": f"Error after {self.max_retries} retries: {str(e)}"}],
                "model": model,
                "role": "assistant"
            }
    
    def get_completion(self, prompt, max_tokens=100):
        """Convenience method for getting text completions"""
        # Create a simple message with the prompt
        messages = [{"role": "user", "content": prompt}]
        
        # Make the API call
        response = self.create_message(
            messages=messages,
            max_tokens=max_tokens
        )
        
        # Extract text content
        if isinstance(response, dict) and "content" in response:
            content = response["content"]
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    return content[0]["text"]
        
        # Try other possible formats
        if hasattr(response, "content") and len(response.content) > 0:
            if hasattr(response.content[0], "text"):
                return response.content[0].text
        
        # Return error message if extraction failed
        return "Error: Could not extract text from response"
        
    @property
    def last_token_usage(self):
        """Get the last token usage"""
        if has_token_manager:
            # Get the most recent values
            return {
                "input": token_manager.input_tokens_per_minute,
                "output": token_manager.output_tokens_per_minute
            }
        else:
            return {
                "input": self.last_input_tokens,
                "output": self.last_output_tokens
            }

# Create singleton instance
streaming_client = StreamingClient()