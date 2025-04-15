"""
Main event loop for Claude Computer Use with comprehensive protection systems
"""
import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("computer_use")

# Import modules (in correct order)
# Import tool intercept FIRST to ensure it's active for all operations
sys.path.append('/home/computeruse/computer_use_demo')
try:
    from tool_intercept import tool_intercept
    logger.info("Tool interception active")
except ImportError:
    logger.warning("Tool interception not available - file operations may exceed rate limits")

# Import other modules
from tools.collection import ToolCollection
from token_management.token_manager import token_manager
from streaming.streaming_client import StreamingClient

# Import tools
from tools import TOOL_GROUPS_BY_VERSION, ToolVersion

# After all imports, initialize streaming client
streaming_client = StreamingClient(token_manager=token_manager)

# Global constants
MAX_TOKENS = 128000  # Maximum tokens for response
THINKING_BUDGET = 32000  # Tokens for thinking
BETAS = ["output-128k-2025-02-19"]  # Beta flags for extended output

async def sampling_loop(
    *,
    model: str,
    provider: str,
    system_prompt_suffix: str,
    messages: list,
    output_callback: Callable,
    tool_output_callback: Callable,
    api_response_callback: Callable,
    api_key: str,
    only_n_most_recent_images: int = None,
    max_tokens: int = MAX_TOKENS,
    tool_version: str = "20250124",
    thinking_budget: int = THINKING_BUDGET,
    token_efficient_tools_beta: bool = False,
):
    """
    Main sampling loop with comprehensive protection
    """
    # Initialize tool collection
    tool_group = TOOL_GROUPS_BY_VERSION[ToolVersion(tool_version)]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    
    # System prompt
    system = {"type": "text", "text": os.getenv("SYSTEM_PROMPT", "") + (system_prompt_suffix or "")}
    
    # Check token usage before proceeding
    token_stats = token_manager.get_stats()
    logger.info(f"Token usage before request: {token_stats}")
    
    while True:
        # Prepare beta flags
        enable_prompt_caching = False
        betas = [tool_group.beta_flag] if tool_group.beta_flag else []
        if token_efficient_tools_beta:
            betas.append("token-efficient-tools-2025-02-19")
        
        # Add extended output beta
        if "output-128k-2025-02-19" not in betas:
            betas.append("output-128k-2025-02-19")
        
        # Use streaming for large requests
        use_streaming = max_tokens > 4096 or len(str(messages)) > 10000
        
        if use_streaming:
            logger.info(f"Using streaming for request with {max_tokens} max tokens")
            try:
                # Stream the response
                response = await streaming_client.stream_completion(
                    messages=messages,
                    model=model,
                    system=[system],
                    max_tokens=max_tokens,
                    tools=tool_collection.to_params(),
                    api_key=api_key,
                    thinking_budget=thinking_budget,
                    betas=betas,
                )
                
                # Process streaming response
                response_params = _response_to_params(response)
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                # Fall back to regular API call
                use_streaming = False
                
        # Use regular API call for smaller requests or if streaming failed
        if not use_streaming:
            try:
                # Choose client based on provider
                if provider == "anthropic":
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key, max_retries=4)
                elif provider == "vertex":
                    from anthropic import AnthropicVertex
                    client = AnthropicVertex()
                elif provider == "bedrock":
                    from anthropic import AnthropicBedrock
                    client = AnthropicBedrock()
                else:
                    raise ValueError(f"Unknown provider: {provider}")
                
                # Make API call
                raw_response = client.beta.messages.with_raw_response.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    system=[system],
                    tools=tool_collection.to_params(),
                    betas=betas,
                    extra_body={"thinking": {"type": "enabled", "budget_tokens": thinking_budget}} if thinking_budget else {},
                )
                
                # Process API response
                api_response_callback(raw_response.http_response.request, raw_response.http_response, None)
                response = raw_response.parse()
                response_params = _response_to_params(response)
                
            except Exception as e:
                logger.error(f"API error: {e}")
                raise
        
        # Append response to messages
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )
        
        tool_result_content = []
        for content_block in response_params:
            output_callback(content_block)
            if content_block["type"] == "tool_use":
                result = await tool_collection.run(
                    name=content_block["name"],
                    tool_input=content_block["input"],
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block["id"])
                )
                tool_output_callback(result, content_block["id"])
        
        if not tool_result_content:
            return messages
        
        messages.append({"content": tool_result_content, "role": "user"})

def _response_to_params(response):
    """Convert API response to content parameters"""
    res = []
    for block in response.content:
        if hasattr(block, "text") and block.text:
            res.append({"type": "text", "text": block.text})
        elif getattr(block, "type", None) == "thinking":
            # Handle thinking blocks
            thinking_block = {
                "type": "thinking",
                "thinking": getattr(block, "thinking", None),
            }
            if hasattr(block, "signature"):
                thinking_block["signature"] = getattr(block, "signature", None)
            res.append(thinking_block)
        else:
            # Handle tool use blocks
            res.append(block.model_dump())
    return res

def _make_api_tool_result(result, tool_use_id):
    """Convert tool result to API format"""
    tool_result_content = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }

def _maybe_prepend_system_tool_result(result, result_text):
    """Add system message to tool result if needed"""
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text
