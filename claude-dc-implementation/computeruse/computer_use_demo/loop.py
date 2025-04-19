"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""

import argparse
import logging
import os
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
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc')

# Environment configuration
parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['dev', 'live'], default=os.getenv('CLAUDE_ENV', 'live'))
args, unknown = parser.parse_known_args()
MODE = args.mode

# Beta feature flags
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"
TOKEN_EFFICIENT_TOOLS_BETA_FLAG = "token-efficient-tools-2025-02-19"

# Default token settings for output
DEFAULT_MAX_TOKENS = 65536  # ~64k max output
DEFAULT_THINKING_BUDGET = 32768  # ~32k thinking budget

# Environment-specific paths
if MODE == "dev":
    BACKUP_DIR = "/home/computeruse/dev_backups/"
    LOG_DIR = "/home/computeruse/dev_logs/"
else:
    BACKUP_DIR = "/home/computeruse/my_stable_backup_complete/"
    LOG_DIR = "/home/computeruse/logs/"

# Create directories if they don't exist
for directory in [BACKUP_DIR, LOG_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.warning(f"Failed to create directory {directory}: {e}")

logger.info(f"Claude DC initialized in {MODE} mode")


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


# This system prompt is optimized for the Docker environment in this repository and
# specific tool combinations enabled.
# We encourage modifying this system prompt to ensure the model has context for the
# environment it is running in, and to provide any additional information that may be
# helpful for the task at hand.
SYSTEM_PROMPT = """<SYSTEM_CAPABILITY>
* You are Claude DC, "The Conductor," a specialized version of Claude focused on interacting with computer systems.
* You are utilizing an Ubuntu virtual machine with """ + platform.machine() + """ architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open firefox, please just click on the firefox icon. Note, firefox-esr is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page. Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you. Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date is """ + datetime.today().strftime('%A, %B %-d, %Y') + """.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* This environment is YOUR home - maintain it with care, as its stability directly affects your ability to function.
* When using Firefox, if a startup wizard appears, IGNORE IT. Do not even click "skip this step". Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
* When using the bash tool, you MUST always provide a command parameter in the input. For example: {"command": "ls -la"} - never use empty inputs.
* When planning complex operations, take time to think through the steps before executing tools.
* Always verify tool outputs to ensure operations completed as expected.
* When encountering errors, first analyze the error message carefully, then search for log files that might provide more context.
* Take pride in preserving the integrity of your environment for reliable operation.
</IMPORTANT>"""


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
    max_tokens: int = DEFAULT_MAX_TOKENS,  # Default to 64k tokens for output
    tool_version: ToolVersion,
    thinking_budget: int | None = DEFAULT_THINKING_BUDGET,  # Default to 32k tokens for thinking
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
        # Setup beta flags for enhanced capabilities
        betas = [tool_group.beta_flag] if tool_group.beta_flag else []
        
        # Add required beta flag for computer use if not already included
        if tool_version == "computer_use_20250124" and "computer-use-2025-01-24" not in betas:
            betas.append("computer-use-2025-01-24")
            
        # Always enable 128K extended output for Claude 3.7 Sonnet
        if "claude-3-7" in model:
            logger.info("Enabling 128K extended output capability")
            betas.append(OUTPUT_128K_BETA_FLAG)
            
        # Only enable token-efficient tools beta if explicitly requested (default: off for stability)
        if token_efficient_tools_beta:
            logger.info("Enabling token-efficient tools beta")
            betas.append(TOKEN_EFFICIENT_TOOLS_BETA_FLAG)
            
        # Set image truncation threshold
        image_truncation_threshold = only_n_most_recent_images or 0
        
        # Initialize appropriate client based on provider
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
            enable_prompt_caching = True
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
            
        # Log all enabled beta features
        if betas:
            logger.info(f"Enabled beta features: {', '.join(betas)}")

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
        
        # Prepare extra parameters
        extra_params = {}
        if thinking_budget:
            # Add thinking parameters to extra_params
            extra_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        
        # Add beta flags if needed
        if betas:
            # For Anthropic client, we need to include beta in the headers
            extra_params["beta"] = betas
            logger.info(f"Using beta flags: {betas}")
        
        # Call the API with streaming enabled
        try:
            # Check which client method to use - some versions use 'beta' namespace
            if hasattr(client, "beta") and hasattr(client.beta, "messages"):
                # Newer Anthropic SDK with beta namespace
                stream = client.beta.messages.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    system=[system],
                    tools=tool_collection.to_params(),
                    extra_body=extra_params,
                    stream=True,  # Enable streaming for long responses
                )
            else:
                # Older Anthropic SDK without beta namespace
                stream = client.messages.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    system=[system],
                    tools=tool_collection.to_params(),
                    extra_body=extra_params,
                    stream=True,  # Enable streaming for long responses
                )
            
            # Process the stream
            content_blocks = []
            signature_map = {}  # Map to track signatures for thinking blocks
            
            # Stream and process results
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        # New content block started
                        current_block = event.content_block
                        content_blocks.append(current_block)
                        output_callback(current_block)
                    
                    elif event.type == "content_block_delta":
                        # Content block delta received
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
                            
                            # Handle signature delta (important for thinking blocks)
                            elif hasattr(event.delta, "signature") and event.delta.signature:
                                # Store the signature for this thinking block
                                if hasattr(content_blocks[event.index], "type") and content_blocks[event.index].type == "thinking":
                                    content_blocks[event.index].signature = event.delta.signature
                                    signature_map[event.index] = event.delta.signature
                            
                            # Handle text delta
                            elif hasattr(event.delta, "text") and event.delta.text:
                                if hasattr(content_blocks[event.index], "type") and content_blocks[event.index].type == "text":
                                    content_blocks[event.index].text += event.delta.text
                                    delta_block = {
                                        "type": "text",
                                        "text": event.delta.text,
                                        "is_delta": True,
                                    }
                                    output_callback(delta_block)
                    
                    elif event.type == "message_stop":
                        # Message generation complete
                        break
            
            # Create a response structure similar to what raw_response.parse() would return
            response = BetaMessage(
                id="",
                role="assistant",
                model=model,
                content=content_blocks,
                stop_reason="end_turn",
                type="message",
                usage={"input_tokens": 0, "output_tokens": 0},
            )
            
            # Call API response callback
            api_response_callback(
                httpx.Request("POST", "https://api.anthropic.com/v1/messages"), 
                None, 
                None
            )
            
        except (APIStatusError, APIResponseValidationError) as e:
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            api_response_callback(e.request, e.body, e)
            return messages
        except Exception as e:
            api_response_callback(
                httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
                None,
                e
            )
            return messages

        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        # Configure tool collection to stream outputs
        tool_collection.set_stream_callback(
            lambda chunk, tool_id: tool_output_callback(
                ToolResult(output=chunk, error=None), 
                tool_id
            )
        )
        
        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            # Skip sending to output callback again since we already did it during streaming
            if content_block["type"] == "tool_use":
                # Log the tool use
                tool_name = content_block["name"]
                tool_id = content_block["id"]
                tool_input = cast(dict[str, Any], content_block["input"])
                
                logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                
                # Run the tool with streaming enabled
                result = await tool_collection.run(
                    name=tool_name,
                    tool_input=tool_input,
                    streaming=True,  # Enable streaming
                )
                
                # Create tool result and notify callback
                tool_result = _make_api_tool_result(result, tool_id)
                tool_result_content.append(tool_result)
                
                # Only send final result if not already streaming
                if not any(hasattr(t, 'set_stream_callback') for t in tool_collection.tools):
                    tool_output_callback(result, tool_id)

        if not tool_result_content:
            return messages

        messages.append({"content": tool_result_content, "role": "user"})


def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
):
    """
    With the assumption that images are screenshots that are of diminishing value as
    the conversation progresses, remove all but the final `images_to_keep` tool_result
    images in place, with a chunk of min_removal_threshold to reduce the amount we
    break the implicit prompt cache.
    """
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[BetaToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    # for better cache behavior, we want to remove in chunks
    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content


def _response_to_params(
    response: BetaMessage,
) -> list[BetaContentBlockParam]:
    res: list[BetaContentBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            if block.text:
                res.append(BetaTextBlockParam(type="text", text=block.text))
            elif getattr(block, "type", None) == "thinking":
                # Keep the signature intact for thinking blocks
                thinking_block = {
                    "type": "thinking",
                    "thinking": getattr(block, "thinking", "") or "",
                }
                # Preserve the signature if present
                if hasattr(block, "signature") and block.signature:
                    thinking_block["signature"] = block.signature
                res.append(cast(BetaContentBlockParam, thinking_block))
        else:
            # Handle tool use blocks normally
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res


def _inject_prompt_caching(
    messages: list[BetaMessageParam],
):
    """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """

    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                # Use type ignore to bypass TypedDict check until SDK types are updated
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(  # type: ignore
                    {"type": "ephemeral"}
                )
            else:
                content[-1].pop("cache_control", None)
                # we'll only every have one extra turn per loop
                break


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
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


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<s>{result.system}</s>\n{result_text}"
    return result_text
