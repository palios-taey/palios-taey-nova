import platform
import httpx
from typing import Any, cast, Optional, List, Dict, Callable
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
from computer_use_demo import token_manager
from .tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolVersion
from computer_use_demo.types import APIProvider, ToolResult

# System prompt for Claude's agent
SYSTEM_PROMPT = f\"\"\"<SYSTEM_CAPABILITY>\n* You are using an \
Ubuntu virtual machine with {platform.machine()} architecture.\n* You \
can install applications with the bash tool. Use curl instead of \
wget.\n* The current date is \
{platform.system()}.\n</SYSTEM_CAPABILITY>\"\"\"

def _inject_prompt_caching(messages: List[BetaMessageParam]):
    \"\"\"\
    Set cache control for the 3 most recent user messages to improve caching.\n    \"\"\"\
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message[\"role\"] == \"user\" and isinstance(message[\"content\"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                message[\"content\"][-1][\"cache_control\"] = BetaCacheControlEphemeralParam({\"type\": \"ephemeral\"})  # type: ignore
            else:
                message[\"content\"][-1].pop(\"cache_control\", None) # type: ignore

def _remove_oldest_tool_result_images(
    messages: List[BetaMessageParam], images_to_keep: Optional[int], min_removal_threshold: Optional[int]
) -> List[BetaMessageParam]:
    \"\"\"\
    Keep the `images_to_keep` most recent `tool_result` images from the conversation.\n    This reduces prompt size while keeping recent screenshots.\n    \"\"\"\
    if images_to_keep is None or images_to_keep <= 0:
        return messages

    # Gather all tool_result blocks from the conversation
    tool_result_blocks = cast(List[BetaToolResultBlockParam], [
        item
        for message in messages
        for item in (message[\"content\"] if isinstance(message[\"content\"], list) else [])
        if isinstance(item, dict) and item.get(\"type\") == \"tool_result\"
    ])
    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get(\"content\", [])
        if isinstance(content, dict) and content.get(\"type\") == \"image\"
    )
    images_to_remove = total_images - images_to_keep
    # Remove images in multiples of min_removal_threshold for cache-friendliness
    images_to_remove -= images_to_remove % (min_removal_threshold or 1)

    # Remove the oldest images first
    for tool_result in tool_result_blocks:
        contents = tool_result.get(\"content\")
        if isinstance(contents, list):
            new_content = []
            for block in contents:
                if isinstance(block, dict) and block.get(\"type\") == \"image\":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue  # skip (remove) this image
                new_content.append(block)
            tool_result[\"content\"] = new_content

    return messages

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request | None, httpx.Response | object | None, Exception | None], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
    stream: bool = False,
):
    # Inject prompt caching instructions
    _inject_prompt_caching(messages)

    # Remove oldest tool_result images if needed
    messages = _remove_oldest_tool_result_images(messages, only_n_most_recent_images, 3)

    # Determine the API client
    if provider == APIProvider.ANTHROPIC:
        client = Anthropic(api_key=api_key)
    elif provider == APIProvider.VERTEX:
        client = AnthropicVertex(api_key=api_key)
    elif provider == APIProvider.BEDROCK:
        client = AnthropicBedrock(api_key=api_key)
    else:
        raise ValueError(f"Invalid provider: {provider}")

    # Determine the tools to use
    tool_collection = ToolCollection(tool_version=tool_version)

    # Construct the Anthropic message
    anthropic_messages = cast(List[BetaMessageParam], messages)
    if system_prompt_suffix:
        anthropic_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT + system_prompt_suffix})
    else:
        anthropic_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    # Call the Anthropic API
    try:
        if stream:
            raw_response = await client.messages.create(
                model=model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                stream=True,
                tool_choice="auto",
                tools=tool_collection.to_anthropic_tools(),
            )
            headers = dict(raw_response.headers)
            response_blocks = []
            async for event in raw_response:
                if event.type == "message_start":
                    pass
                elif event.type == "content_block_start":
                    response_blocks.append({"type": event.content_block.type, "data": ""})
                elif event.type == "content_block_delta":
                    if response_blocks:
                        response_blocks[-1]["data"] += event.delta.text
                        output_callback(response_blocks[-1])
                elif event.type == "tool_use":
                    response_blocks.append({"type": "tool_use", "id": event.tool_use.id, "name": event.tool_use.name, "input": event.tool_use.input})
                    output_callback(response_blocks[-1])
                elif event.type == "tool_result":
                    response_blocks.append({"type": "tool_result", "tool_use_id": event.tool_result.tool_use_id, "content": event.tool_result.content})
                    tool_output_callback(ToolResult(output=str(event.tool_result.content)), event.tool_result.tool_use_id)
                elif event.type == "message_end":
                    pass
                elif event.type == "ping":
                    pass
                else:
                    logger.warning(f"Unknown event type: {event.type}")

            token_manager.manage_request(headers)
            api_response_callback(None, {"status_code": 200, "headers": headers}, None)
        else:
            response = await client.messages.create(
                model=model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                tool_choice="auto",
                tools=tool_collection.to_anthropic_tools(),
            )
            token_manager.manage_request(dict(response.http_response.headers))
            api_response_callback(response.http_response.request, response.http_response, None)
            response_blocks = response.content

        messages.append({"role": "assistant", "content": response_blocks})
        tool_result_content = []
        for content_block in response_blocks:
            output_callback(content_block)
            if content_block.get("type") == "tool_use":
                result = await tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),\
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
    return messages
