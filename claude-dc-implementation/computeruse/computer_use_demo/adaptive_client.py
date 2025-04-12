"""
Adaptive Anthropic Client that handles streaming requirements transparently.
"""

import os
import time
from typing import Dict, Any, List, Union, Optional, cast

import httpx
from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

# Import token manager
try:
    from simple_token_manager import token_manager
except ImportError:
    token_manager = None


class AdaptiveAnthropicClient:
    """
    A wrapper around the Anthropic client that handles streaming requirements transparently.
    Designed to be a drop-in replacement for the existing Anthropic client in loop.py.
    """
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "anthropic"):
        """Initialize with an API key and provider."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "NOT_PROVIDED")
        self.provider = provider
        
        # Initialize the appropriate client
        if provider == "anthropic":
            self.client = Anthropic(api_key=self.api_key, max_retries=4)
        elif provider == "vertex":
            self.client = AnthropicVertex()
        elif provider == "bedrock":
            self.client = AnthropicBedrock()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Initialize the beta property
        self.beta = AdaptiveBetaClient(self)
    
    def _calculate_streaming_requirement(self, max_tokens: int, thinking_budget: Optional[int] = None) -> bool:
        """Determine if streaming is required based on token sizes."""
        return max_tokens > 4096 or (thinking_budget is not None and thinking_budget > 4096)


class AdaptiveBetaClient:
    """Beta client that provides access to beta endpoints."""
    
    def __init__(self, parent_client):
        self.parent_client = parent_client
        self.messages = AdaptiveMessagesClient(self.parent_client)


class AdaptiveMessagesClient:
    """Messages client that handles streaming requirements transparently."""
    
    def __init__(self, parent_client):
        self.parent_client = parent_client
        self.with_raw_response = AdaptiveMessagesWithRawResponseClient(self.parent_client)
    
    def create(self, **kwargs):
        """Create a message, forwarding to with_raw_response.create()."""
        return self.with_raw_response.create(**kwargs).parse()


class AdaptiveMessagesWithRawResponseClient:
    """Client that handles raw responses."""
    
    def __init__(self, parent_client):
        self.parent_client = parent_client
    
    def create(self, **kwargs):
        """
        Create a message, automatically handling streaming for large token operations.
        """
        # Extract parameters to check for streaming requirement
        max_tokens = kwargs.get('max_tokens', 4096)
        thinking_budget = None
        extra_body = kwargs.get('extra_body', {})
        if extra_body and 'thinking' in extra_body:
            thinking = extra_body.get('thinking', {})
            if thinking and isinstance(thinking, dict):
                thinking_budget = thinking.get('budget_tokens')
        
        # Determine if streaming is required
        requires_streaming = self.parent_client._calculate_streaming_requirement(max_tokens, thinking_budget)
        
        # If streaming is required, handle it transparently
        if requires_streaming:
            return self._handle_streaming_request(**kwargs)
        else:
            # Use the standard client
            return self.parent_client.client.beta.messages.with_raw_response.create(**kwargs)
    
    def _handle_streaming_request(self, **kwargs):
        """Handle a request that requires streaming but present it as non-streaming."""
        # Make a copy of kwargs to avoid modifying the original
        stream_kwargs = dict(kwargs)
        
        # Remove the stream parameter if it exists
        if 'stream' in stream_kwargs:
            del stream_kwargs['stream']
        
        try:
            # Make the streaming request using the context manager
            with self.parent_client.client.beta.messages.stream(**stream_kwargs) as stream:
                # Collect all text from the text stream
                combined_text = ""
                for chunk in stream.text_stream:
                    combined_text += chunk
                
                # Create a message response object that looks like a non-streaming response
                message = BetaMessage(
                    id=getattr(stream, 'id', ''),
                    type="message",
                    role="assistant",
                    content=[BetaTextBlock(type="text", text=combined_text)],
                    model=getattr(stream, 'model', kwargs.get('model', '')),
                    stop_reason="end_turn"
                )
            
            # Create a wrapper that mimics a raw response
            class StreamedRawResponse:
                def __init__(self, message, headers):
                    self.message = message
                    self.http_response = type('MockResponse', (), {
                        'headers': headers,
                        'request': httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
                        'status_code': 200,
                        'read': lambda: b'{"streamed_response": true}',
                        'text': '{"streamed_response": true}'
                    })
                
                def parse(self):
                    return self.message
            
            # Mock HTTP response headers for token management
            mock_headers = {
                "x-input-tokens": str(len(str(kwargs.get('messages', ''))) // 4),
                "x-output-tokens": str(len(combined_text) // 4)
            }
            
            # Apply token management if available
            if token_manager:
                token_manager.manage_request(mock_headers)
            
            # Create and return the wrapper
            return StreamedRawResponse(message, mock_headers)
            
        except Exception as e:
            # Re-raise any exceptions
            raise e


def create_adaptive_client(api_key=None, provider="anthropic"):
    """Factory function to create an adaptive client."""
    return AdaptiveAnthropicClient(api_key=api_key, provider=provider)
