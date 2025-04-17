import platform
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast, Optional, List, Dict

import httpx
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

from .tools import (
    TOOL_GROUPS_BY_VERSION,
    ToolCollection,
    ToolVersion,
)
from .types import APIProvider, ToolResult
from .token_manager import token_manager

PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open firefox, please just click on the firefox icon.  Note, firefox-esr is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)".
  GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""

def _inject_prompt_caching(messages: list[BetaMessageParam]):
    """
    Set cache breakpoints for the 3 most recent user turns.
    """
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance((content := message["content"]), list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam({"type": "ephemeral"})  # type: ignore
            else:
                content[-1].pop("cache_control", None)
                break

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    """Convert a ToolResult object into a ToolResultBlockParam for the API."""
    is_error = False
    if result.error:
        is_error = True
        tool_result_content: str = result.error
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
    output_callback: Callable[[str], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[httpx.Request, httpx.Response | object | None, Exception | None], None],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
) -> list[BetaMessageParam]:
    """
    Agentic sampling loop for assistant/tool interaction with streaming support.
    """
    tool_group = TOOL_GROUPS_BY_VERSION.get(str(tool_version), None)
    if tool_group is None:
        raise ValueError(f"Unknown tool_version: {tool_version}")
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
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
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
            enable_prompt_caching = True
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        if enable_prompt_caching:
            betas.append(PROMPT_CACHING_BETA_FLAG)
            _inject_prompt_caching(messages)
            # Disable image truncation when prompt caching to maximize cache hits
            only_n_most_recent_images = 0
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore

        if only_n_most_recent_images:
            # Optionally filter older images from context (if configured)
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )
        extra_body: Dict[str, Any] = {}
        if thinking_budget:
            extra_body = {
                "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
            }

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
            # Fallback: rough estimate based on text length
            all_text = ""
            for msg in messages:
                if isinstance(msg["content"], str):
                    all_text += msg["content"]
                elif isinstance(msg["content"], list):
                    for block in msg["content"]:
                        if isinstance(block, dict) and "text" in block:
                            all_text += block["text"]
            estimated_input_tokens = max(1, (len(all_text) // 4))
        estimated_output_tokens = max_tokens
        token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)

        # Call Claude API with streaming
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
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            api_response_callback(e.request, e.body, e)
            return messages

        assistant_text = ""
        tool_event: Optional[BetaToolUseBlockParam] = None
        # Iterate over streaming events
        for event in stream_response:
            if hasattr(event, "type") and (getattr(event, "type") == "tool" or getattr(event, "type") == "tool_use"):
                tool_event = event
                break
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                chunk_text = event.delta.text
                assistant_text += str(chunk_text)
                output_callback(chunk_text)
        # If a tool was requested by Claude
        if tool_event:
            content_blocks: List[BetaContentBlockParam] = []
            if assistant_text:
                content_blocks.append(BetaTextBlockParam(type="text", text=assistant_text))
            # Convert tool_event to a serializable dict (tool_use block)
            if isinstance(tool_event, dict):
                tool_use_block = tool_event
            else:
                tool_use_block = tool_event.model_dump() if callable(getattr(tool_event, "model_dump", None)) else tool_event.__dict__
            tool_use_block_param = tool_use_block  # dict representing the tool_use
            content_blocks.append(tool_use_block_param)
            # Append assistant message with tool request to history
            messages.append({"role": "assistant", "content": content_blocks})
            # Execute the requested tool
            tool_name = tool_use_block_param.get("tool") or tool_use_block_param.get("name") or tool_use_block_param.get("tool_name")
            tool_input = tool_use_block_param.get("input") or {}
            result = await tool_collection.run(name=tool_name, tool_input=cast(dict[str, Any], tool_input))
            # Prepare tool result block and append as user message
            tool_result_block = _make_api_tool_result(result, tool_use_block_param.get("id"))
            messages.append({"role": "user", "content": [tool_result_block]})
            # Notify UI/CLI via callback
            tool_output_callback(result, tool_use_block_param.get("id"))
            # Continue loop to send tool result to Claude for the next response
            continue
        else:
            # No tool was used, final assistant answer obtained
            if assistant_text:
                messages.append({"role": "assistant", "content": [BetaTextBlockParam(type="text", text=assistant_text)]})
            # Update token usage statistics
            output_tokens = 0
            if "ENCODING" in globals() and callable(globals().get("ENCODING", None)):
                # If tiktoken is available and ENCODING defined
                try:
                    output_tokens = len(ENCODING.encode(assistant_text))  # type: ignore
                except Exception:
                    output_tokens = max(1, (len(assistant_text) // 4))
            else:
                output_tokens = max(1, (len(assistant_text) // 4))
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
    Remove all but the final `images_to_keep` tool_result images from the conversation history.
    This helps reduce prompt size while preserving recent screenshots.
    """
    if images_to_keep is None:
        return messages

    # Gather all tool_result blocks from conversation
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
    # Remove in multiples of min_removal_threshold for better cache behavior
    images_to_remove -= images_to_remove % (min_removal_threshold or 1)

    for tool_result in tool_result_blocks:
        contents = tool_result.get("content")
        if isinstance(contents, list):
            new_content = []
            for block in contents:
                if isinstance(block, dict) and block.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue  # skip this image (remove it)
                new_content.append(block)
            tool_result["content"] = new_content

