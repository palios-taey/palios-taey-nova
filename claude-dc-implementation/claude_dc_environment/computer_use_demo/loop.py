"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""

import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast

import httpx
from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from token_manager import TokenManager
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from .tools import (
    TOOL_GROUPS_BY_VERSION,
    ToolCollection,
    ToolResult,
    ToolVersion,
)

# Constants
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
SYSTEM_PROMPT = "You are a helpful AI assistant."  # Default system prompt
logger = __import__('logging').getLogger(__name__)

# Initialize token manager
token_manager = TokenManager()

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    VERTEX = "vertex"
    BEDROCK = "bedrock"

def _inject_prompt_caching(messages: list[BetaMessageParam]) -> None:
    """Inject prompt caching instructions into messages."""
    for message in messages:
        if "content" in message and isinstance(message["content"], list):
            for block in message["content"]:
                if block["type"] == "text":
                    block["cache_control"] = {"type": "ephemeral"}

def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam], n: int, min_removal_threshold: int
) -> None:
    """Filter messages to keep only the n most recent images."""
    image_count = sum(
        1 for m in messages for c in m.get("content", []) if c.get("type") == "image"
    )
    if image_count <= min_removal_threshold:
        return
    images_kept = 0
    for message in reversed(messages):
        if "content" not in message or not isinstance(message["content"], list):
            continue
        for i, block in enumerate(message["content"]):
            if block.get("type") == "image":
                if images_kept < n:
                    images_kept += 1
                else:
                    message["content"][i] = {"type": "text", "text": "[Image removed]"}

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaToolUseBlockParam | BetaTextBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request | None, httpx.Response | dict | BetaMessage | None, Exception | None], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
    stream: bool = True,
) -> list[BetaMessageParam]:
    """
    Agentic sampling loop for assistant/tool interaction with computer use.

    Args:
        model: The Anthropic model to use.
        provider: The API provider (Anthropic, Vertex, or Bedrock).
        system_prompt_suffix: Additional text to append to the system prompt.
        messages: List of messages in the conversation.
        output_callback: Callback for rendering assistant output.
        tool_output_callback: Callback for rendering tool results.
        api_response_callback: Callback for logging API requests/responses.
        api_key: API key for authentication.
        only_n_most_recent_images: Limit to n most recent images in messages.
        max_tokens: Maximum tokens for the response.
        tool_version: Version of the toolset to use.
        thinking_budget: Budget for thinking tokens, if enabled.
        token_efficient_tools_beta: Enable token-efficient tools beta.
        stream: Whether to stream the response (default: True).

    Returns:
        Updated list of messages after processing.
    """
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        enable_prompt_caching = False
        betas = [tool_group.beta_flag] if tool_group.beta_flag else []
        if token_efficient_tools_beta:
            betas.append("token-efficient-tools-2025-02-19")
        betas.append("output-128k-2025-02-19")

        image_truncation_threshold = only_n_most_recent_images or 0
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
            enable_prompt_caching = True
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()

        if enable_prompt_caching:
            betas.append(PROMPT_CACHING_BETA_FLAG)
            _inject_prompt_caching(messages)
            only_n_most_recent_images = 0
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore

        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages, only_n_most_recent_images, image_truncation_threshold
            )

        extra_body = {"thinking": {"type": "enabled", "budget_tokens": thinking_budget}} if thinking_budget else {}

        try:
            if stream:
                with client.messages.with_raw_response.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    system=system["text"],
                    tools=tool_collection.to_params(),
                    betas=betas,
                    stream=True,
                    **extra_body,
                ) as raw_response_stream:
                    headers = dict(raw_response_stream.headers)
                    response_blocks = []
                    for event in raw_response_stream:
                        if event.type == "content_block_start":
                            block = event.content_block
                            if block.type == "text":
                                response_blocks.append(BetaTextBlockParam(type="text", text=""))
                            elif block.type == "tool_use":
                                response_blocks.append(cast(BetaToolUseBlockParam, block.model_dump()))
                            elif block.type == "thinking":
                                response_blocks.append({"type": "thinking", "thinking": ""})
                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                response_blocks[-1]["text"] += event.delta.text
                            elif event.delta.type == "thinking_delta":
                                response_blocks[-1]["thinking"] += event.delta.text
                        elif event.type == "message_stop":
                            api_response_callback(None, {"status_code": 200, "headers": headers}, None)
                    token_manager.manage_request(headers)
            else:
                with client.messages.with_raw_response.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    system=system["text"],
                    tools=tool_collection.to_params(),
                    betas=betas,
                    stream=False,
                    **extra_body,
                ) as raw_response:
                    response = raw_response.parse()
                    headers = dict(raw_response.headers)
                    api_response_callback(None, response, None)
                    token_manager.manage_request(headers)
                    response_blocks = []
                    for block in response.content:
                        if block.type == "text":
                            response_blocks.append(BetaTextBlockParam(type="text", text=block.text))
                        elif block.type == "tool_use":
                            response_blocks.append(cast(BetaToolUseBlockParam, block.model_dump()))
                        elif block.type == "thinking":
                            response_blocks.append({"type": "thinking", "thinking": block.thinking})
                        elif block.type == "redacted_thinking":
                            response_blocks.append({"type": "redacted_thinking", "data": block.data})
                        else:
                            logger.warning(f"Unknown block type: {block.type}")

            messages.append({"role": "assistant", "content": response_blocks})
            tool_result_content = []
            for content_block in response_blocks:
                output_callback(content_block)
                if content_block.get("type") == "tool_use":
                    result = await tool_collection.run(
                        name=content_block["name"],
                        tool_input=cast(dict[str, Any], content_block["input"]),
                    )
                    tool_result = {"type": "tool_result", "tool_use_id": content_block["id"], "content": result.output}
                    tool_result_content.append(tool_result)
                    tool_output_callback(result, content_block["id"])
            if not tool_result_content:
                return messages
            messages.append({"content": tool_result_content, "role": "user"})

        except (APIStatusError, APIResponseValidationError, APIError) as e:
            api_response_callback(getattr(e, 'request', None), getattr(e, 'response', None) or getattr(e, 'body', None), e)
            return messages
        except Exception as e:
            api_response_callback(None, None, e)
            return messages
