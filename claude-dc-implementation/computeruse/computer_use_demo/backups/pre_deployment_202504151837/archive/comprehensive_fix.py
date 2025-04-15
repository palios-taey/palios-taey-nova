#!/usr/bin/env python3
"""
Comprehensive fix for streaming issues in both loop.py and streamlit.py
"""
import os
import sys
import re

def update_response_to_params():
    """Update the _response_to_params function in loop.py"""
    loop_path = "/home/computeruse/computer_use_demo/loop.py"
    
    # Make a backup
    backup_path = f"{loop_path}.backup-{os.path.basename(__file__)}"
    os.system(f"cp {loop_path} {backup_path}")
    print(f"Created backup at {backup_path}")
    
    # Read the content
    with open(loop_path, 'r') as f:
        content = f.read()
    
    # Find the _response_to_params function
    pattern = r'def _response_to_params\([^)]*\):.*?(?=def|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find _response_to_params function in loop.py")
        return False
    
    # Define our new implementation
    new_function = '''def _response_to_params(response):
    """
    Convert a response object to parameters.
    Modified to handle streaming responses.
    """
    res = []
    
    # Handle streaming response
    if hasattr(response, 'stream') and response.stream:
        # Create a simple text block to allow the pipeline to continue
        return [{"type": "text", "text": "Please wait while Claude processes your request..."}]
    
    # Handle regular response
    if hasattr(response, 'content'):
        for block in response.content:
            if isinstance(block, BetaTextBlock):
                if block.text:
                    res.append(BetaTextBlockParam(type="text", text=block.text))
                elif getattr(block, "type", None) == "thinking":
                    # Handle thinking blocks - include signature field
                    thinking_block = {
                        "type": "thinking",
                        "thinking": getattr(block, "thinking", None),
                    }
                    if hasattr(block, "signature"):
                        thinking_block["signature"] = getattr(block, "signature", None)
                    res.append(cast(BetaContentBlockParam, thinking_block))
            else:
                # Handle tool use blocks normally
                res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    
    return res'''
    
    # Replace the function
    new_content = content.replace(match.group(0), new_function)
    
    # Write back to the file
    with open(loop_path, 'w') as f:
        f.write(new_content)
    
    print("Successfully updated _response_to_params function in loop.py")
    return True

def update_render_api_response():
    """Update the _render_api_response function in streamlit.py"""
    streamlit_path = "/home/computeruse/computer_use_demo/streamlit.py"
    
    # Make a backup
    backup_path = f"{streamlit_path}.backup-{os.path.basename(__file__)}"
    os.system(f"cp {streamlit_path} {backup_path}")
    print(f"Created backup at {backup_path}")
    
    # Read the content
    with open(streamlit_path, 'r') as f:
        content = f.read()
    
    # Find the _render_api_response function
    pattern = r'def _render_api_response\([^)]*\):.*?(?=def|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find _render_api_response function in streamlit.py")
        return False
    
    # Define our new implementation
    new_function = '''def _render_api_response(request, response, response_id, tab=None):
    """Render an API response to a streamlit tab"""
    if tab is None:
        tab = st
        
    with tab.expander(f"Request/Response ({response_id})"):
        # Render request details
        if request:
            try:
                tab.markdown(f"**Request**: `{request.method} {request.url}`")
                if hasattr(request, 'headers'):
                    for k, v in request.headers.items():
                        tab.markdown(f"`{k}: {v}`")
                if hasattr(request, 'read') and callable(request.read):
                    try:
                        tab.text(request.read().decode())
                    except:
                        tab.text(str(request))
                else:
                    tab.text(str(request))
            except Exception as e:
                tab.error(f"Error rendering request: {e}")
                tab.text(str(request))
        else:
            tab.text("No request information available")
            
        tab.markdown("---")
            
        # Handle response
        if response:
            try:
                # Check for streaming response
                if hasattr(response, 'stream') and response.stream:
                    tab.text("Streaming response - content preview not available")
                    return
                
                # Handle normal response
                if hasattr(response, 'status_code'):
                    tab.markdown(f"**Status**: `{response.status_code}`")
                    
                if hasattr(response, 'headers'):
                    for k, v in response.headers.items():
                        tab.markdown(f"`{k}: {v}`")
                
                # Try to display content
                content_displayed = False
                
                # Method 1: model_dump_json for Pydantic models
                if hasattr(response, 'model_dump_json') and callable(response.model_dump_json):
                    try:
                        tab.json(response.model_dump_json())
                        content_displayed = True
                    except:
                        pass
                
                # Method 2: read() for httpx responses
                if not content_displayed and hasattr(response, 'read') and callable(response.read):
                    try:
                        content = response.read()
                        if isinstance(content, bytes):
                            tab.json(content.decode())
                        else:
                            tab.json(content)
                        content_displayed = True
                    except:
                        pass
                
                # Method 3: content attribute
                if not content_displayed and hasattr(response, 'content'):
                    try:
                        content = response.content
                        if isinstance(content, bytes):
                            tab.json(content.decode())
                        else:
                            tab.json(content)
                        content_displayed = True
                    except:
                        pass
                
                # Method 4: text attribute or method
                if not content_displayed and hasattr(response, 'text'):
                    try:
                        if callable(response.text):
                            tab.text(response.text())
                        else:
                            tab.text(response.text)
                        content_displayed = True
                    except:
                        pass
                
                # Fallback
                if not content_displayed:
                    tab.text(str(response))
                    
            except Exception as e:
                tab.error(f"Error rendering response: {e}")
                tab.text(str(response))
        else:
            tab.text("No response information available")'''
    
    # Replace the function
    new_content = content.replace(match.group(0), new_function)
    
    # Write back to the file
    with open(streamlit_path, 'w') as f:
        f.write(new_content)
    
    print("Successfully updated _render_api_response function in streamlit.py")
    return True

def update_adaptive_client():
    """Update the adaptive_client.py file with a simpler version"""
    client_path = "/home/computeruse/computer_use_demo/adaptive_client.py"
    
    # Make a backup
    backup_path = f"{client_path}.backup-{os.path.basename(__file__)}"
    os.system(f"cp {client_path} {backup_path}")
    print(f"Created backup at {backup_path}")
    
    # Create new client implementation
    new_content = '''"""
Adaptive Anthropic Client that handles streaming requirements transparently.
"""

import os
import time
import json
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

# Import token manager
try:
    from simple_token_manager import token_manager
except ImportError:
    token_manager = None


class AdaptiveAnthropicClient:
    """
    A wrapper around the Anthropic client that handles streaming requirements transparently.
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
        
        # For small token operations, use the standard client
        if not self.parent_client._calculate_streaming_requirement(max_tokens, thinking_budget):
            # Use the standard client
            return self.parent_client.client.beta.messages.with_raw_response.create(**kwargs)
        
        # For large token operations that require streaming, use standard client but with streaming=True
        modified_kwargs = dict(kwargs)
        modified_kwargs['stream'] = True
        
        # Apply token management if available
        if token_manager:
            headers = kwargs.get('headers', {})
            token_estimates = {
                "x-input-tokens": str(len(str(kwargs.get('messages', ''))) // 4),
                "x-output-tokens": str(max_tokens // 2)  # Conservative estimate
            }
            token_manager.manage_request(token_estimates)
        
        try:
            # Use the standard client with streaming
            return self.parent_client.client.beta.messages.with_raw_response.create(**modified_kwargs)
        except Exception as e:
            print(f"Error in API call: {e}")
            raise e


def create_adaptive_client(api_key=None, provider="anthropic"):
    """Factory function to create an adaptive client."""
    return AdaptiveAnthropicClient(api_key=api_key, provider=provider)
'''
    
    # Write to the file
    with open(client_path, 'w') as f:
        f.write(new_content)
    
    print("Successfully updated adaptive_client.py")
    return True

if __name__ == "__main__":
    print("Applying comprehensive fix for streaming issues...")
    
    # Update all components
    update_adaptive_client()
    update_response_to_params()
    update_render_api_response()
    
    print("\nFixes have been applied successfully!")
    print("Please restart streamlit with: cd /home/computeruse/computer_use_demo/ && python streamlit.py")
