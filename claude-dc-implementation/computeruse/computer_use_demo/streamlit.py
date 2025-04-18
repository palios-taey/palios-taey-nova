import asyncio
import base64
import os
import subprocess
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import cast, get_args

import httpx
import streamlit as st
from anthropic import RateLimitError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
from streamlit.delta_generator import DeltaGenerator

from computer_use_demo.loop import (
    APIProvider,
    sampling_loop,
)
from computer_use_demo.tools import ToolResult, ToolVersion

PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-7-sonnet-20250219",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}

@dataclass(kw_only=True, frozen=True)
class ModelConfig:
    tool_version: ToolVersion
    max_output_tokens: int
    default_output_tokens: int
    has_thinking: bool = False

SONNET_3_5_NEW = ModelConfig(
    tool_version="computer_use_20241022",
    max_output_tokens=1024 * 8,
    default_output_tokens=1024 * 4,
)

SONNET_3_7 = ModelConfig(
    tool_version="computer_use_20250124",
    max_output_tokens=128_000,  # support extended 128K output
    default_output_tokens=64_000,
    has_thinking=True,
)

MODEL_TO_MODEL_CONF: dict[str, ModelConfig] = {
    "claude-3-7-sonnet-20250219": SONNET_3_7,
}

CONFIG_DIR = PosixPath("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"
STREAMLIT_STYLE = """
<style>
    /* Highlight the stop button in red */
    button[kind=header] {
        background-color: rgb(255, 75, 75);
        border: 1px solid rgb(255, 75, 75);
        color: rgb(255, 255, 255);
    }
    button[kind=header]:hover {
        background-color: rgb(255, 51, 51);
    }
    /* Hide the streamlit deploy button */
    .stAppDeployButton {
        visibility: hidden;
    }
</style>
"""

WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data, as malicious web content can hijack Claude's behavior"
INTERRUPT_TEXT = "(user stopped or interrupted and wrote the following)"
INTERRUPT_TOOL_ERROR = "human stopped or interrupted tool execution"

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

def setup_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_key" not in st.session_state:
        # Load API key from file or env
        st.session_state.api_key = (CONFIG_DIR / "api_key").read_text().strip() if API_KEY_FILE.exists() else os.getenv("ANTHROPIC_API_KEY", "")
    if "provider" not in st.session_state:
        st.session_state.provider = os.getenv("API_PROVIDER", "anthropic") or APIProvider.ANTHROPIC
    if "provider_radio" not in st.session_state:
        st.session_state.provider_radio = st.session_state.provider
    if "model" not in st.session_state:
        _reset_model()
    if "auth_validated" not in st.session_state:
        st.session_state.auth_validated = False
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "tools" not in st.session_state:
        st.session_state.tools = {}
    if "only_n_most_recent_images" not in st.session_state:
        st.session_state.only_n_most_recent_images = 3
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = (CONFIG_DIR / "system_prompt").read_text().strip() if (CONFIG_DIR / "system_prompt").exists() else ""
    if "hide_images" not in st.session_state:
        st.session_state.hide_images = False
    # Removed token-efficient tools beta flag (always disabled for stability)
    if "in_sampling_loop" not in st.session_state:
        st.session_state.in_sampling_loop = False
    if "current_message_placeholder" not in st.session_state:
        st.session_state.current_message_placeholder = None
    if "current_message_text" not in st.session_state:
        st.session_state.current_message_text = ""
    if "current_thinking_placeholder" not in st.session_state:
        st.session_state.current_thinking_placeholder = None
    if "current_thinking_text" not in st.session_state:
        st.session_state.current_thinking_text = ""

def _reset_model():
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[cast(APIProvider, st.session_state.provider)]
    _reset_model_conf()

def _reset_model_conf():
    model_conf = (
        SONNET_3_7 if "3-7" in st.session_state.model
        else MODEL_TO_MODEL_CONF.get(st.session_state.model, SONNET_3_5_NEW)
    )
    st.session_state.tool_version = model_conf.tool_version
    st.session_state.has_thinking = model_conf.has_thinking
    st.session_state.output_tokens = model_conf.default_output_tokens
    st.session_state.max_output_tokens = model_conf.max_output_tokens
    st.session_state.thinking_budget = int(model_conf.default_output_tokens / 2)

def _api_response_callback(request: httpx.Request | None, response: httpx.Response | object | None, error: Exception | None, *, tab: DeltaGenerator, response_state: dict):
    """Callback to log API request/response (for HTTP logs tab)."""
    response_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_state[response_id] = (request, response)
    if error:
        _render_error(error)
    _render_api_response(request, response, response_id, tab)

def _tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict[str, ToolResult]):
    """Handle a tool output by storing it to state and rendering it."""
    tool_state[tool_id] = tool_output
    _render_message(Sender.TOOL, tool_output)

def _streaming_output_callback(content_block):
    """Handle streaming output by updating the current message placeholder."""
    # Handle streaming delta updates
    if isinstance(content_block, dict) and content_block.get("is_delta", False):
        if content_block["type"] == "text":
            # Append delta text to current message
            st.session_state.current_message_text += content_block["text"]
            if st.session_state.current_message_placeholder is not None:
                st.session_state.current_message_placeholder.markdown(st.session_state.current_message_text + "▌")
            return
        elif content_block["type"] == "thinking":
            # Append delta thinking text to current thinking message
            st.session_state.current_thinking_text += content_block["thinking"]
            if st.session_state.current_thinking_placeholder is not None:
                st.session_state.current_thinking_placeholder.markdown(f"[Thinking]\n\n{st.session_state.current_thinking_text}▌")
            return

    # Handle full content blocks (no longer delta)
    if hasattr(content_block, "type"):
        # If starting a new text or tool_use block, finalize any existing thinking placeholder
        if content_block.type in ["text", "tool_use"] and st.session_state.get("current_thinking_placeholder"):
            st.session_state.current_thinking_placeholder.markdown(f"[Thinking]\n\n{st.session_state.current_thinking_text}")
            st.session_state.current_thinking_placeholder = None

        if content_block.type == "text":
            # Begin a new assistant text message (or output a complete text block)
            with st.chat_message(Sender.BOT):
                if hasattr(content_block, "text"):
                    st.session_state.current_message_text = content_block.text or ""
                    if st.session_state.current_message_placeholder is not None:
                        st.session_state.current_message_placeholder.markdown(st.session_state.current_message_text + "▌")
                    else:
                        st.markdown(st.session_state.current_message_text + ("▌" if st.session_state.current_message_text else ""))

        elif content_block.type == "thinking":
            # Begin a new thinking block in its own assistant message
            with st.chat_message(Sender.BOT):
                st.session_state.current_thinking_placeholder = st.empty()
                st.session_state.current_thinking_text = content_block.thinking or ""
                st.session_state.current_thinking_placeholder.markdown(f"[Thinking]\n\n{st.session_state.current_thinking_text}▌")

        elif content_block.type == "tool_use":
            # Render a tool invocation block in its own assistant message
            with st.chat_message(Sender.BOT):
                tool_name = getattr(content_block, "name", "")
                tool_input = getattr(content_block, "input", {}) or {}
                warning_message = ""
                if tool_name == "bash" and (not tool_input or "command" not in tool_input):
                    warning_message = "\n\n**⚠️ Warning: Bash tool requires a command parameter. This call will fail!**"
                st.code(f"Tool Use: {tool_name}\nInput: {tool_input}{warning_message}")

        else:
            # Fallback: render any other content block types directly
            with st.chat_message(Sender.BOT):
                st.write(content_block)

def _render_api_response(request: httpx.Request, response: httpx.Response | object | None, response_id: str, tab: DeltaGenerator):
    """Render an API request/response pair in the HTTP Exchange Logs tab."""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            st.markdown(f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}")
            try:
                st.json(request.read().decode())
            except:
                st.write("Could not decode request body")
            if isinstance(response, httpx.Response):
                # Display response metadata and content if available
                status = response.status_code
                st.markdown(f"`Status: {status}`")
                try:
                    st.json(response.json())
                except:
                    resp_text = response.text[:1000] + ("..." if len(response.text) > 1000 else "")
                    st.markdown(f"Response text: `{resp_text}`")
            elif response is not None:
                # If response is a parsed object or custom data
                st.write(response)

def _render_message(sender: Sender, message: str | BetaContentBlockParam | ToolResult):
    """Render a single chat message in the Chat tab."""
    if not message:
        return  # skip empty messages

    # If ToolResult object, render its content appropriately
    is_tool_result = isinstance(message, ToolResult)
    if is_tool_result and st.session_state.hide_images and not (hasattr(message, "error") or hasattr(message, "output")):
        return
    with st.chat_message(sender):
        if is_tool_result:
            message = cast(ToolResult, message)
            if message.output:
                if message.__class__.__name__ == "CLIResult":
                    st.code(message.output)
                else:
                    st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image and not st.session_state.hide_images:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict):
            # Render Beta content blocks
            if message.get("type") == "text":
                st.markdown(message.get("text", ""))
            elif message.get("type") == "thinking":
                thinking_content = message.get("thinking", "")
                st.markdown(f"[Thinking]\n\n{thinking_content}")
            elif message.get("type") == "tool_use":
                st.code(f'Tool Use: {message.get("name", "")}\nInput: {message.get("input", "")}')
            else:
                st.write(message)
        else:
            # Render plain string messages
            st.markdown(str(message))

async def main():
    """Streamlit UI render loop."""
    setup_state()
    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)
    st.title("Claude Computer Use Demo")
    if not os.getenv("HIDE_WARNING", False):
        st.warning(WARNING_TEXT)

    # Sidebar controls
    with st.sidebar:
        def _reset_api_provider():
            if st.session_state.provider_radio != st.session_state.provider:
                _reset_model()
                st.session_state.provider = st.session_state.provider_radio
                st.session_state.auth_validated = False

        provider_options = [option.value for option in APIProvider]
        st.radio(
            "API Provider",
            options=provider_options,
            key="provider_radio",
            format_func=lambda x: x.title(),
            on_change=_reset_api_provider,
        )
        st.text_input("Model", key="model", on_change=_reset_model_conf)
        if st.session_state.provider == APIProvider.ANTHROPIC:
            st.text_input(
                "Anthropic API Key",
                type="password",
                key="api_key",
                on_change=lambda: (CONFIG_DIR / "api_key").write_text(st.session_state.api_key or ""),
            )
        st.number_input(
            "Only send N most recent images",
            min_value=0,
            key="only_n_most_recent_images",
            help="Truncate older screenshots in the conversation to save tokens",
        )
        st.text_area(
            "Custom System Prompt Suffix",
            key="custom_system_prompt",
            help="Additional instructions to append to the base system prompt.",
            on_change=lambda: (CONFIG_DIR / "system_prompt").write_text(st.session_state.custom_system_prompt or ""),
        )
        st.checkbox("Hide screenshots", key="hide_images")
        # Removed token-efficient tools beta toggle for stability
        versions = get_args(ToolVersion)
        st.radio(
            "Tool Versions",
            key="tool_versions",
            options=versions,
            index=versions.index(st.session_state.tool_version),
        )
        st.number_input("Max Output Tokens", key="output_tokens", step=1)
        st.checkbox("Thinking Enabled", key="thinking", value=True)
        st.number_input(
            "Thinking Budget",
            key="thinking_budget",
            max_value=st.session_state.max_output_tokens,
            step=1,
            disabled=not st.session_state.thinking,
        )
        if st.button("Reset", type="primary"):
            with st.spinner("Resetting..."):
                st.session_state.clear()
                setup_state()
                subprocess.run("pkill Xvfb; pkill tint2", shell=True)
                await asyncio.sleep(1)
                subprocess.run("./start_all.sh", shell=True)

    # Main chat interface
    if not st.session_state.auth_validated:
        if auth_error := validate_auth(st.session_state.provider, st.session_state.api_key):
            st.warning(f"Please resolve the following auth issue:\n\n{auth_error}")
            return
        else:
            st.session_state.auth_validated = True

    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input("Type a message to send to Claude to control the computer...")
    with chat:
        # Display conversation history
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        # Tool results: retrieve full ToolResult object from state for rendering
                        _render_message(Sender.TOOL, st.session_state.tools[block["tool_use_id"]])
                    else:
                        _render_message(message["role"], cast(BetaContentBlockParam | ToolResult, block))
        # Display past HTTP logs
        for identity, (request, response) in st.session_state.responses.items():
            _render_api_response(request, response, identity, http_logs)

        # If user sent a new message
        if new_message:
            st.session_state.messages.append({
                "role": Sender.USER,
                "content": [
                    *maybe_add_interruption_blocks(),
                    BetaTextBlockParam(type="text", text=new_message),
                ],
            })
            _render_message(Sender.USER, new_message)

        try:
            most_recent_message = st.session_state.messages[-1]
        except IndexError:
            return
        if most_recent_message["role"] is not Sender.USER:
            # No new user message to respond to
            return

        # Run Claude's sampling loop for the latest user message
        with track_sampling_loop():
            # Create a placeholder chat message for streaming assistant response
            with st.chat_message(Sender.BOT):
                st.session_state.current_message_placeholder = st.empty()
                st.session_state.current_message_text = ""

            # Call the sampling loop and stream output
            result_messages = await sampling_loop(
                system_prompt_suffix=st.session_state.custom_system_prompt,
                model=st.session_state.model,
                provider=st.session_state.provider,
                messages=st.session_state.messages,
                output_callback=_streaming_output_callback,
                tool_output_callback=partial(_tool_output_callback, tool_state=st.session_state.tools),
                api_response_callback=partial(_api_response_callback, tab=http_logs, response_state=st.session_state.responses),
                api_key=st.session_state.api_key,
                only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                tool_version=st.session_state.tool_version,
                max_tokens=st.session_state.output_tokens,
                thinking_budget=st.session_state.thinking_budget if st.session_state.thinking else None
            )
            # Store results and finalize streaming placeholders
            st.session_state.messages = result_messages
            if st.session_state.current_message_placeholder:
                st.session_state.current_message_placeholder.markdown(st.session_state.current_message_text)
                st.session_state.current_message_placeholder = None
            if st.session_state.get("current_thinking_placeholder"):
                st.session_state.current_thinking_placeholder.markdown(f"[Thinking]\n\n{st.session_state.current_thinking_text}")
                st.session_state.current_thinking_placeholder = None

def maybe_add_interruption_blocks():
    """If an ongoing generation was interrupted by the user, annotate the conversation with an interruption marker."""
    if not st.session_state.in_sampling_loop:
        return []
    # If we were in the middle of sampling and the user interrupted, mark the last assistant message and any pending tool calls as interrupted
    result = []
    last_message = st.session_state.messages[-1]
    previous_tool_use_ids = [block["id"] for block in last_message["content"] if block["type"] == "tool_use"]
    for tool_use_id in previous_tool_use_ids:
        st.session_state.tools[tool_use_id] = ToolResult(error=INTERRUPT_TOOL_ERROR)
        result.append(BetaToolResultBlockParam(tool_use_id=tool_use_id, type="tool_result", content=INTERRUPT_TOOL_ERROR, is_error=True))
    # Mark that the assistant was interrupted mid-response
    result.append(BetaTextBlockParam(type="text", text=INTERRUPT_TEXT))
    return result

@contextmanager
def track_sampling_loop():
    """Context manager to track whether we are in an assistant response generation loop."""
    st.session_state.in_sampling_loop = True
    try:
        yield
    finally:
        st.session_state.in_sampling_loop = False

def validate_auth(provider: APIProvider, api_key: str | None):
    if provider == APIProvider.ANTHROPIC:
        if not api_key:
            return "Enter your Anthropic API key in the sidebar to continue."
    if provider == APIProvider.BEDROCK:
        import boto3
        if not boto3.Session().get_credentials():
            return "You must have AWS credentials set up to use the Bedrock API."
    if provider == APIProvider.VERTEX:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        if not os.environ.get("CLOUD_ML_REGION"):
            return "Set the CLOUD_ML_REGION environment variable to use the Vertex API."
        try:
            google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        except DefaultCredentialsError:
            return "Your Google Cloud credentials are not set up correctly."

