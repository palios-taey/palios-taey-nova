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
    ToolResult,
    ToolVersion,
    ToolFailure,
)

PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# Base system prompt (capabilities and guidelines for the virtual machine environment)
SYSTEM_PROMPT = """<SYSTEM_CAPABILITY>
* You are utilizing an Ubuntu virtual machine on a {} architecture with internet access.
* You can install applications with your bash tool. Use curl instead of wget.
* To open Firefox, click the Firefox icon (note: firefox-esr is installed).
* GUI apps run with the bash tool will appear in the desktop environment (set DISPLAY=:1 and run in background).
* For very large command outputs, redirect to a file and use grep or open in the editor rather than dumping entire output.
* When viewing a page, you may need to scroll or zoom out to see all content.
* Computer function calls can take time; consider batching multiple actions into one call when feasible.
* The current date is {}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* If Firefox shows a startup wizard, ignore it and directly use the address bar to enter URLs or search terms.
* If viewing a PDF, take a screenshot of relevant sections rather than trying to read the entire PDF via screenshots.
</IMPORTANT>
""".format(platform.machine(), datetime.today().strftime('%A, %B %-d, %Y'))

async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request, httpx.Response | object | None, Exception | None], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        enable_prompt_caching = False
        betas = []
        # Add tool beta flag if present
        if tool_group.beta_flag:
            betas.append(tool_group.beta_flag)
        
        # Removed token_efficient_tools_beta as it conflicts with streaming
        
        image_truncation_threshold = only_n_most_recent_images or 0
        
        # Initialize the appropriate client based on provider
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
            # Because cached reads are 10% of the price, we don't think it's
            # ever sensible to break the cache by truncating images
            only_n_most_recent_images = 0
            # Use type ignore to bypass TypedDict check until SDK types are updated
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore

        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )
        
        # Prepare extra parameters for thinking if enabled
        extra_body = {}
        if thinking_budget:
            extra_body = {
                "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
            }

        # Create a mock request for reporting API info
        mock_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        
        try:
            # Use streaming for better UX and to preserve thinking notes
            stream = client.beta.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=[system],
                tools=tool_collection.to_params(),
                betas=betas,
                extra_body=extra_body,
                stream=True,  # Enable streaming
            )
            
            # Process the stream
            content_blocks = []
            
            # Track the current stream state
            for event in stream:
                # Process different event types
                if hasattr(event, "type"):
                    # New content block started
                    if event.type == "content_block_start":
                        if hasattr(event, "content_block"):
                            current_block = event.content_block
                            content_blocks.append(current_block)
                            output_callback(current_block)
                    
                    # Content block delta (incremental updates)
                    elif event.type == "content_block_delta":
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Handle thinking delta
                            if hasattr(event.delta, "thinking") and event.delta.thinking:
                                if hasattr(content_blocks[event.index], "thinking"):
                                    content_blocks[event.index].thinking += event.delta.thinking
                                else:
                                    content_blocks[event.index].thinking = event.delta.thinking
                                
                                # Create a delta block to send to output callback
                                delta_block = {
                                    "type": "thinking",
                                    "thinking": event.delta.thinking,
                                    "is_delta": True,
                                }
                                output_callback(delta_block)
                            
                            # Handle text delta
                            elif hasattr(event.delta, "text") and event.delta.text:
                                if hasattr(content_blocks[event.index], "text"):
                                    content_blocks[event.index].text += event.delta.text
                                else:
                                    content_blocks[event.index].text = event.delta.text
                                    
                                delta_block = {
                                    "type": "text",
                                    "text": event.delta.text,
                                    "is_delta": True,
                                }
                                output_callback(delta_block)
                    
                    # Message generation complete
                    elif event.type == "message_stop":
                        break
            
            # Create response structure
            response = BetaMessage(
                id="",
                role="assistant",
                model=model,
                content=content_blocks,
                stop_reason="end_turn" if not any(block.type == "tool_use" for block in content_blocks if hasattr(block, "type")) else "tool_use",
                type="message",
                usage={"input_tokens": 0, "output_tokens": 0},
            )
            
            api_response_callback(mock_request, None, None)
            
        except (APIStatusError, APIResponseValidationError) as e:
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            api_response_callback(e.request, e.body, e)
            return messages
        except Exception as e:
            api_response_callback(mock_request, None, e)
            return messages

        # Convert to params for next message
        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        # Handle tool usage in the response
        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                result = await tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block["id"])
                )
                tool_output_callback(result, content_block["id"])

        if not tool_result_content:
            return messages
        messages.append({"content": tool_result_content, "role": "user"})
