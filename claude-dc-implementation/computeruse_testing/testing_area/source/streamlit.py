"""
Streamlit application for Claude Computer Use Demo.
This version includes proper support for streaming with tools.
"""

import asyncio
import base64
import os
import subprocess
import sys
import traceback
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
from pathlib import PosixPath
from typing import cast, get_args, Any, Dict, Union, Optional

# Define StrEnum for Python 3.10 compatibility
if sys.version_info < (3, 11):
    # Backport of StrEnum for Python < 3.11
    class StrEnum(str, Enum):
        """
        Enum where members are also (and must be) strings.
        """
        def __new__(cls, *values):
            if len(values) > 3:
                raise TypeError(f'too many arguments for str(): {values!r}')
            if len(values) == 1:
                # Construct by name (default Enum behavior)
                obj = str.__new__(cls, values[0])
            else:
                # Construct the normal way
                obj = str.__new__(cls)
            obj._value_ = values[0]
            return obj
        
        def _generate_next_value_(name, start, count, last_values):
            """Return the name as the value."""
            return name
else:
    from enum import StrEnum

import httpx
import streamlit as st
from anthropic import RateLimitError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

# Import constants from module's __init__.py
# Try different import paths based on how the module is being run
try:
    # Direct import when the module is in path
    from computer_use_demo import (
        PROMPT_CACHING_BETA_FLAG,
        OUTPUT_128K_BETA_FLAG,
        TOKEN_EFFICIENT_TOOLS_BETA_FLAG,
        DEFAULT_MAX_TOKENS,
        DEFAULT_THINKING_BUDGET,
        APIProvider,
        ToolVersion,
    )
except ImportError:
    # Relative import when running from within the package
    try:
        # Import from current package using relative import
        from . import (
            PROMPT_CACHING_BETA_FLAG,
            OUTPUT_128K_BETA_FLAG,
            TOKEN_EFFICIENT_TOOLS_BETA_FLAG,
            DEFAULT_MAX_TOKENS,
            DEFAULT_THINKING_BUDGET,
            APIProvider,
            ToolVersion,
        )
    except ImportError:
        # Last resort - define constants directly (for standalone running)
        import logging
        logging.warning("Using fallback constants - some features may be limited")
        PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
        OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"
        TOKEN_EFFICIENT_TOOLS_BETA_FLAG = "token-efficient-tools-2025-02-19"
        DEFAULT_MAX_TOKENS = 65536
        DEFAULT_THINKING_BUDGET = 32768
        
        # Define APIProvider as a class with string constants
        class APIProvider:
            ANTHROPIC = "anthropic"
            BEDROCK = "bedrock"
            VERTEX = "vertex"
            
        # Define ToolVersion
        ToolVersion = "computer_use_20250124"

# Conditional import for different Streamlit versions
try:
    # Try newer versions first
    from streamlit.delta_generator import DeltaGenerator
except ImportError:
    try:
        # Try alternative import path
        from streamlit import DeltaGenerator
    except ImportError:
        # Last resort - try to get it from st directly
        DeltaGenerator = type(st.empty())
except ModuleNotFoundError:
    # Fallback for newer Streamlit versions where the import structure changed
    from streamlit import DeltaGenerator

# Import tools module using flexible import paths
try:
    # Direct package import
    from computer_use_demo.tools import ToolResult, ToolVersion as ToolVersion_
    from computer_use_demo.loop import sampling_loop
except ImportError:
    try:
        # Relative import when part of package
        from .tools import ToolResult, ToolVersion as ToolVersion_
        from .loop import sampling_loop
    except ImportError:
        # Fallback for standalone execution
        import logging
        logging.warning("Using mock tool imports - functionality may be limited")
        
        # Define minimal ToolResult for UI display
        @dataclass
        class ToolResult:
            output: Optional[str] = None
            error: Optional[str] = None
            base64_image: Optional[str] = None
            system: Optional[str] = None
        
        # Define mock sampling_loop
        async def sampling_loop(*args, **kwargs):
            logging.error("sampling_loop not available - imports failed")
            raise ImportError("Cannot import sampling_loop function")
        
        # Use ToolVersion from previous import if available
        if 'ToolVersion' not in locals():
            ToolVersion_ = "computer_use_20250124"
            
# Use ToolVersion_ to avoid conflict with the imported type hint
ToolVersion = ToolVersion_

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.streamlit')

PROVIDER_TO_DEFAULT_MODEL_NAME: dict[str, str] = {
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
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_key" not in st.session_state:
        # Try to load API key from file first, then environment
        st.session_state.api_key = load_from_storage("api_key") or os.getenv(
            "ANTHROPIC_API_KEY", ""
        )
    if "provider" not in st.session_state:
        st.session_state.provider = (
            os.getenv("API_PROVIDER", "anthropic") or APIProvider.ANTHROPIC
        )
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
    if "tool_placeholders" not in st.session_state:
        st.session_state.tool_placeholders = {}
    if "only_n_most_recent_images" not in st.session_state:
        st.session_state.only_n_most_recent_images = 3
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = load_from_storage("system_prompt") or ""
    if "hide_images" not in st.session_state:
        st.session_state.hide_images = False
    if "token_efficient_tools_beta" not in st.session_state:
        st.session_state.token_efficient_tools_beta = False
    if "in_sampling_loop" not in st.session_state:
        st.session_state.in_sampling_loop = False
    # Streaming-specific state
    if "current_message_placeholder" not in st.session_state:
        st.session_state.current_message_placeholder = None
    if "current_message_text" not in st.session_state:
        st.session_state.current_message_text = ""
    if "current_thinking_placeholder" not in st.session_state:
        st.session_state.current_thinking_placeholder = None
    if "current_thinking_text" not in st.session_state:
        st.session_state.current_thinking_text = ""


def _reset_model():
    """Reset model configuration."""
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[
        st.session_state.provider
    ]
    _reset_model_conf()


def _reset_model_conf():
    """Reset model configuration based on selected model."""
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


@contextmanager
def track_sampling_loop():
    """Track when we're in a sampling loop for interrupt handling."""
    st.session_state.in_sampling_loop = True
    try:
        yield
    finally:
        st.session_state.in_sampling_loop = False


async def main():
    """Main Streamlit application."""
    setup_state()

    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

    st.title("Claude Computer Use Demo")

    if not os.getenv("HIDE_WARNING", False):
        st.warning(WARNING_TEXT)

    with st.sidebar:
        st.markdown("### Claude DC - Tier 4 Features")
        
        # Show status of Phase 2 enhancements
        st.info("📡 Streaming Responses: **Enabled**")
        st.info("🔄 Tool Integration in Stream: **Enabled**")
        st.info("💾 Prompt Caching: **Enabled**")
        st.info("📊 128K Extended Output: **Enabled**")
        st.info("🛠️ Real-Time Tool Output: **Enabled**")
        
        st.markdown("---")
        
        def _reset_api_provider():
            if st.session_state.provider_radio != st.session_state.provider:
                _reset_model()
                st.session_state.provider = st.session_state.provider_radio
                st.session_state.auth_validated = False

        provider_options = [APIProvider.ANTHROPIC, APIProvider.BEDROCK, APIProvider.VERTEX]
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
        versions = get_args(ToolVersion)
        st.radio(
            "Tool Versions",
            key="tool_versions",
            options=versions,
            index=versions.index(st.session_state.tool_version),
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
        # Render past chats
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    # The tool result we send back to the Anthropic API isn't sufficient to render all details,
                    # so we store the tool use responses
                    if isinstance(block, dict) and block["type"] == "tool_result":
                        _render_message(
                            Sender.TOOL, st.session_state.tools[block["tool_use_id"]]
                        )
                    else:
                        _render_message(
                            message["role"],
                            cast(Union[BetaContentBlockParam, ToolResult], block),
                        )

        # Render past HTTP exchanges
        for identity, (request, response) in st.session_state.responses.items():
            _render_api_response(request, response, identity, http_logs)

        # Handle new user messages
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

        # Only respond to user messages
        if most_recent_message["role"] is not Sender.USER:
            return

        # Initialize placeholders for streaming
        with st.chat_message("assistant"):
            st.session_state.current_message_placeholder = st.empty()
            st.session_state.current_message_text = ""
            st.session_state.current_thinking_placeholder = None
            st.session_state.current_thinking_text = ""

        with track_sampling_loop():
            # Run the agent sampling loop with streaming
            st.session_state.messages = await sampling_loop(
                system_prompt_suffix=st.session_state.custom_system_prompt,
                model=st.session_state.model,
                provider=st.session_state.provider,
                messages=st.session_state.messages,
                output_callback=_streaming_output_callback,
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


def _streaming_output_callback(content_block: Union[BetaContentBlockParam, Dict[str, Any]]):
    """Handle streamed content from Claude API."""
    # Handle streamed content (deltas with is_delta flag)
    if isinstance(content_block, dict) and content_block.get("is_delta", False):
        if content_block["type"] == "text":
            # Update text message with delta
            delta_text = content_block.get("text", "")
            st.session_state.current_message_text += delta_text
            if st.session_state.current_message_placeholder:
                st.session_state.current_message_placeholder.markdown(
                    st.session_state.current_message_text
                )
                
        elif content_block["type"] == "thinking":
            # Update thinking block with delta
            delta_thinking = content_block.get("thinking", "")
            if not st.session_state.current_thinking_text:
                # First thinking content - create a new thinking section
                with st.chat_message("assistant"):
                    st.session_state.current_thinking_placeholder = st.empty()
                    st.session_state.current_thinking_text = f"**Thinking:**\n\n{delta_thinking}"
                    st.session_state.current_thinking_placeholder.markdown(
                        st.session_state.current_thinking_text
                    )
            else:
                # Update existing thinking block
                st.session_state.current_thinking_text += delta_thinking
                if st.session_state.current_thinking_placeholder:
                    st.session_state.current_thinking_placeholder.markdown(
                        st.session_state.current_thinking_text
                    )
        return
        
    # Handle complete content blocks
    if isinstance(content_block, dict):
        if content_block.get("type") == "text":
            # Normal text content from assistant
            text_content = content_block.get("text", "")
            st.session_state.current_message_text = text_content
            if st.session_state.current_message_placeholder:
                st.session_state.current_message_placeholder.markdown(text_content)
                
        elif content_block.get("type") == "thinking":
            # Complete thinking block
            thinking_content = content_block.get("thinking", "")
            with st.chat_message("assistant"):
                st.write(f"**Thinking:**\n\n{thinking_content}")
                
        elif content_block.get("type") == "tool_use":
            # Tool use notification
            tool_name = content_block.get("name", "unknown")
            tool_input = content_block.get("input", {})
            # Add to current message 
            st.session_state.current_message_text += f"\n\n**Using tool: {tool_name}**"
            if st.session_state.current_message_placeholder:
                st.session_state.current_message_placeholder.markdown(
                    st.session_state.current_message_text
                )
            # Also display as code for more detail
            with st.chat_message("assistant"):
                st.code(f"Using tool: {tool_name}\nWith input: {tool_input}")
    else:
        # Fallback for other content types (complete blocks)
        _render_message(Sender.BOT, content_block)


def maybe_add_interruption_blocks():
    """Add interruption context if sampling was interrupted."""
    if not st.session_state.in_sampling_loop:
        return []
    
    # If this function is called while we're in the sampling loop, 
    # we can assume that the previous sampling loop was interrupted
    result = []
    last_message = st.session_state.messages[-1]
    
    # Find any incomplete tool calls that need to be marked as interrupted
    previous_tool_use_ids = [
        block["id"] 
        for block in last_message["content"] 
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]
    
    # Create error results for any interrupted tool calls
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
        
    # Add a text notification about the interruption
    result.append(BetaTextBlockParam(type="text", text=INTERRUPT_TEXT))
    return result


def _tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    """Handle tool execution results including streaming chunks."""
    # Check if this is a streaming chunk or final result
    is_streaming = (
        hasattr(tool_output, 'output') and 
        tool_output.output and 
        not hasattr(tool_output, 'base64_image') and
        not hasattr(tool_output, 'error')
    )
    
    # For streaming output, update existing tool output if possible
    if is_streaming:
        # Get or create placeholder for streaming content
        if tool_id not in st.session_state.tools:
            # First chunk for this tool - create placeholder
            with st.chat_message(Sender.TOOL.value):
                placeholder = st.empty()
                st.session_state.tools[tool_id] = tool_output
                # Also store the placeholder in a separate dict
                if 'tool_placeholders' not in st.session_state:
                    st.session_state.tool_placeholders = {}
                st.session_state.tool_placeholders[tool_id] = placeholder
                placeholder.code(tool_output.output, language="bash")
        else:
            # Append to existing tool output
            existing = st.session_state.tools[tool_id]
            if hasattr(existing, 'output'):
                existing.output += tool_output.output
                # Update placeholder with latest content
                if 'tool_placeholders' in st.session_state and tool_id in st.session_state.tool_placeholders:
                    st.session_state.tool_placeholders[tool_id].code(existing.output, language="bash")
    else:
        # This is a final result or non-streaming tool output
        # Store tool result for future reference
        tool_state[tool_id] = tool_output
        
        # Update existing placeholder if there is one, otherwise render new message
        if 'tool_placeholders' in st.session_state and tool_id in st.session_state.tool_placeholders:
            # We already have a placeholder - update it
            if hasattr(tool_output, 'error') and tool_output.error:
                # Display error
                st.error(tool_output.error)
            elif hasattr(tool_output, 'base64_image') and tool_output.base64_image:
                # Handle image result
                _render_message(Sender.TOOL, tool_output)
            else:
                # Just update placeholder if this is just text output
                placeholder = st.session_state.tool_placeholders[tool_id]
                placeholder.code(tool_output.output, language="bash")
        else:
            # No placeholder exists yet - render as new message
            _render_message(Sender.TOOL, tool_output)


def _api_response_callback(
    request: httpx.Request,
    response: Union[httpx.Response, object, None],
    error: Optional[Exception],
    tab: DeltaGenerator,
    response_state: dict,
):
    """Handle API response callbacks."""
    # Generate a unique ID for this response
    response_id = datetime.now().isoformat()
    response_state[response_id] = (request, response)
    
    # Handle any errors
    if error:
        _render_error(error)
        
    # Render the API response in the logs tab
    _render_api_response(request, response, response_id, tab)


def _render_api_response(
    request: httpx.Request,
    response: Union[httpx.Response, object, None],
    response_id: str,
    tab: DeltaGenerator,
):
    """Render API request/response in the logs tab."""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            
            # Request details
            if request:
                st.markdown(
                    f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
                )
                try:
                    st.json(request.read().decode())
                except Exception:
                    st.text("Could not decode request body")
                    
            st.markdown("---")
            
            # Response details
            if isinstance(response, httpx.Response):
                st.markdown(
                    f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                )
                try:
                    st.json(response.text)
                except Exception:
                    st.text(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            else:
                st.write(response)


def _render_error(error: Exception):
    """Render an error message with traceback."""
    if isinstance(error, RateLimitError):
        body = "You have been rate limited."
        if retry_after := getattr(error, "headers", {}).get("retry-after"):
            body += f" **Retry after {str(timedelta(seconds=int(retry_after)))} (HH:MM:SS).** See the API [documentation](https://docs.anthropic.com/en/api/rate-limits) for more details."
        body += f"\n\n{error}"
    else:
        body = str(error)
        body += "\n\n**Traceback:**"
        lines = "\n".join(traceback.format_exception(error))
        body += f"\n\n```{lines}```"
        
    # Log the error
    save_to_storage(f"error_{datetime.now().timestamp()}.md", body)
    # Display to user
    st.error(f"**{error.__class__.__name__}**\n\n{body}", icon="🛑")


def _render_message(
    sender: Sender,
    message: Union[str, BetaContentBlockParam, ToolResult, Dict[str, Any]],
):
    """Render a message in the chat UI."""
    # Skip empty messages or hidden images
    is_tool_result = not isinstance(message, (str, dict))
    if not message or (
        is_tool_result
        and st.session_state.hide_images
        and not hasattr(message, "error")
        and not hasattr(message, "output")
    ):
        return
        
    # Render based on message type
    with st.chat_message(sender.value):
        if is_tool_result:
            # Tool output
            message = cast(ToolResult, message)
            if message.output:
                if hasattr(message, "__class__") and message.__class__.__name__ == "CLIResult":
                    st.code(message.output)
                else:
                    st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image and not st.session_state.hide_images:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict):
            # Content block
            if message.get("type") == "text":
                st.write(message.get("text", ""))
            elif message.get("type") == "thinking":
                st.markdown(f"**Thinking:**\n\n{message.get('thinking', '')}")
            elif message.get("type") == "tool_use":
                st.code(f'Tool Use: {message.get("name")}\nInput: {message.get("input")}')
            else:
                # Unknown block type
                st.write(message)
        else:
            # Plain text message
            st.markdown(message)


def validate_auth(provider: str, api_key: str | None):
    """Validate authentication credentials."""
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


if __name__ == "__main__":
    asyncio.run(main())