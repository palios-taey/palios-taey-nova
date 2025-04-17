# loop.py
import platform
import logging
from typing import Any, cast, Optional, List, Dict, Callable
from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIError, APIResponseValidationError, APIStatusError
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)
from computer_use_demo import token_manager
from computer_use_demo.tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolVersion
from computer_use_demo.types import APIProvider, ToolResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base system prompt with dynamic info
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are using an Ubuntu virtual machine with {platform.machine()} architecture.
* You can install applications with the bash tool. Use curl instead of wget.
* The current date is {platform.system()}.
</SYSTEM_CAPABILITY>"""

def _inject_prompt_caching(messages: List[BetaMessageParam]):
    """Add ephemeral cache-control to recent user messages to improve response caching."""
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(message["content"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                message["content"][-1]["cache_control"] = BetaCacheControlEphemeralParam({"type": "ephemeral"})  # type: ignore
            else:
                message["content"][-1].pop("cache_control", None)

def _remove_oldest_tool_result_images(
    messages: List[BetaMessageParam],
    images_to_keep: Optional[int],
    min_removal_threshold: int = 1
) -> List[BetaMessageParam]:
    """Keep only the latest `images_to_keep` tool_result images in conversation history to manage token load."""
    if images_to_keep is None or images_to_keep <= 0:
        return messages
    tool_result_blocks = cast(List[BetaToolResultBlockParam], [
        item
        for msg in messages
        for item in (msg["content"] if isinstance(msg["content"], list) else [])
        if isinstance(item, dict) and item.get("type") == "tool_result"
    ])
    # Count total images in all tool_result blocks
    total_images = sum(
        1 for tr in tool_result_blocks for content in tr.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )
    images_to_remove = total_images - images_to_keep
    images_to_remove -= images_to_remove % (min_removal_threshold or 1)
    # Remove from oldest tool_result blocks first
    for tr in tool_result_blocks:
        if images_to_remove <= 0:
            break
        contents = tr.get("content")
        if isinstance(contents, list):
            new_content = []
            for block in contents:
                if isinstance(block, dict) and block.get("type") == "image" and images_to_remove > 0:
                    images_to_remove -= 1
                    continue  # drop this image
                new_content.append(block)
            tr["content"] = new_content
    return messages

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: List[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam | Dict], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[Any, Any, Optional[Exception]], None],
    api_key: str,
    only_n_most_recent_images: Optional[int] = None,
    max_tokens: int = 4096,
    tool_version: Optional[ToolVersion] = None,
    thinking_budget: Optional[int] = None,
    token_efficient_tools_beta: bool = False,
    stream: bool = True
) -> List[BetaMessageParam]:
    """Run one conversation turn with Claude. Streams the assistant's reply if `stream=True`."""
    # Apply caching hints and prune old images
    _inject_prompt_caching(messages)
    messages = _remove_oldest_tool_result_images(messages, only_n_most_recent_images, min_removal_threshold=3)
    # Initialize API client
    if provider == APIProvider.ANTHROPIC:
        client = Anthropic(api_key=api_key)
    elif provider == APIProvider.VERTEX:
        client = AnthropicVertex(api_key=api_key)
    elif provider == APIProvider.BEDROCK:
        client = AnthropicBedrock(api_key=api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    # Prepare tool collection
    tc = ToolCollection(tool_version=tool_version) if tool_version else ToolCollection()
    # Construct full message list with system prompt at the start
    anthropic_messages = cast(List[BetaMessageParam], messages.copy())
    if system_prompt_suffix:
        anthropic_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT + system_prompt_suffix})
    else:
        anthropic_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    # Enforce input token rate limit (40k/min) by token bucket
    estimated_input_tokens = len(str(anthropic_messages)) // 4  # rough estimate
    token_manager.consume_tokens(estimated_input_tokens)
    try:
        if stream:
            # Streaming mode: iterate over event stream
            raw_response = await client.messages.create(
                model=model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                stream=True,
                tool_choice="auto",
                tools=(tc.to_anthropic_tools() if hasattr(tc, "to_anthropic_tools") else None),
            )
            headers = dict(raw_response.headers)
            response_blocks: List[Dict] = []
            async for event in raw_response:
                if event.type == "message_start":
                    continue  # start of assistant response
                elif event.type == "content_block_start":
                    # Begin a new content block (text or other type)
                    response_blocks.append({"type": event.content_block.type, "data": ""})
                elif event.type == "content_block_delta":
                    # Append streaming text delta to current text block
                    if response_blocks and response_blocks[-1].get("type") == "text":
                        response_blocks[-1]["data"] += event.delta.text
                        output_callback(response_blocks[-1])
                elif event.type == "tool_use":
                    # Assistant invoked a tool
                    response_blocks.append({
                        "type": "tool_use",
                        "id": event.tool_use.id,
                        "name": event.tool_use.name,
                        "input": event.tool_use.input
                    })
                    output_callback(response_blocks[-1])
                elif event.type == "tool_result":
                    # Assistant expects a tool result (Anthropic might emit placeholder event)
                    response_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": event.tool_result.tool_use_id,
                        "content": event.tool_result.content
                    })
                    # Immediately show a placeholder or partial tool result (if any)
                    tool_output_callback(ToolResult(output=str(event.tool_result.content)), event.tool_result.tool_use_id)
                elif event.type == "message_end":
                    continue  # end of assistant message
                elif event.type == "ping":
                    continue  # keep-alive ping
                else:
                    logger.warning(f"Unknown event type: {event.type}")
            # Log token usage from headers
            token_manager.manage_request(headers)
            api_response_callback(None, {"status_code": 200, "headers": headers}, None)
        else:
            # Non-streaming mode
            response = await client.messages.create(
                model=model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                tool_choice="auto",
                tools=(tc.to_anthropic_tools() if hasattr(tc, "to_anthropic_tools") else None),
            )
            # Update rate limit usage
            token_manager.manage_request(dict(response.http_response.headers))
            api_response_callback(response.http_response.request, response.http_response, None)
            response_blocks = response.content  # list of BetaContentBlockParam
        # Add assistant response to conversation history
        messages.append({"role": "assistant", "content": response_blocks})
        tool_result_blocks: List[Dict] = []
        # Process any tool requests from the assistant
        for block in response_blocks:
            if block.get("type") == "tool_use":
                tool_name = block["name"]
                tool_input = cast(Dict[str, Any], block["input"])
                # Run the requested tool and get result
                result: ToolResult = await tc.run(name=tool_name, tool_input=tool_input)
                output_text = result.output if result.output is not None else ""
                # If output is too large, truncate and queue remainder
                max_tokens_allowed = token_manager.safe_max_tokens
                max_chars = max_tokens_allowed * 4
                leftover = None
                if isinstance(output_text, str) and len(output_text) > max_chars:
                    leftover = output_text[max_chars:]
                    output_text = output_text[:max_chars] + f"\n[... Output truncated, {len(leftover)} characters remaining]"
                # Account for tokens from this tool output (enforce rate limit before injecting to prompt)
                token_manager.consume_tokens(len(output_text) // 4 if isinstance(output_text, str) else 0)
                # Store leftover chunk for possible future retrieval (especially for file reading tools)
                if leftover:
                    if tool_name in ["read_file", "open_file", "cat", "view_file"]:
                        file_path = None
                        if isinstance(tool_input, dict):
                            file_path = tool_input.get("path") or tool_input.get("file_path") or tool_input.get("filename")
                        key = f"{tool_name}:{file_path or block.get('id')}"
                        token_manager.leftover_chunks[key] = leftover
                # Prepare tool_result block for conversation
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": output_text
                })
                # Immediately display the tool result output in the UI
                tool_output_callback(result, block["id"])
        # If any tool results were produced, append them as a user message so Claude can continue the conversation
        if tool_result_blocks:
            messages.append({"role": "user", "content": tool_result_blocks})
        return messages
    except (APIStatusError, APIResponseValidationError, APIError) as e:
        # Log API errors
        api_response_callback(getattr(e, "request", None), getattr(e, "response", None) or getattr(e, "body", None), e)
        return messages
    except Exception as e:
        # Log any other errors
        api_response_callback(None, None, e)
        return messages

