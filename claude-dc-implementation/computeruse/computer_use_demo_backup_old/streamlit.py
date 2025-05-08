"""
Entrypoint for streamlit, see https://docs.streamlit.io/
"""

import asyncio
import base64
import json
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
    tool_version=ToolVersion.COMPUTER_USE_20241022,
    max_output_tokens=1024 * 8,
    default_output_tokens=1024 * 4,
)

SONNET_3_7 = ModelConfig(
    tool_version=ToolVersion.COMPUTER_USE_20250124,
    max_output_tokens=128_000,
    default_output_tokens=1024 * 16,
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
    """Set up any state variables that don't exist yet - with improved error handling"""
    try:
        # Essential state variables
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        if "thinking" not in st.session_state:
            st.session_state.thinking = None
            
        if "api_key" not in st.session_state:
            # Try to load API key from file first, then environment
            try:
                st.session_state.api_key = load_from_storage("api_key") or os.getenv(
                    "ANTHROPIC_API_KEY", ""
                )
            except Exception as e:
                st.warning(f"Could not load API key: {str(e)}")
                st.session_state.api_key = ""
                
        if "provider" not in st.session_state:
            try:
                st.session_state.provider = (
                    os.getenv("API_PROVIDER", "anthropic") or APIProvider.ANTHROPIC
                )
            except Exception as e:
                st.warning(f"Could not set provider: {str(e)}")
                st.session_state.provider = APIProvider.ANTHROPIC
                
        if "provider_radio" not in st.session_state:
            st.session_state.provider_radio = st.session_state.provider
            
        if "model" not in st.session_state:
            try:
                _reset_model()
            except Exception as e:
                st.warning(f"Could not reset model: {str(e)}")
                st.session_state.model = "claude-3-7-sonnet-20250219"
                
        if "auth_validated" not in st.session_state:
            st.session_state.auth_validated = False
            
        if "responses" not in st.session_state:
            st.session_state.responses = {}
            
        if "tools" not in st.session_state:
            st.session_state.tools = {}
            
        if "only_n_most_recent_images" not in st.session_state:
            st.session_state.only_n_most_recent_images = 3
            
        if "custom_system_prompt" not in st.session_state:
            try:
                st.session_state.custom_system_prompt = load_from_storage("system_prompt") or ""
            except Exception as e:
                st.warning(f"Could not load system prompt: {str(e)}")
                st.session_state.custom_system_prompt = ""
                
        if "hide_images" not in st.session_state:
            st.session_state.hide_images = False
            
        if "token_efficient_tools_beta" not in st.session_state:
            st.session_state.token_efficient_tools_beta = False
            
        if "in_sampling_loop" not in st.session_state:
            st.session_state.in_sampling_loop = False
            
    except Exception as e:
        # Last resort fallback - ensure at least minimal state is set up
        st.error(f"Error setting up state: {str(e)}. Setting up minimal required state.")
        st.session_state.messages = getattr(st.session_state, "messages", [])
        st.session_state.responses = getattr(st.session_state, "responses", {})
        st.session_state.tools = getattr(st.session_state, "tools", {})
        st.session_state.model = getattr(st.session_state, "model", "claude-3-7-sonnet-20250219")
        st.session_state.api_key = getattr(st.session_state, "api_key", os.getenv("ANTHROPIC_API_KEY", ""))


def _reset_model():
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[
        cast(APIProvider, st.session_state.provider)
    ]
    _reset_model_conf()


def _reset_model_conf():
    model_conf = (
        SONNET_3_7
        if "3-7" in st.session_state.model
        else MODEL_TO_MODEL_CONF.get(st.session_state.model, SONNET_3_5_NEW)
    )
    st.session_state.tool_version = model_conf.tool_version
    st.session_state.has_thinking = model_conf.has_thinking
    st.session_state.output_tokens = model_conf.default_output_tokens
    st.session_state.max_output_tokens = model_conf.max_output_tokens
    st.session_state.thinking_budget = int(model_conf.default_output_tokens / 2)


async def main():
    """Render loop for streamlit"""
    setup_state()

    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

    st.title("Claude Computer Use Demo")

    if not os.getenv("HIDE_WARNING", False):
        st.warning(WARNING_TEXT)

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
                on_change=lambda: save_to_storage("api_key", st.session_state.api_key),
            )

        st.number_input(
            "Only send N most recent images",
            min_value=0,
            key="only_n_most_recent_images",
            help="To decrease the total tokens sent, remove older screenshots from the conversation",
        )
        st.text_area(
            "Custom System Prompt Suffix",
            key="custom_system_prompt",
            help="Additional instructions to append to the system prompt. see computer_use_demo/loop.py for the base system prompt.",
            on_change=lambda: save_to_storage(
                "system_prompt", st.session_state.custom_system_prompt
            ),
        )
        st.checkbox("Hide screenshots", key="hide_images")
        st.checkbox(
            "Enable token-efficient tools beta", key="token_efficient_tools_beta"
        )
        
        # Get available tool versions and check if current version exists
        versions = list(ToolVersion)
        version_values = [v.value for v in versions]
        current_version = getattr(st.session_state, "tool_version", ToolVersion.COMPUTER_USE_20250124.value)
        
        # Find index of current version or default to 0
        try:
            index = version_values.index(current_version)
        except ValueError:
            index = 0
            
        st.radio(
            "Tool Versions",
            key="tool_versions",
            options=versions,
            index=index,
            format_func=lambda x: x.value
        )

        st.number_input("Max Output Tokens", key="output_tokens", step=1)

        st.checkbox("Thinking Enabled", key="thinking", value=False)
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

                subprocess.run("pkill Xvfb; pkill tint2", shell=True)  # noqa: ASYNC221
                await asyncio.sleep(1)
                subprocess.run("./start_all.sh", shell=True)  # noqa: ASYNC221

    if not st.session_state.auth_validated:
        if auth_error := validate_auth(
            st.session_state.provider, st.session_state.api_key
        ):
            st.warning(f"Please resolve the following auth issue:\n\n{auth_error}")
            return
        else:
            st.session_state.auth_validated = True

    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input(
        "Type a message to send to Claude to control the computer..."
    )

    with chat:
        # render past chats
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    # the tool result we send back to the Anthropic API isn't sufficient to render all details,
                    # so we store the tool use responses
                    if isinstance(block, dict) and block["type"] == "tool_result":
                        # Safely check for tool_use_id and handle missing keys
                        tool_use_id = block.get("tool_use_id")
                        if tool_use_id is not None and tool_use_id in st.session_state.tools:
                            _render_message(
                                Sender.TOOL, st.session_state.tools[tool_use_id]
                            )
                        else:
                            # Fallback if tool_use_id is missing or not in tools dictionary
                            # Just display the content directly if available
                            content = block.get("content", "Tool result content unavailable")
                            is_error = block.get("is_error", False)
                            if is_error:
                                _render_message(
                                    Sender.TOOL, {"error": content, "output": None, "base64_image": None}
                                )
                            else:
                                _render_message(
                                    Sender.TOOL, {"error": None, "output": content, "base64_image": None}
                                )
                    else:
                        _render_message(
                            message["role"],
                            cast(BetaContentBlockParam | ToolResult, block),
                        )

        # render past http exchanges - with error handling
        if hasattr(st.session_state, "responses"):
            try:
                for identity, response_pair in st.session_state.responses.items():
                    # Safely unpack response pair, handling potential incorrect structures
                    try:
                        if isinstance(response_pair, tuple) and len(response_pair) >= 2:
                            request, response = response_pair
                        else:
                            # Fallback if response_pair is not properly structured
                            request, response = None, response_pair
                    except:
                        # Last resort fallback
                        request, response = None, None
                        
                    # Use our updated function that safely handles None requests
                    _render_api_response(request, response, identity, http_logs)
            except Exception as e:
                # Fail gracefully if anything goes wrong in the rendering process
                with http_logs:
                    st.warning(f"Could not render HTTP exchanges: {str(e)}")

        # render past chats
        if new_message:
            st.session_state.messages.append(
                {
                    "role": Sender.USER,
                    "content": [
                        *maybe_add_interruption_blocks(),
                        BetaTextBlockParam(type="text", text=new_message),
                    ],
                }
            )
            _render_message(Sender.USER, new_message)

        try:
            most_recent_message = st.session_state["messages"][-1]
        except IndexError:
            return

        if most_recent_message["role"] is not Sender.USER:
            # we don't have a user message to respond to, exit early
            return

        with track_sampling_loop():
            # run the agent sampling loop with the newest message
            st.session_state.messages = await sampling_loop(
                system_prompt_suffix=st.session_state.custom_system_prompt,
                model=st.session_state.model,
                provider=st.session_state.provider,
                messages=st.session_state.messages,
                output_callback=partial(_render_message, Sender.BOT),
                tool_output_callback=partial(
                    _tool_output_callback, tool_state=st.session_state.tools
                ),
                api_response_callback=partial(
                    _api_response_callback,
                    tab=http_logs,
                    response_state=st.session_state.responses,
                ),
                api_key=st.session_state.api_key,
                only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                tool_version=st.session_state.tool_version,
                max_tokens=st.session_state.output_tokens,
                thinking_budget=st.session_state.thinking_budget
                if st.session_state.thinking
                else None,
                token_efficient_tools_beta=st.session_state.token_efficient_tools_beta,
            )


def maybe_add_interruption_blocks():
    if not st.session_state.in_sampling_loop:
        return []
    # If this function is called while we're in the sampling loop, we can assume that the previous sampling loop was interrupted
    # and we should annotate the conversation with additional context for the model and heal any incomplete tool use calls
    result = []
    last_message = st.session_state.messages[-1]
    previous_tool_use_ids = [
        block["id"] for block in last_message["content"] if block["type"] == "tool_use"
    ]
    for tool_use_id in previous_tool_use_ids:
        st.session_state.tools[tool_use_id] = ToolResult(error=INTERRUPT_TOOL_ERROR)
        result.append(
            BetaToolResultBlockParam(
                tool_use_id=tool_use_id,
                type="tool_result",
                content=INTERRUPT_TOOL_ERROR,
                is_error=True,
            )
        )
    result.append(BetaTextBlockParam(type="text", text=INTERRUPT_TEXT))
    return result


@contextmanager
def track_sampling_loop():
    st.session_state.in_sampling_loop = True
    yield
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
            google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except DefaultCredentialsError:
            return "Your google cloud credentials are not set up correctly."


def load_from_storage(filename: str) -> str | None:
    """Load data from a file in the storage directory."""
    try:
        file_path = CONFIG_DIR / filename
        if file_path.exists():
            data = file_path.read_text().strip()
            if data:
                return data
    except Exception as e:
        st.write(f"Debug: Error loading {filename}: {e}")
    return None


def save_to_storage(filename: str, data: str) -> None:
    """Save data to a file in the storage directory."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CONFIG_DIR / filename
        file_path.write_text(data)
        # Ensure only user can read/write the file
        file_path.chmod(0o600)
    except Exception as e:
        st.write(f"Debug: Error saving {filename}: {e}")


def _api_response_callback(
    request: httpx.Request | None,
    response: httpx.Response | object | None,
    error: Exception | None,
    tab: DeltaGenerator,
    response_state: dict[str, tuple[httpx.Request | None, httpx.Response | object | None]],
):
    """
    Handle an API response by storing it to state and rendering it.
    Safely handles None request objects.
    """
    response_id = datetime.now().isoformat()
    
    try:
        # Safely store response in state
        response_state[response_id] = (request, response)
        
        # Handle error if present
        if error:
            _render_error(error)
            
        # Render the response (our updated function handles None requests)
        _render_api_response(request, response, response_id, tab)
    except Exception as e:
        # Fallback if any part of the callback process fails
        st.error(f"Error in API response handling: {str(e)}")
        
        # Try to render the response directly if possible
        try:
            if isinstance(response, httpx.Response):
                st.code(response.text, language="json")
            elif response is not None:
                st.write(response)
        except:
            # Last resort fallback
            st.info("Response available but couldn't be rendered properly")


def _tool_output_callback(
    tool_output: ToolResult, tool_id: str, tool_state: dict[str, ToolResult]
):
    """Handle a tool output by storing it to state and rendering it."""
    tool_state[tool_id] = tool_output
    _render_message(Sender.TOOL, tool_output)


def _render_api_response(
    request: httpx.Request | None,
    response: httpx.Response | object | None,
    response_id: str,
    tab: DeltaGenerator,
):
    """Safely render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            
            # Safely handle request which might be None
            if request is not None:
                try:
                    st.markdown(
                        f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
                    )
                    st.json(request.read().decode())
                except Exception as e:
                    st.error(f"Error rendering request: {str(e)}")
            else:
                st.info("No request information available")
            
            st.markdown("---")
            
            # Safely handle response
            if isinstance(response, httpx.Response):
                try:
                    st.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    st.json(response.text)
                except Exception as e:
                    st.error(f"Error rendering response: {str(e)}")
            else:
                st.write(response)


def _render_error(error: Exception):
    """Safely render an error with proper error handling for different types"""
    try:
        if isinstance(error, RateLimitError):
            body = "You have been rate limited."
            # Safely access rate limit information
            if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                retry_after = error.response.headers.get("retry-after")
                if retry_after:
                    body += f" **Retry after {str(timedelta(seconds=int(retry_after)))} (HH:MM:SS).** See API documentation for more details."
            
            # Safely access error message
            if hasattr(error, 'message'):
                body += f"\n\n{error.message}"
        else:
            body = str(error)
            body += "\n\n**Traceback:**"
            try:
                lines = "\n".join(traceback.format_exception(error))
                body += f"\n\n```{lines}```"
            except:
                # Fallback if exception formatting fails
                body += "\n\n```Unable to format traceback```"
        
        # Safely save error to storage
        try:
            save_to_storage(f"error_{datetime.now().timestamp()}.md", body)
        except Exception as storage_error:
            st.warning(f"Could not save error details: {str(storage_error)}")
        
        # Display error in UI without any icon parameter to avoid compatibility issues
        st.error(f"**{error.__class__.__name__}**\n\n{body}")
    except Exception as e:
        # Fallback if error rendering itself fails
        st.error(f"Error occurred, but could not render details properly: {str(e)}")


def _render_message(
    sender: Sender,
    message: str | BetaContentBlockParam | ToolResult,
):
    """Convert input from the user or output from the agent to a streamlit message."""
    # streamlit's hotreloading breaks isinstance checks, so we need to check for class names
    is_tool_result = not isinstance(message, str | dict)
    if not message or (
        is_tool_result
        and st.session_state.hide_images
        and not hasattr(message, "error")
        and not hasattr(message, "output")
    ):
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
            # Safely get the message type with a fallback to "unknown"
            message_type = message.get("type", "unknown")
            
            if message_type == "text":
                # Safely get text content
                text_content = message.get("text", "")
                st.write(text_content)
                
            elif message_type == "thinking":
                thinking_content = message.get("thinking", "")
                st.markdown(f"[Thinking]\n\n{thinking_content}")
                
            elif message_type == "tool_use":
                # Safely access name and input fields with fallbacks
                name = message.get("name", message.get("tool_use", {}).get("name", message.get("type", "unknown")))
                input_data = message.get("input", message.get("tool_use", {}).get("input", {}))
                st.code(f'Tool Use: {name}\nInput: {json.dumps(input_data, indent=2)}')
                
            elif "text" in message:
                # Fallback for dictionaries that have text but no type
                st.write(message["text"])
                
            elif "content" in message:
                # Fallback for dictionaries that have content but no type
                st.write(message["content"])
                
            else:
                # Last resort fallback - just display the message as JSON
                try:
                    st.code(json.dumps(message, indent=2, default=str))
                except Exception as e:
                    st.error(f"Could not render message: {e}")
        else:
            st.markdown(message)


if __name__ == "__main__":
    asyncio.run(main())