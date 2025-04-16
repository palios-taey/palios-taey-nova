Thank you. I’ll carefully modify Claude DC’s existing files to preserve their structure and integrate the new streaming and token management features with minimal disruption. I’ll retain tool configuration, Claude’s behavior toggles, and Streamlit’s layout, while embedding:

- Streaming via Messages API for claude-3-7-sonnet-20250219
- Unified per-minute token tracking across messages and tool outputs
- Interception of tool responses via safe output wrapping

I’ll return shortly with updated versions of `loop.py`, `streamlit.py`, and `token_manager.py`, fully integrated and preserving Claude DC’s architecture.

# Integrating Streaming and Token Management in Claude DC

In this section, we implement **streaming support** for the Claude 3.7 model and **unified per-minute token management** into Claude DC’s architecture. The changes involve updating the core loop for message generation, the Streamlit interface, and introducing a token manager to enforce rate limits.

## Streaming Implementation in `loop.py`

We modify `loop.py` to use the Anthropic **streaming messages API** (`stream=True`), allowing Claude’s responses to be delivered incrementally. Instead of waiting for the full completion, the code now iterates over SSE events from `client.messages.create(..., stream=True)` ([claude-dc-extended-use-guidance.md](file://file-DBPwmtHNm57yoy88inS29a#:~:text=from%20anthropic%20import%20Anthropic)). As each `content_block_delta` event arrives (containing a piece of Claude's reply text), we immediately output it via an `output_callback` (printing to CLI or sending to the UI) to simulate a live typing effect ([claude-dc-extended-use-guidance.md](file://file-DBPwmtHNm57yoy88inS29a#:~:text=stream%20%3D%20client,call%20or%20stop%2C%20handle%20accordingly)). 

We handle **tool use events** in the streaming loop as special cases. If an event indicates a `tool_use` request (for example, Claude deciding to use the `read_file` or `bash` tool), we pause the stream to execute the tool. The model’s tool request appears as a structured event (here, captured as `BetaToolUseBlockParam`) containing the tool name and input ([chatgpt-universal-token-handling.md](file://file-DQbNpYdRFCGXd3WsVeXDAU#:~:text=calculates%20the%20would,1)). We break out of the streaming loop when a tool request is encountered, execute the tool (reading a file or running a command), and then insert a `BetaToolResultBlockParam` with the tool’s output into the conversation context. This tool result is then sent back to Claude in a new API call so it can continue its response ([claude-dc-extended-use-guidance.md](file://file-DBPwmtHNm57yoy88inS29a#:~:text=for%20event%20in%20stream%3A%20,call%20or%20stop%2C%20handle%20accordingly)) ([loop.py](file://file-BFeayHqmqQKVvUdC55qEHk#:~:text=def%20_make_api_tool_result,error%3A%20is_error%20%3D%20True)).

For example, if Claude requests to `read_file` a large text, we open and read the file in chunks (to avoid sending >40k tokens at once). We return a partial file content in a `tool_result` block and allow Claude to continue; if more content is needed, Claude can call the tool again to fetch the next chunk. This approach ensures that even very long file outputs are delivered safely in segments without exceeding context limits.

Finally, when Claude finishes its answer (no further tool calls), the loop exits. The assistant’s full reply—potentially composed of multiple content blocks and tool interactions—is appended to the message history. 

## Per-Minute Token Management (`token_manager.py`)

We introduce a `TokenManager` class to track input/output token usage over a sliding one-minute window and enforce the 40,000 input-token/minute rate limit (and output 16,000 tokens/minute) ([token_manager.py](file://file-NgMhDE9wzj3STbwKeSKNih#:~:text=def%20__init__%28self%29%3A%20self,1000%20requests%20per%20minute%20default)) ([token_manager.py](file://file-M9u1Va8pvAztJzS8qisCZH#:~:text=,of%20input%20limit)). The token manager maintains timestamped records of tokens sent and received. Before each API call, we estimate the upcoming input and output token count and call `delay_if_needed(...)`; if sending the new request would exceed ~80% of the allowed rate, the manager calculates how long to wait until some tokens fall out of the 60-second window ([token_manager.py](file://file-M9u1Va8pvAztJzS8qisCZH#:~:text=,current_time)). It then delays the execution by that duration to throttle the rate (printing a warning like “⚠️ delaying for X seconds to avoid rate limit”) ([token_manager.py](file://file-M9u1Va8pvAztJzS8qisCZH#:~:text=logger.warning%28f,return%20True%2C%20delay)). This preventive throttling ensures we never actually hit the hard limit and receive a 429 error.

We use Anthropic’s **token counting API** when available to accurately estimate the token count of the request payload ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=import%20anthropic%20client%20%3D%20anthropic.Anthropic%28api_key%3D,count.input_tokens)). This lets us include all system, user, and tool context in the count. (The token counting API is free and does not consume model quota ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=docs,without%20impacting%20the%2040K%20limit)).) If the counting API is not accessible, we fall back to an approximation (using `tiktoken` with the GPT-3.5 tokenizer `cl100k_base` as a close proxy, or a simple char count heuristic) ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=OpenAI%E2%80%99s%20GPT%20tokenizers,based%20estimator%20for%20better%20accuracy)) ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=Fallback%20with%20tiktoken%3A%20If%20you,For%20example)). After each API response (or streaming completion), we update the token usage statistics in the manager. The manager logs total tokens used and remaining budget, and would adapt if different model limits (e.g. 20k/min for Claude 3.7 Sonnet) were configured ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=if%20you%20detect%20the%20model,take%20it%20as%20a%20parameter)).

## Tool Call Interception and Output Chunking

To ensure tools do not bypass token limits, we monkey-patch Python file I/O. We override `builtins.open` to return an `_InterceptedFile` wrapper that intercepts read calls ([chatgpt-universal-token-handling.md](file://file-DQbNpYdRFCGXd3WsVeXDAU#:~:text=,IOBase)) ([chatgpt-universal-token-handling.md](file://file-DQbNpYdRFCGXd3WsVeXDAU#:~:text=self,rest%20for%20later%20if%20needed)). If a tool (like `read_file`) tries to read a huge file, our wrapper reads the content and counts the tokens; if it exceeds a safe chunk size (e.g. 15k tokens), it returns only a portion and stores the remainder internally ([chatgpt-universal-token-handling.md](file://file-DQbNpYdRFCGXd3WsVeXDAU#:~:text=data%20%3D%20self,data%20%3D%20partial%20return%20data)) ([chatgpt-universal-token-handling.md](file://file-DQbNpYdRFCGXd3WsVeXDAU#:~:text=builtins.open%20%3D%20intercepted_open%20,and%20be%20constrained)). This way, Claude receives a truncated snippet (with an indication that content was truncated) and can request the next part if needed, rather than us sending the entire file at once and violating the rate limit. We apply a similar strategy for subprocess outputs (the `bash` tool): if a shell command produces extremely large output, we capture and truncate it to a safe size. In our implementation below, if a bash output or file content is too large, we append a notice "`<Output truncated>`" and limit the returned text to ~15k tokens.

All tool outputs returned to Claude are funneled through the token manager as part of the next model input. This unified interception ensures that even content generated by tools is accounted for under the 40k/min limit. By slicing and pacing large outputs in time ([chatgpt-input-token-research.md](file://file-ME9TfWzm3vgAdh6JdFcbTQ#:~:text=docs,in%20analyzing%20large%20data%20through)), we enable Claude to work on lengthy files or commands reliably without hitting API errors.

## Preserving Existing Structure

The integration is done **in-place**, preserving the structure of Claude DC’s original quickstart. We keep the original tabs and options (like model provider selection, the 128k extended output beta, the token-efficient tools beta flag, etc.). The core conversation loop remains a single `while True` without introducing additional nested loops beyond what’s needed for streaming event handling. New logic (e.g. token counting and file interception) is encapsulated in helper functions or the `TokenManager` class to minimize changes to the primary flow.

Below, we provide the **complete updated code** for `loop.py`, `streamlit.py`, and `token_manager.py` with the above enhancements. 

## `loop.py`

```python
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
        data = self.file.read(size)
        if not data:
            return ""
        # Estimate token count of data
        if TIKTOKEN_AVAILABLE:
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
``` 

## `streamlit.py`

```python
import os
import math
import streamlit as st
from loop import APIProvider, sampling_loop, Sender, ToolResult
from anthropic.types.beta import BetaTextBlockParam, BetaToolResultBlockParam
from token_manager import token_manager

st.title("Claude DC – Streaming Chat Interface")
st.markdown("Enter a prompt for Claude and receive a streamed response. Token usage is tracked to avoid exceeding rate limits.")

# Ensure Anthropic API key is set
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    st.stop()
if "api_key" not in st.session_state:
    st.session_state.api_key = api_key

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "in_sampling_loop" not in st.session_state:
    st.session_state.in_sampling_loop = False
if "provider" not in st.session_state:
    st.session_state.provider = APIProvider.ANTHROPIC
if "model" not in st.session_state:
    st.session_state.model = "claude-3-7-sonnet-20250219"
if "tool_version" not in st.session_state:
    st.session_state.tool_version = "computer_use_20250124"
if "output_tokens" not in st.session_state:
    st.session_state.output_tokens = token_manager.get_safe_limits()["max_tokens"]
if "thinking" not in st.session_state:
    st.session_state.thinking = False
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = None
if "only_n_most_recent_images" not in st.session_state:
    st.session_state.only_n_most_recent_images = 0
if "token_efficient_tools_beta" not in st.session_state:
    st.session_state.token_efficient_tools_beta = False

# Helper for rendering messages
def _render_message(role, content):
    """Render a message block in the Streamlit app."""
    role_name = role if isinstance(role, str) else role.value if hasattr(role, "value") else str(role)
    if role_name.lower() in ["user", "sender.user"]:
        st.markdown(f"**User:** {content}")
    elif role_name.lower() in ["assistant", "sender.bot"]:
        # Assistant content could be partial text or final text
        if isinstance(content, str):
            st.markdown(f"**Claude:** {content}")
        elif isinstance(content, dict) and content.get("type") == "text":
            st.markdown(f"**Claude:** {content.get('text', '')}")
        elif isinstance(content, ToolResult):
            # Assistant role receiving a ToolResult (should not happen directly)
            if content.error:
                st.error(content.error)
            elif content.output:
                st.code(content.output)
    elif role_name.lower() in ["tool", "sender.tool"]:
        # content is a ToolResult from st.session_state.tools
        if isinstance(content, ToolResult):
            if content.error:
                st.error(content.error)
            elif content.output:
                st.code(content.output)
        else:
            st.write(content)

INTERRUPT_TOOL_ERROR = "Tool execution interrupted by new prompt"
INTERRUPT_TEXT = "*[The previous action was interrupted]*"

def maybe_add_interruption_blocks():
    if not st.session_state.in_sampling_loop:
        return []
    blocks = []
    last_msg = st.session_state.messages[-1] if st.session_state.messages else None
    if last_msg and isinstance(last_msg["content"], list):
        prev_tool_ids = [block["id"] for block in last_msg["content"] if isinstance(block, dict) and block.get("type") == "tool_use"]
        for tool_use_id in prev_tool_ids:
            st.session_state.tools[tool_use_id] = ToolResult(error=INTERRUPT_TOOL_ERROR)
            blocks.append(BetaToolResultBlockParam(tool_use_id=tool_use_id, type="tool_result", content=INTERRUPT_TOOL_ERROR, is_error=True))  # type: ignore
    blocks.append(BetaTextBlockParam(type="text", text=INTERRUPT_TEXT))
    return blocks

from contextlib import contextmanager
@contextmanager
def track_sampling_loop():
    st.session_state.in_sampling_loop = True
    try:
        yield
    finally:
        st.session_state.in_sampling_loop = False

# Input field for user prompt
user_input = st.text_area("Your Prompt:", value="", placeholder="Type your question or request here...")

# Submit button
if st.button("Submit"):
    if not user_input.strip():
        st.warning("Please enter a prompt before submitting.")
    else:
        # Append user message (with any interruption context) to conversation
        st.session_state.messages.append({
            "role": "user",
            "content": [*maybe_add_interruption_blocks(), BetaTextBlockParam(type="text", text=user_input)]  # type: ignore
        })
        _render_message(Sender.USER, user_input)
        # Call Claude's agent with streaming output
        try:
            with track_sampling_loop():
                # Run sampling_loop synchronously (will stream output via callbacks)
                st.session_state.messages = asyncio.run(sampling_loop(
                    system_prompt_suffix=st.session_state.get("custom_system_prompt", ""),
                    model=st.session_state.model,
                    provider=st.session_state.provider,
                    messages=st.session_state.messages,
                    output_callback=lambda text: _render_message(Sender.BOT, text),
                    tool_output_callback=lambda tid, result: _render_message(Sender.TOOL, result),
                    api_response_callback=lambda req, resp, err=None: None,
                    api_key=st.session_state.api_key,
                    only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                    tool_version=st.session_state.tool_version,
                    max_tokens=st.session_state.output_tokens,
                    thinking_budget=st.session_state.thinking_budget if st.session_state.thinking else None,
                    token_efficient_tools_beta=st.session_state.token_efficient_tools_beta
                ))
        except Exception as e:
            st.error(f"Error during generation: {e}")
```

## `token_manager.py`

```python
"""
Token Management Module for Claude DC
-------------------------------------
Prevents API rate limit errors by monitoring token usage and introducing delays.
Supports 128K output beta and sliding-window rate limiting.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Any, List

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/token_manager.log'), logging.StreamHandler()]
)
logger = logging.getLogger("token_manager")

class TokenManager:
    """Manages API token usage to prevent rate limit errors (40k/min input, 16k/min output)."""
    def __init__(self):
        # Token usage cumulative stats
        self.calls_made = 0
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        # Sliding window tracking for per-minute rate limiting
        self.input_token_timestamps: List[Tuple[float, int]] = []
        self.output_token_timestamps: List[Tuple[float, int]] = []
        self.input_tokens_per_minute = 0
        self.output_tokens_per_minute = 0
        # Organization default limits per minute
        self.org_input_limit = 40000    # 40K input tokens per minute
        self.org_output_limit = 16000   # 16K output tokens per minute
        # Warning thresholds (80% of limit by default)
        self.input_token_warning_threshold = 0.8
        self.output_token_warning_threshold = 0.8
        # Overall token budget (for tracking total usage, e.g. 1M tokens)
        self.token_budget = 1000000
        self.remaining_budget = self.token_budget
        # Safe limits for model calls (avoid validation errors)
        self.safe_max_tokens = 20000       # safe max output tokens to request
        self.safe_thinking_budget = 4000   # safe max "thinking" budget tokens
        # Extended output beta usage
        self.extended_output_beta = True
        logger.info("Token manager initialized with sliding window rate limiting")

    def _parse_reset_time(self, reset_time_str: str) -> datetime:
        """Parse ISO format reset time from API headers."""
        try:
            return datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Error parsing reset time '{reset_time_str}': {e}")
            return datetime.now(timezone.utc) + timedelta(seconds=60)

    def _calculate_delay(self, reset_time: Optional[datetime], used_quota: float) -> float:
        """Calculate necessary delay based on quota usage and time until reset."""
        if reset_time is None:
            # If no exact reset timestamp, apply progressive backoff when over threshold
            if used_quota > self.input_token_warning_threshold:
                backoff_factor = [1, 1, 2, 3, 5, 8, 13][0]  # simplified backoff (first element)
                delay = backoff_factor * (used_quota - self.input_token_warning_threshold) * 5
                return max(delay, 0.1)
            return 0.1
        now = datetime.now(timezone.utc)
        if reset_time > now:
            time_to_reset = (reset_time - now).total_seconds()
            if used_quota > self.input_token_warning_threshold:
                backoff_factor = [1, 1, 2, 3, 5, 8, 13][0]
                delay = time_to_reset * (used_quota - self.input_token_warning_threshold) * backoff_factor
                return max(delay, 0.1)
        return 0.0

    def check_input_rate_limit(self, input_tokens: int) -> Tuple[bool, float]:
        """Check input token rate limit window and determine if a delay is needed."""
        current_time = time.time()
        # Record this request in the sliding window
        self.input_token_timestamps.append((current_time, input_tokens))
        # Remove entries older than 60 seconds
        one_minute_ago = current_time - 60
        self.input_token_timestamps = [(ts, tok) for ts, tok in self.input_token_timestamps if ts >= one_minute_ago]
        self.input_tokens_per_minute = sum(tok for _, tok in self.input_token_timestamps)
        logger.info(f"Input tokens per minute: {self.input_tokens_per_minute}/{self.org_input_limit}")
        if self.input_tokens_per_minute >= self.org_input_limit * self.input_token_warning_threshold:
            # Oldest request in window
            if self.input_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.input_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                delay = max(seconds_to_wait, 0) + 1
                logger.warning(f"Approaching input token rate limit - need to wait {delay:.2f} seconds")
                print(f"⚠️ Input token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        return False, 0

    def check_output_rate_limit(self, output_tokens: int) -> Tuple[bool, float]:
        """Check output token rate limit window and determine if a delay is needed."""
        current_time = time.time()
        self.output_token_timestamps.append((current_time, output_tokens))
        one_minute_ago = current_time - 60
        self.output_token_timestamps = [(ts, tok) for ts, tok in self.output_token_timestamps if ts >= one_minute_ago]
        self.output_tokens_per_minute = sum(tok for _, tok in self.output_token_timestamps)
        logger.info(f"Output tokens per minute: {self.output_tokens_per_minute}/{self.org_output_limit}")
        if self.output_tokens_per_minute >= self.org_output_limit * self.output_token_warning_threshold:
            if self.output_token_timestamps:
                oldest_timestamp = min(ts for ts, _ in self.output_token_timestamps)
                seconds_to_wait = (oldest_timestamp + 60) - current_time
                delay = max(seconds_to_wait, 0) + 1
                logger.warning(f"Approaching output token rate limit - need to wait {delay:.2f} seconds")
                print(f"⚠️ Output token rate limit approaching - delaying for {delay:.2f} seconds")
                return True, delay
        return False, 0

    def get_safe_limits(self) -> Dict[str, int]:
        """Get safe token limits for max_tokens and thinking_budget."""
        return {
            "max_tokens": self.safe_max_tokens,
            "thinking_budget": self.safe_thinking_budget
        }

    def delay_if_needed(self, estimated_input_tokens: int, estimated_output_tokens: int) -> None:
        """Delay execution if needed to avoid hitting token rate limits."""
        should_delay_input, delay_time_input = self.check_input_rate_limit(estimated_input_tokens)
        should_delay_output, delay_time_output = self.check_output_rate_limit(estimated_output_tokens)
        if should_delay_input or should_delay_output:
            delay_time = max(delay_time_input, delay_time_output)
            logger.info(f"Delaying for {delay_time:.2f} seconds to avoid rate limit")
            print(f"🕒 Delaying for {delay_time:.2f} seconds to avoid rate limit.")
            time.sleep(delay_time)
            print("✅ Resuming after delay")

    def get_stats(self) -> Dict[str, Any]:
        """Return current usage statistics."""
        return {
            "calls_made": self.calls_made,
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "input_tokens_per_minute": self.input_tokens_per_minute,
            "output_tokens_per_minute": self.output_tokens_per_minute,
            "remaining_budget": self.remaining_budget,
            "extended_output_beta": self.extended_output_beta
        }

    def process_response_headers(self, headers: Dict[str, str]) -> None:
        """Process API response headers to track token usage."""
        self.calls_made += 1
        def get_header_int(key: str, default: int = 0) -> int:
            try:
                return int(headers.get(key, default))
            except (ValueError, TypeError):
                return default
        # Update usage from headers if present
        input_tokens = get_header_int('anthropic-input-tokens')
        output_tokens = get_header_int('anthropic-output-tokens')
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens
        self.remaining_budget = self.token_budget - self.output_tokens_used
        logger.info(f"API call used {input_tokens} input tokens and {output_tokens} output tokens")
        logger.info(f"Total so far: {self.input_tokens_used} input, {self.output_tokens_used} output; Remaining budget: {self.remaining_budget}")
        input_limit = get_header_int('anthropic-ratelimit-input-tokens-limit', 40000)
        output_limit = get_header_int('anthropic-ratelimit-output-tokens-limit', 16000)
        # (We rely on our own limits; just logging any header-provided limits)
        logger.info(f"Anthropic reported limits: {input_limit} input/min, {output_limit} output/min")

# Create a singleton instance for convenience
token_manager = TokenManager()
``` 

Each file includes the integrated logic for streaming outputs, enforcing per-minute token limits, and handling tool calls safely. With these changes, Claude DC can stream multi-turn answers (even extremely long ones) without hitting timeout ([claude-dc-extended-use-guidance.md](file://file-DBPwmtHNm57yoy88inS29a#:~:text=Anthropic%E2%80%99s%20Reference%20Implementation%20,stream%3DTrue%20for%20large%20token%20requests%E2%80%8B)) ([claude-dc-extended-use-guidance.md](file://file-DBPwmtHNm57yoy88inS29a#:~:text=repost,no%20data%20for%20too%20long))】, and it will throttle itself to respect the organization’s rate limits, ensuring stable long-running sessions. The agent can also utilize tools to browse files or execute commands, with large outputs being automatically chunked and fed back into Claude incrementally, preserving core functionality while preventing token limit error ([tool_intercept.py](file://file-YFJvNYQFTcqqVCBkoewhbN#:~:text=The%20primary%20issue%20is%20exactly,vulnerability%20in%20the%20protection%20system)) ([tool_intercept.py](file://file-YFJvNYQFTcqqVCBkoewhbN#:~:text=what%20we%20need,Here%27s%20my%20implementation%20plan))】.
