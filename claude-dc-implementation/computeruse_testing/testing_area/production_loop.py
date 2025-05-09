"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
Enhanced with streaming support for improved user experience.
"""

import os
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast, Optional

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

# Import tools - use absolute import for testing
try:
    # Try local import first (for production)
    from .tools import (
        TOOL_GROUPS_BY_VERSION,
        ToolCollection,
        ToolResult,
        ToolVersion,
    )
except ImportError:
    # Fall back to absolute import (for testing)
    from tools import (
        TOOL_GROUPS_BY_VERSION,
        ToolCollection,
        ToolResult,
        ToolVersion,
    )

# Constants
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

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

# Feature flag for streaming (defaults to enabled)
ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# This system prompt is optimized for the Docker environment in this repository and
# specific tool combinations enabled.
# We encourage modifying this system prompt to ensure the model has context for the
# environment it is running in, and to provide any additional information that may be
# helpful for the task at hand.
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
    Agentic sampling loop for the assistant/tool interaction of computer use.
    Enhanced with streaming support for improved user experience.
    """
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    system = BetaTextBlockParam(
        type="text",
        text=f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}",
    )

    while True:
        # Initialize beta flags and parameters
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
        extra_body = {}
        if thinking_budget:
            # Ensure we only send the required fields for thinking
            extra_body = {
                "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
            }
        
        # Set up streaming parameter if enabled
        api_params = {
            "max_tokens": max_tokens,
            "messages": messages,
            "model": model,
            "system": [system],
            "tools": tool_collection.to_params(),
            "beta": beta_flags if beta_flags else None,
            "extra_body": extra_body if extra_body else None,
        }
        
        # Add streaming if enabled
        if ENABLE_STREAMING:
            api_params["stream"] = True
            print(f"Streaming enabled for improved responsiveness")
        
        # Clean up params by removing None values
        api_params = {k: v for k, v in api_params.items() if v is not None}
        
        try:
            # Try to make the API call
            try:
                if ENABLE_STREAMING:
                    # Streaming path - process token by token
                    print(f"Making streaming API call")
                    # Direct streaming for SDK compatibility
                    api_params["stream"] = True
                    stream = client.messages.create(**api_params)
                    
                    # Call API response callback
                    api_response_callback(None, None, None)
                    
                    # Process stream events
                    content_blocks = []
                    
                    # Track current streaming context
                    current_block_index = None
                    
                    # Process the streaming events
                    for event in stream:
                        if hasattr(event, "type"):
                            event_type = event.type
                            
                            if event_type == "content_block_start":
                                # New content block started
                                current_block = event.content_block
                                content_blocks.append(current_block)
                                current_block_index = len(content_blocks) - 1
                                
                                # Convert block to params for callback
                                if hasattr(current_block, "model_dump"):
                                    block_dict = current_block.model_dump()
                                else:
                                    # Fallback for older SDK versions
                                    block_dict = {"type": getattr(current_block, "type", "unknown")}
                                    
                                    if hasattr(current_block, "text"):
                                        block_dict["text"] = current_block.text
                                    elif hasattr(current_block, "thinking"):
                                        block_dict["thinking"] = current_block.thinking
                                    elif hasattr(current_block, "name") and getattr(current_block, "type", None) == "tool_use":
                                        block_dict["name"] = current_block.name
                                        block_dict["input"] = getattr(current_block, "input", {})
                                        block_dict["id"] = getattr(current_block, "id", "unknown")
                                
                                # Send to callback
                                output_callback(block_dict)
                                
                            elif event_type == "content_block_delta":
                                # Content block delta received
                                if hasattr(event, "index") and event.index < len(content_blocks):
                                    current_block_index = event.index
                                    
                                    # Handle text delta
                                    if hasattr(event.delta, "text") and event.delta.text:
                                        # Update block with delta
                                        if hasattr(content_blocks[current_block_index], "text"):
                                            content_blocks[current_block_index].text += event.delta.text
                                        else:
                                            content_blocks[current_block_index].text = event.delta.text
                                            
                                        # Create delta block for callback
                                        delta_block = {
                                            "type": "text",
                                            "text": event.delta.text,
                                            "is_delta": True,
                                        }
                                        
                                        # Send to callback
                                        output_callback(delta_block)
                                        
                                    # Handle thinking delta
                                    elif hasattr(event.delta, "thinking") and event.delta.thinking:
                                        # Update block with delta
                                        if hasattr(content_blocks[current_block_index], "thinking"):
                                            content_blocks[current_block_index].thinking += event.delta.thinking
                                        else:
                                            content_blocks[current_block_index].thinking = event.delta.thinking
                                            
                                        # Create delta block for callback
                                        delta_block = {
                                            "type": "thinking",
                                            "thinking": event.delta.thinking,
                                            "is_delta": True,
                                        }
                                        
                                        # Send to callback
                                        output_callback(delta_block)
                            
                            elif event_type == "message_stop":
                                # Message generation complete
                                print("Message generation complete")
                                break
                        
                    # Create response in the expected format
                    response = BetaMessage(
                        id="streaming_msg",
                        role="assistant",
                        model=model,
                        content=content_blocks,
                        stop_reason="end_turn",
                        type="message",
                    )
                    
                else:
                    # Non-streaming path - traditional API call
                    print(f"Making non-streaming API call")
                    api_params["stream"] = False
                    response = client.messages.create(**api_params)
                    api_response_callback(None, None, None)
                    
            except TypeError as e:
                # Handle parameter errors
                print(f"API parameter error: {e}")
                if "beta" in str(e):
                    # Try without beta flags
                    api_params.pop("beta", None)
                    print("Retrying without beta flags")
                    
                    if ENABLE_STREAMING:
                        raw_stream = client.beta.messages.with_raw_response.stream(**api_params)
                        # Process stream similar to above, omitted for brevity
                    else:
                        raw_response = client.beta.messages.with_raw_response.create(**api_params)
                        api_response_callback(
                            raw_response.http_response.request, raw_response.http_response, None
                        )
                        response = raw_response.parse()
                else:
                    # Other TypeError, re-raise
                    raise
                
        except (APIStatusError, APIResponseValidationError) as e:
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            api_response_callback(e.request, e.body, e)
            return messages
        except Exception as e:
            api_response_callback(None, None, e)
            return messages

        # Convert the response to the expected format
        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        # Process any tool usage
        tool_result_content = []
        for content_block in response_params:
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
                
                # Run the tool
                try:
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=cast(dict[str, Any], tool_input),
                    )
                    
                    # Process tool result
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

        # If no tool was used, we're done
        if not tool_result_content:
            return messages

        # Add tool results to conversation
        messages.append({"content": tool_result_content, "role": "user"})

# Helper functions below, largely unchanged from original implementation

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