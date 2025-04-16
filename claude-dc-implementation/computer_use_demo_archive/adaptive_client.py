"""
Adaptive Anthropic client that automatically enables streaming for large outputs.
"""

import logging
import time
from typing import Any, Dict, List, Optional

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

def create_adaptive_client(api_key: Optional[str] = None, base_client=None):
    """
    Create an Anthropic client that automatically enables streaming for large responses.
    
    Args:
        api_key: Anthropic API key
        base_client: Optional pre-configured Anthropic client
        
    Returns:
        An enhanced Anthropic client with streaming capability
    """
    if base_client is not None:
        return base_client
    
    # Create standard client
    client = Anthropic(api_key=api_key)
    
    # Store original method
    original_create = client.beta.messages.create
    original_with_raw_response = client.beta.messages.with_raw_response.create
    
    # Define wrapper for standard create method
    def adaptive_create(*args, **kwargs):
        """Wrapper that enables streaming for large responses"""
        # Check if this is a large request
        max_tokens = kwargs.get('max_tokens', 4096)
        stream = kwargs.get('stream', None)
        
        # If stream is already set, respect that setting
        if stream is not None:
            return original_create(*args, **kwargs)
        
        # Enable streaming for large responses
        if max_tokens > 20000:
            logger.info(f"Enabling streaming for request with {max_tokens} tokens")
            kwargs['stream'] = True
            return handle_streaming_response(*args, **kwargs)
        
        # Use standard method for smaller requests
        return original_create(*args, **kwargs)
    
    # Define wrapper for with_raw_response
    def adaptive_with_raw_response_create(*args, **kwargs):
        """Wrapper for raw response method"""
        # Check if this is a large request
        max_tokens = kwargs.get('max_tokens', 4096)
        stream = kwargs.get('stream', None)
        
        # If stream is already set, respect that setting
        if stream is not None:
            return original_with_raw_response(*args, **kwargs)
        
        # Enable streaming for large responses
        if max_tokens > 20000:
            logger.info(f"Enabling streaming for raw response with {max_tokens} tokens")
            kwargs['stream'] = True
            # We need to handle this differently for raw responses
            # For simplicity, we'll just use the original method with streaming enabled
            return original_with_raw_response(*args, **kwargs)
        
        # Use standard method for smaller requests
        return original_with_raw_response(*args, **kwargs)
    
    # Define streaming handler
    def handle_streaming_response(*args, **kwargs):
        """Handle streaming response and convert to standard format"""
        stream = original_create(*args, **kwargs)
        
        # Initialize storage for content blocks
        content_blocks = []
        current_block = None
        
        # Process the stream
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
                if current_block is not None and hasattr(chunk.delta, 'text'):
                    current_block["text"] += chunk.delta.text
            
            elif chunk.type == "content_block_stop":
                # Finalize the current block and add to list
                if current_block is not None:
                    content_blocks.append(current_block)
                    current_block = None
            
            elif chunk.type == "message_stop":
                # Message is complete
                pass
        
        # Create a synthetic response
        response = {
            "id": "msg_streaming_synthetic",
            "type": "message",
            "role": "assistant",
            "content": content_blocks,
            "model": kwargs.get("model", "unknown"),
            "stop_reason": "end_turn",
            "stop_sequence": None,
        }
        
        return response
    
    # Replace the original methods with our wrapped versions
    client.beta.messages.create = adaptive_create
    client.beta.messages.with_raw_response.create = adaptive_with_raw_response_create
    
    return client
