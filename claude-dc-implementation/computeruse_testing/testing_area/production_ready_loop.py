"""
Production-Ready Streaming Implementation for Claude DC

This module enhances Claude DC with streaming capabilities for a more responsive
user experience. It implements streaming with tool usage and maintains backward
compatibility with existing systems.
"""

import os
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast, Optional, Dict, List

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

# Import tools - using relative imports for production environment
from .tools import (
    TOOL_GROUPS_BY_VERSION,
    ToolCollection,
    ToolResult,
    ToolVersion,
)

# Get boolean environment variable with default value
def get_bool_env(name, default=False):
    """Parse boolean environment variables with proper error handling."""
    value = os.environ.get(name)
    if value is None:
        return default
    
    value = value.lower()
    if value in ('true', 't', 'yes', 'y', '1'):
        return True
    elif value in ('false', 'f', 'no', 'n', '0'):
        return False
    else:
        # Invalid value, log a warning
        print(f"Warning: Invalid boolean value for {name}: '{value}', using default: {default}")
        return default

# Feature flag for streaming (defaults to enabled, can be disabled if needed)
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# Original system prompt remains unchanged for compatibility
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open firefox, please just click on the firefox icon.  Note, firefox-esr is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""

# Tool input validation for safety
def validate_tool_input(tool_name, tool_input):
    """Validate and potentially fix tool inputs"""
    # Make a copy of the input to avoid modifying the original
    fixed_input = tool_input.copy() if tool_input else {}
    
    # Handle bash tool
    if tool_name.lower() == 'bash':
        if 'command' not in fixed_input or not fixed_input['command']:
            print(f"Warning: Bash tool called without a command, adding default")
            fixed_input['command'] = "echo 'Please specify a command'"
    
    # Handle computer tool
    elif tool_name.lower() == 'computer':
        if 'action' not in fixed_input or not fixed_input['action']:
            print(f"Warning: Computer tool called without an action, adding default")
            fixed_input['action'] = "screenshot"
        
        # Check for required coordinates for click actions
        if fixed_input.get('action') in ['left_click', 'right_click', 'mouse_move'] and 'coordinate' not in fixed_input:
            print(f"Warning: Computer tool {fixed_input.get('action')} called without coordinates, adding default")
            fixed_input['coordinate'] = [500, 400]  # Default to middle of screen
    
    # Handle str_replace_editor tool
    elif tool_name.lower() == 'str_replace_editor':
        if 'command' not in fixed_input:
            print(f"Warning: Editor tool called without a command, adding default")
            fixed_input['command'] = "view"
        
        if 'path' not in fixed_input:
            print(f"Warning: Editor tool called without a path, adding default")
            fixed_input['path'] = "/tmp/test.txt"
    
    return fixed_input

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
    Agentic sampling loop for Claude DC with streaming support.
    This is an enhanced version of the original sampling loop that adds support
    for token-by-token streaming for a more responsive user experience.
    """
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        # Process beta flags
        beta_flags = []
        if tool_group.beta_flag:
            beta_flags.append(tool_group.beta_flag)
        if token_efficient_tools_beta:
            beta_flags.append("token-efficient-tools-2025-02-19")
        
        # Initialize API provider client
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key, max_retries=4)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        else:
            client = Anthropic(api_key=api_key, max_retries=4)

        # Apply image truncation if specified
        image_truncation_threshold = only_n_most_recent_images or 0
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )
            
        # Set up API parameters
        api_params = {
            "max_tokens": max_tokens,
            "messages": messages,
            "model": model,
            "system": [system],
            "tools": tool_collection.to_params(),
        }
        
        # Add beta flags if any
        if beta_flags:
            try:
                api_params["beta"] = beta_flags
            except Exception as e:
                print(f"Warning: Failed to add beta flags: {e}")
        
        # Add thinking budget if specified
        if thinking_budget:
            try:
                api_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
            except Exception as e:
                print(f"Warning: Failed to add thinking budget: {e}")
        
        # Enable streaming if the feature flag is set
        if ENABLE_STREAMING:
            api_params["stream"] = True
            print(f"Streaming enabled for improved responsiveness")
            
            # Make the API call with streaming
            try:
                try:
                    # Try with all parameters
                    stream = client.messages.create(**api_params)
                    
                    # Process the stream
                    response_blocks = []
                    current_block = None
                    current_index = None
                    
                    for event in stream:
                        if hasattr(event, "type"):
                            event_type = event.type
                            
                            if event_type == "content_block_start":
                                # New content block
                                if hasattr(event.content_block, "type"):
                                    block_type = event.content_block.type
                                    
                                    # Create content block based on type
                                    if block_type == "text":
                                        current_block = BetaTextBlockParam(
                                            type="text",
                                            text=getattr(event.content_block, "text", "")
                                        )
                                    elif block_type == "tool_use":
                                        # Handle tool use block
                                        current_block = {
                                            "type": "tool_use",
                                            "name": getattr(event.content_block, "name", ""),
                                            "input": getattr(event.content_block, "input", {}),
                                            "id": getattr(event.content_block, "id", ""),
                                        }
                                    elif block_type == "thinking":
                                        # Handle thinking block
                                        current_block = {
                                            "type": "thinking",
                                            "thinking": getattr(event.content_block, "thinking", ""),
                                        }
                                    else:
                                        # Unknown block type
                                        current_block = {"type": block_type}
                                else:
                                    # Fallback for blocks without type
                                    current_block = {"type": "unknown"}
                                
                                # Add block to list and send to callback
                                response_blocks.append(current_block)
                                current_index = len(response_blocks) - 1
                                output_callback(current_block)
                                
                            elif event_type == "content_block_delta":
                                # Handle deltas
                                if hasattr(event, "index") and event.index < len(response_blocks):
                                    current_index = event.index
                                    current_block = response_blocks[current_index]
                                    
                                    # Handle text delta
                                    if hasattr(event.delta, "text") and event.delta.text:
                                        delta_text = event.delta.text
                                        
                                        # Update current block
                                        if current_block["type"] == "text":
                                            current_block["text"] += delta_text
                                        
                                        # Create delta for callback
                                        delta_block = {
                                            "type": "text",
                                            "text": delta_text,
                                            "is_delta": True,
                                        }
                                        
                                        # Send to callback
                                        output_callback(delta_block)
                                    
                                    # Handle thinking delta
                                    elif hasattr(event.delta, "thinking") and event.delta.thinking:
                                        delta_thinking = event.delta.thinking
                                        
                                        # Update current block
                                        if current_block["type"] == "thinking":
                                            current_block["thinking"] += delta_thinking
                                        
                                        # Create delta for callback
                                        delta_block = {
                                            "type": "thinking",
                                            "thinking": delta_thinking,
                                            "is_delta": True,
                                        }
                                        
                                        # Send to callback
                                        output_callback(delta_block)
                                
                            elif event_type == "message_stop":
                                # Message complete
                                print("Message generation complete")
                                break
                    
                    # Create a response object in the expected format
                    response = BetaMessage(
                        id="streaming_msg",
                        role="assistant",
                        model=model,
                        content=response_blocks,
                        stop_reason="end_turn",
                        type="message",
                    )
                                    
                except (TypeError, ValueError) as e:
                    # Handle API parameter errors by falling back to non-streaming
                    print(f"Streaming API error: {e}, falling back to non-streaming")
                    api_params["stream"] = False
                    response = client.messages.create(**api_params)
                
            except (APIStatusError, APIResponseValidationError, APIError) as e:
                # Handle API errors
                api_response_callback(getattr(e, "request", None), getattr(e, "response", None), e)
                return messages
            except Exception as e:
                # Handle unexpected errors
                api_response_callback(None, None, e)
                return messages
            
        else:
            # Non-streaming path (standard implementation)
            try:
                # Use standard with_raw_response pattern for non-streaming
                raw_response = client.beta.messages.with_raw_response.create(**api_params)
                api_response_callback(
                    raw_response.http_response.request, raw_response.http_response, None
                )
                response = raw_response.parse()
            except (APIStatusError, APIResponseValidationError) as e:
                api_response_callback(e.request, e.response, e)
                return messages
            except APIError as e:
                api_response_callback(e.request, e.body, e)
                return messages
            except Exception as e:
                api_response_callback(None, None, e)
                return messages

        # Process the response in a way compatible with both streaming and non-streaming
        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        # Process tool usage
        tool_result_content = []
        for content_block in response_params:
            # Skip if already processed via callback in streaming mode
            if not ENABLE_STREAMING:
                output_callback(content_block)
                
            if content_block["type"] == "tool_use":
                # Extract tool information
                tool_name = content_block["name"]
                tool_id = content_block["id"]
                tool_input = content_block["input"]
                
                # Validate and fix tool input if needed
                validated_input = validate_tool_input(tool_name, cast(dict[str, Any], tool_input))
                if validated_input != tool_input:
                    print(f"Fixed tool input for {tool_name}")
                    tool_input = validated_input
                
                # Run the tool with error handling
                try:
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=cast(dict[str, Any], tool_input),
                    )
                    
                    # Process the result
                    tool_result_content.append(
                        _make_api_tool_result(result, content_block["id"])
                    )
                    tool_output_callback(result, content_block["id"])
                except Exception as e:
                    # Handle tool execution errors
                    print(f"Tool execution error: {e}")
                    error_result = ToolResult(error=str(e))
                    tool_result_content.append(
                        _make_api_tool_result(error_result, content_block["id"])
                    )
                    tool_output_callback(error_result, content_block["id"])

        # If no tools were used, we're done
        if not tool_result_content:
            return messages

        # Add tool results to messages
        messages.append({"content": tool_result_content, "role": "user"})

# Helper functions unchanged from original implementation

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
    return res

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
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