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
        
        # Ensure stream=True for the API call
        stream_kwargs['stream'] = True
        
        try:
            # Make the streaming request
            stream_response = self.parent_client.client.beta.messages.stream(**stream_kwargs)
            
            # Collect all chunks to reconstruct a complete response
            chunks = []
            for chunk in stream_response:
                chunks.append(chunk)
            
            # Create a wrapper that mimics a raw response
            class StreamedRawResponse:
                def __init__(self, chunks, http_response):
                    self.chunks = chunks
                    self.http_response = http_response
                
                def parse(self):
                    """Combine chunks into a complete response."""
                    if not self.chunks:
                        return None
                    
                    # Use the first chunk as the base response
                    final_response = self.chunks[0]
                    
                    # For text messages, combine the text from all chunks
                    combined_text = ""
                    for chunk in self.chunks:
                        if hasattr(chunk, 'delta') and chunk.delta:
                            if hasattr(chunk.delta, 'text'):
                                combined_text += chunk.delta.text
                    
                    # Convert to BetaMessage format
                    final_content = [BetaTextBlock(type="text", text=combined_text)]
                    
                    # Create a BetaMessage response
                    message = BetaMessage(
                        id=getattr(final_response, 'id', ''),
                        type="message",
                        role="assistant",
                        content=final_content,
                        model=getattr(final_response, 'model', ''),
                        stop_reason=getattr(self.chunks[-1], 'stop_reason', None)
                    )
                    
                    return message
            
            # Mock HTTP response with headers for token management
            class MockHTTPResponse:
                def __init__(self):
                    self.request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
                    self.headers = {
                        "x-input-tokens": str(len(str(kwargs.get('messages', ''))) // 4),
                        "x-output-tokens": str(len("".join([
                            chunk.delta.text for chunk in chunks 
                            if hasattr(chunk, 'delta') and chunk.delta and hasattr(chunk.delta, 'text')
                        ])) // 4)
                    }
                    self.status_code = 200
                
                def read(self):
                    return b'{"streamed_response": true}'
                
                @property
                def text(self):
                    return '{"streamed_response": true}'
            
            # Create and return the wrapper
            return StreamedRawResponse(chunks, MockHTTPResponse())
            
        except Exception as e:
            # Re-raise any exceptions
            raise e


def create_adaptive_client(api_key=None, provider="anthropic"):
    """Factory function to create an adaptive client."""
    return AdaptiveAnthropicClient(api_key=api_key, provider=provider)
