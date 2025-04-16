import sys; sys.path.insert(0, "/home/computeruse")
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, Union, Optional, List, Dict

import httpx
from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIError, APIResponseValidationError, APIStatusError
from anthropic.types.beta import BetaCacheControlEphemeralParam, BetaContentBlockParam, BetaImageBlockParam, BetaMessage, BetaMessageParam, BetaTextBlock, BetaTextBlockParam, BetaToolResultBlockParam, BetaToolUseBlockParam

from computer_use_demo.tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolResult, ToolVersion
from token_manager import token_manager
# Import safe file operations to intercept file I/O for tools
import builtins
from pathlib import Path
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    ENCODING = tiktoken.get_encoding("cl100k_base")
except ImportError:
    TIKTOKEN_AVAILABLE = False
CHUNK_TOKEN_LIMIT = 15000  # max tokens per chunk for file and command outputs

PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

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
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to find a summary in it, then it's better to ask the user for permission to open the file directly instead of screenshotting every page.
</IMPORTANT>
"""

# Monkey-patch builtins.open to intercept large file reads
_original_open = builtins.open
class _InterceptedFile:
    def __init__(self, file_obj, path: str):
        self.file = file_obj
        self.path = path
        self.remaining_data = None
    def read(self, size: int = -1) -> str:
        # Improved handling of both string and bytes data
        data = self.file.read(size)
        # Check if data is bytes or string
        if isinstance(data, bytes):
            try:
                # Try to decode bytes to string first
                decoded_data = data.decode('utf-8', errors='replace')
                token_count = len(ENCODING.encode(decoded_data))
            except (UnicodeDecodeError, AttributeError):
                # If decoding fails, use a rough estimate based on byte length
                token_count = max(1, len(data) // 4)  # Rough estimate
        else:
            # If it's already a string
            token_count = len(ENCODING.encode(data))
        else:
            token_count = max(1, (len(data) // 4))
        if token_count > CHUNK_TOKEN_LIMIT:
            # Truncate data to chunk limit and store remainder
            if TIKTOKEN_AVAILABLE:
                tokens = ENCODING.encode(data)
                partial_tokens = tokens[:CHUNK_TOKEN_LIMIT]
                partial_data = ENCODING.decode(partial_tokens)
                remainder_tokens = tokens[CHUNK_TOKEN_LIMIT:]
                remainder_data = ENCODING.decode(remainder_tokens) if remainder_tokens else ""
            else:
                # approximate characters for chunk
                approx_chars = CHUNK_TOKEN_LIMIT * 4
                partial_data = data[:approx_chars]
                remainder_data = data[approx_chars:]
            self.remaining_data = remainder_data
            data = partial_data
        return data
    def __iter__(self):
        # allow iteration over lines
        return iter(self.file)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False
    def close(self):
        self.file.close()
builtins.open = lambda path, mode='r', *args, **kwargs: _InterceptedFile(_original_open(path, mode, *args, **kwargs), path) if 'r' in mode else _original_open(path, mode, *args, **kwargs)

def _inject_prompt_caching(messages: list[BetaMessageParam]):
    """
    Set cache breakpoints for the 3 most recent turns.
    """
    breakpoints_remaining = 3
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(content := message["content"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam({"type": "ephemeral"})  # type: ignore
            else:
                content[-1].pop("cache_control", None)
                break

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = result.error
    else:
        if result.output:
            tool_result_content.append(
                {"type": "text", "text": result.output}
            )
        if getattr(result, "base64_image", None):
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

async def sampling_loop(
    system_prompt_suffix: str,
    model: str,
    provider: APIProvider,
    messages: list[BetaMessageParam],
    output_callback: Callable[[str], None],
    tool_output_callback: Callable[[str, ToolResult], None],
    api_response_callback: Callable[[Any, Any, Optional[Exception]], None],
    api_key: Optional[str],
    only_n_most_recent_images: int,
    tool_version: Union[ToolVersion, str],
    max_tokens: int,
    thinking_budget: Optional[int],
    token_efficient_tools_beta: bool,
) -> list[BetaMessageParam]:
    tool_group = TOOL_GROUPS_BY_VERSION.get(str(tool_version), None)
    if tool_group is None:
        raise ValueError(f"Unknown tool_version: {tool_version}")
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    system_prompt = SYSTEM_PROMPT + ((" " + system_prompt_suffix) if system_prompt_suffix else "")
    system = BetaTextBlockParam(type="text", text=system_prompt)

    while True:
        enable_prompt_caching = False
        betas: List[str] = []
        if tool_group.beta_flag:
            betas.append(tool_group.beta_flag)
        if token_efficient_tools_beta:
            betas.append("token-efficient-tools-2025-02-19")
        # Add extended output beta flag
        betas.append("output-128k-2025-02-19")
        image_truncation_threshold = only_n_most_recent_images or 0
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key or "", max_retries=4)
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
            only_n_most_recent_images = 0
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore
        if only_n_most_recent_images:
            # Optionally filter older images from context (not fully implemented here)
            pass
        extra_body = {}
        if thinking_budget:
            extra_body = {
                "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
            }

        # Estimate token usage for this request and apply rate limiting
        estimated_input_tokens = 0
        try:
            count_resp = client.beta.messages.count_tokens(model=model, messages=messages, system=[system], tools=tool_collection.to_params(), betas=betas, extra_body=extra_body)
            estimated_input_tokens = getattr(count_resp, "input_tokens", 0)
        except Exception:
            # Fallback to rough estimation
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
            api_response_callback(e.request, getattr(e, 'response', None), e)
            return messages
        except APIError as e:
            api_response_callback(e.request, getattr(e, 'body', None), e)
            return messages

        assistant_text = ""
        tool_event = None
        # Iterate over streaming events
        for event in stream_response:
            if hasattr(event, "type") and (getattr(event, "type") == "tool" or getattr(event, "type") == "tool_use"):
                tool_event = event
                break
            # Handle content delta events
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                chunk_text = event.delta.text
                assistant_text += str(chunk_text)
                output_callback(chunk_text)
        # If a tool was requested by Claude
        if tool_event:
            content_blocks: List[BetaContentBlockParam] = []
            if assistant_text:
                content_blocks.append(BetaTextBlockParam(type="text", text=assistant_text))
            # Convert tool_event to param dict
            if isinstance(tool_event, dict):
                tool_use_block = tool_event
            else:
                tool_use_block = tool_event.model_dump() if callable(getattr(tool_event, "model_dump", None)) else tool_event.__dict__
            tool_use_block_param = tool_use_block  # dict with type "tool_use"
            content_blocks.append(tool_use_block_param)
            # Append assistant message with tool request to history
            messages.append({"role": "assistant", "content": content_blocks})
            # Execute the requested tool
            tool_name = tool_use_block_param.get("tool", tool_use_block_param.get("tool_name"))
            tool_input = tool_use_block_param.get("input") or ""
            result_text = ""
            is_error = False
            if tool_name in ["bash", "BashTool", "bash_tool", "bash_tool_20250124"]:
                # Run bash command
                try:
                    proc = httpx.run(tool_input, shell=True, capture_output=True, text=True, timeout=30)
                    result_text = proc.stdout if proc.stdout else proc.stderr
                except Exception as exc:
                    result_text = f"Command execution failed: {exc}"
                    is_error = True
            elif tool_name and "read" in tool_name:
                # Read file content
                try:
                    with open(tool_input, 'r', errors='ignore') as f:
                        data = f.read()
                        result_text = data
                        # If file content chunked, mark truncation
                        if hasattr(f, "remaining_data") and f.remaining_data:
                            result_text += "\n<Content truncated>"
                except Exception as exc:
                    result_text = f"File read error: {exc}"
                    is_error = True
            else:
                result_text = f"Tool '{tool_name}' not supported or implemented."
                is_error = True
            # Truncate tool output if too large
            if TIKTOKEN_AVAILABLE:
                token_count = len(ENCODING.encode(result_text))
            else:
                token_count = max(1, (len(result_text) // 4))
            if token_count > CHUNK_TOKEN_LIMIT:
                if TIKTOKEN_AVAILABLE:
                    tokens = ENCODING.encode(result_text)
                    partial_tokens = tokens[:CHUNK_TOKEN_LIMIT]
                    partial_text = ENCODING.decode(partial_tokens)
                else:
                    partial_text = result_text[:CHUNK_TOKEN_LIMIT * 4]
                result_text = partial_text + "\n<Output truncated>"
            # Prepare tool result block
            tool_use_id = tool_use_block_param.get("id")
            tool_result_block: Dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_text if is_error else [{"type": "text", "text": result_text}],
                "is_error": is_error
            }
            # Append tool result to assistant message content
            messages[-1]["content"].append(tool_result_block)
            # Notify via tool_output_callback for UI/CLI
            result_obj = ToolResult(output=result_text) if not is_error else ToolResult(error=result_text)
            tool_output_callback(tool_use_id, result_obj)
            # Continue loop to send tool result to Claude and get further response
            continue
        else:
            # No tool used, final answer obtained
            content_blocks: List[BetaContentBlockParam] = []
            if assistant_text:
                content_blocks.append(BetaTextBlockParam(type="text", text=assistant_text))
            messages.append({"role": "assistant", "content": content_blocks})
            # Tally actual output tokens and update token manager
            output_tokens = 0
            if TIKTOKEN_AVAILABLE:
                output_tokens = len(ENCODING.encode(assistant_text))
            else:
                output_tokens = max(1, (len(assistant_text) // 4))
            header_info = {
                "anthropic-input-tokens": str(estimated_input_tokens),
                "anthropic-output-tokens": str(output_tokens)
            }
            token_manager.process_response_headers(header_info)
            return messages

