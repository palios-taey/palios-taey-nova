"""
Adaptive Anthropic client that automatically chooses streaming for large outputs.
"""

import logging
from typing import Any, Dict, List, Optional, Union
import time

from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/adaptive_client.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('adaptive_client')

class AdaptiveAnthropicClient:
    """
    Client that wraps the Anthropic SDK client and automatically uses 
    streaming for requests with large max_tokens to prevent timeouts.
    """
    
    def __init__(self, api_key: str, base_client=None, streaming_threshold: int = 21333):
        """
        Initialize the adaptive client.
        
        Args:
            api_key: Anthropic API key
            base_client: Optional pre-configured Anthropic client
            streaming_threshold: Max token count above which to use streaming
        """
        self.api_key = api_key
        self.client = base_client or Anthropic(api_key=api_key)
        self.streaming_threshold = streaming_threshold
        logger.info(f"AdaptiveAnthropicClient initialized with streaming threshold of {streaming_threshold} tokens")
        
        # Expose client attributes
        self.beta = AdaptiveBetaClient(self)
    
    def messages(self, *args, **kwargs):
        """Pass through to client.messages for compatibility."""
        return self.client.messages(*args, **kwargs)

class AdaptiveBetaClient:
    """Adapter for beta endpoints."""
    
    def __init__(self, parent):
        self.parent = parent
        self.messages = AdaptiveMessagesClient(parent)

class AdaptiveMessagesClient:
    """Adapter for messages endpoints with streaming intelligence."""
    
    def __init__(self, parent):
        self.parent = parent
        
    def create(self, *args, **kwargs):
        """
        Create a message, automatically using streaming for large outputs.
        """
        # Check if max_tokens exceeds threshold
        max_tokens = kwargs.get('max_tokens', 4096)
        stream = kwargs.get('stream', None)
        
        # If stream is explicitly set, respect that setting
        if stream is not None:
            logger.info(f"Using explicit stream={stream} setting")
            return self.parent.client.beta.messages.create(*args, **kwargs)
        
        # Otherwise, decide based on max_tokens
        if max_tokens > self.parent.streaming_threshold:
            logger.info(f"max_tokens ({max_tokens}) exceeds threshold ({self.parent.streaming_threshold}), enabling streaming")
            kwargs['stream'] = True
            return self._handle_streaming_request(*args, **kwargs)
        else:
            logger.info(f"max_tokens ({max_tokens}) below threshold, using non-streaming request")
            return self.parent.client.beta.messages.create(*args, **kwargs)
    
    def _handle_streaming_request(self, *args, **kwargs):
        """
        Handle a streaming request, collecting all content into a final response.
        """
        # Call the API with streaming enabled
        start_time = time.time()
        logger.info("Starting streaming request")
        
        stream = self.parent.client.beta.messages.create(*args, **kwargs)
        
        # Initialize storage for content blocks
        content_blocks = []
        current_block = None
        completion_text = ""
        
        # Process the stream
        try:
            for chunk in stream:
                # Handle different chunk types
                if chunk.type == "content_block_start":
                    # Start a new content block
                    current_block = {
                        "type": chunk.content_block.type,
                        "text": ""
                    }
                
                elif chunk.type == "content_block_delta":
                    # Add to the current content block
                    if current_block is not None:
                        current_block["text"] += chunk.delta.text
                    
                    # Also build the full completion text
                    completion_text += chunk.delta.text
                
                elif chunk.type == "content_block_stop":
                    # Finalize the current block and add to list
                    if current_block is not None:
                        content_blocks.append(current_block)
                        current_block = None
                
                elif chunk.type == "message_stop":
                    # Message is complete
                    pass
                
                # Could handle other types like 'error' here if needed
            
            # Calculate duration
            duration = time.time() - start_time
            logger.info(f"Streaming request completed in {duration:.2f}s")
            
            # Create a synthetic response object similar to non-streaming response
            response = {
                "id": "msg_streaming_synthetic",
                "type": "message",
                "role": "assistant",
                "content": content_blocks,
                "model": kwargs.get("model", "unknown"),
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 0,  # We don't know exact count
                    "output_tokens": len(completion_text) // 4  # Rough estimate
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")
            # Re-raise the exception
            raise

    with_raw_response = None  # Will be set up after client is created

def create_adaptive_client(api_key: Optional[str] = None, base_client=None):
    """Create and initialize the adaptive client."""
    client = AdaptiveAnthropicClient(api_key=api_key, base_client=base_client)
    
    # Set up with_raw_response attribute - not implemented in this basic version
    # In a full implementation, this would handle raw response objects similarly
    client.beta.messages.with_raw_response = None
    
    return client
