import platform
import httpx
from typing import Any, cast, Optional, List, Dict
from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIError, APIResponseValidationError, APIStatusError
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
from .token_manager import token_manager
from .tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolVersion
from .types import APIProvider, ToolResult

# System prompt for Claude's agent
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are using an Ubuntu virtual machine with {platform.machine()} architecture.
* You can install applications with the bash tool. Use curl instead of wget.
* The current date is {platform.system()}.
</SYSTEM_CAPABILITY>"""

def _inject_prompt_caching(messages: List[BetaMessageParam]):
    """
    Set cache control for the 3 most recent user messages to improve caching.
    """
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(message["content"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                message["content"][-1]["cache_control"] = BetaCacheControlEphemeralParam({"type": "ephemeral"})  # type: ignore
            else:
                message["content"][-1].pop("cache_control", None)
                break

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    """Convert a ToolResult object into a ToolResultBlockParam for the conversation."""
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = result.error
    else:
        # Prepare content list for text and image outputs
        tool_result_content_list: list[BetaTextBlockParam | BetaImageBlockParam] = []
        if result.output:
            tool_result_content_list.append({"type": "text", "text": result.output})
        if result.base64_image:
            tool_result_content_list.append({
                "type": "image",
                "source": {"type": "base64", "data": result.base64_image},
            })
        tool_result_content = tool_result_content_list
    return BetaToolResultBlockParam(
        tool_use_id=tool_use_id,
        type="tool_result",
        content=tool_result_content,
        is_error=is_error,
    )

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Optional[callable] = None,
    tool_output_callback: Optional[callable] = None,
    api_response_callback: Optional[callable] = None,
    api_key: str,
    only_n_most_recent_images: int = 0,
    max_tokens: int = 4096,
    tool_version: ToolVersion = None,
    thinking_budget: Optional[int] = None,
    token_efficient_tools_beta: bool = False,
) -> list[BetaMessageParam]:
    """
    Run Claude's agentic loop, streaming the response back to the UI.
    """
    tool_group = TOOL_GROUPS_BY_VERSION.get(str(tool_version)) if tool_version else None
    if tool_group is None:
        raise ValueError(f"Unknown tool_version: {tool_version}")
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))

    # Build system prompt with optional suffix
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{(' ' + system_prompt_suffix) if system_prompt_suffix else ''}",
    )

    while True:
        enable_prompt_caching = False
        betas: List[str] = []
        if tool_group.beta_flag:
            betas.append(tool_group.beta_flag)
        if token_efficient_tools_beta:
            betas.append("token-efficient-tools-2025-02-19")
        image_truncation_threshold = only_n_most_recent_images or 0

        # Initialize appropriate Anthropic client for provider
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
            enable_prompt_caching = True
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Apply prompt caching for recent user messages if available
        if enable_prompt_caching:
            betas.append("prompt-caching-2024-07-31")
            _inject_prompt_caching(messages)
            # If caching, don't remove images for cache to work effectively
            only_n_most_recent_images = 0
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore

        # Optionally filter older images from context to reduce token usage
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )
        extra_body: Dict[str, Any] = {}
        if thinking_budget:
            extra_body = {"thinking": {"type": "enabled", "budget_tokens": thinking_budget}}

        # Estimate token usage for rate limiting
        estimated_input_tokens = 0
        try:
            count_resp = client.beta.messages.count_tokens(
                model=model,
                messages=messages,
                system=[system],
                tools=tool_collection.to_params(),
                betas=betas,
                extra_body=extra_body,
            )
            estimated_input_tokens = getattr(count_resp, "input_tokens", 0)
        except Exception:
            # Fallback to a rough estimate if token count failed
            all_text = ""
            for msg in messages:
                if isinstance(msg["content"], str):
                    all_text += msg["content"]
                elif isinstance(msg["content"], list):
                    for block in msg["content"]:
                        if isinstance(block, dict) and "text" in block:
                            all_text += block["text"]
            estimated_input_tokens = max(1, len(all_text) // 4)
        estimated_output_tokens = max_tokens
        token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)

        # Call Claude API with streaming response
        try:
            stream_response = client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                system=[system],
                tools=tool_collection.to_params(),
                betas=betas,
                extra_body=extra_body,
                stream=True,
            )
        except (APIStatusError, APIResponseValidationError) as e:
            # If API returned an error status or invalid response, record and break
            if api_response_callback:
                api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            # If a general API error occurred, record it and break
            if api_response_callback:
                api_response_callback(e.request, e.body, e)
            return messages

        assistant_text = ""
        tool_event: Optional[BetaToolUseBlockParam] = None
        # Stream output tokens and accumulate assistant text
        for event in stream_response:
            if hasattr(event, "type") and (getattr(event, "type") in {"tool", "tool_use"}):
                tool_event = event
                break  # Claude is requesting a tool, break out to handle it
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                chunk_text = event.delta.text
                assistant_text += str(chunk_text)
                if output_callback:
                    output_callback(chunk_text)

        # If a tool was requested by Claude:
        if tool_event:
            content_blocks: List[BetaContentBlockParam] = []
            if assistant_text:
                content_blocks.append(BetaTextBlockParam(type="text", text=assistant_text))
            # Serialize the tool_event (tool_use block) to a dict
            if isinstance(tool_event, dict):
                tool_use_block = tool_event
            else:
                tool_use_block = tool_event.model_dump() if callable(getattr(tool_event, "model_dump", None)) else tool_event.__dict__
            tool_use_block_param = tool_use_block  # dictionary form of tool_use
            content_blocks.append(tool_use_block_param)
            # Append assistant message with the tool request to the message history
            messages.append({"role": "assistant", "content": content_blocks})
            # Execute the requested tool
            tool_name = tool_use_block_param.get("tool") or tool_use_block_param.get("name") or tool_use_block_param.get("tool_name")
            tool_input = tool_use_block_param.get("input") or {}
            result = await tool_collection.run(name=tool_name, tool_input=cast(dict[str, Any], tool_input))
            # Convert tool result to a message block and append as a user turn
            tool_result_block = _make_api_tool_result(result, tool_use_block_param.get("id"))
            messages.append({"role": "user", "content": [tool_result_block]})
            # Notify UI about the tool output (for display)
            if tool_output_callback:
                tool_output_callback(result, tool_use_block_param.get("id"))
            # Continue loop to send the tool's output to Claude for the next response
            continue
        else:
            # No tool used: final assistant answer obtained
            if assistant_text:
                messages.append({"role": "assistant", "content": [BetaTextBlockParam(type="text", text=assistant_text)]})
            # Update token usage stats
            output_tokens = 0
            try:
                from tokenizers import Encoding as ENCODING  # optional: use tiktoken if available
            except ImportError:
                ENCODING = None
            if ENCODING and callable(getattr(ENCODING, "encode", None)):
                # If encoding available, count tokens precisely
                try:
                    output_tokens = len(ENCODING.encode(assistant_text))  # type: ignore
                except Exception:
                    output_tokens = max(1, len(assistant_text) // 4)
            else:
                output_tokens = max(1, len(assistant_text) // 4)
            header_info = {
                "anthropic-input-tokens": str(estimated_input_tokens),
                "anthropic-output-tokens": str(output_tokens)
            }
            token_manager.process_response_headers(header_info)
            return messages

def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
):
    """
    Remove all but the last `images_to_keep` tool_result images from the conversation.
    This reduces prompt size while keeping recent screenshots.
    """
    if images_to_keep is None or images_to_keep <= 0:
        return messages

    # Gather all tool_result blocks from the conversation
    tool_result_blocks = cast(List[BetaToolResultBlockParam], [
        item
        for message in messages
        for item in (message["content"] if isinstance(message["content"], list) else [])
        if isinstance(item, dict) and item.get("type") == "tool_result"
    ])
    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )
    images_to_remove = total_images - images_to_keep
    # Remove images in multiples of min_removal_threshold for cache-friendliness
    images_to_remove -= images_to_remove % (min_removal_threshold or 1)

    # Remove the oldest images first
    for tool_result in tool_result_blocks:
        contents = tool_result.get("content")
        if isinstance(contents, list):
            new_content = []
            for block in contents:
                if isinstance(block, dict) and block.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue  # skip (remove) this image
                new_content.append(block)
            tool_result["content"] = new_content

