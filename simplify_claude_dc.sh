#!/bin/bash
# Script to simplify Claude DC configuration

echo "Simplifying Claude DC configuration..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current loop.py
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p /home/computeruse/backups
cp /home/computeruse/computer_use_demo/loop.py /home/computeruse/backups/loop.py.bak_${TIMESTAMP}
cp /home/computeruse/computer_use_demo/claude_ui.py /home/computeruse/backups/claude_ui.py.bak_${TIMESTAMP}
echo "Created backups in /home/computeruse/backups/"

# Update the loop.py file to simplify beta handling
cat > /home/computeruse/computer_use_demo/loop.py << 'EOF'
"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
Simplified version focusing on core functionality.
"""

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
if 'CLAUDE_ENV' in os.environ:
    MODE = os.environ['CLAUDE_ENV']
else:
    MODE = 'live'
    
logger.info(f"Claude DC initialized in {MODE} mode")

# Beta feature flags
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

# Default token settings for output
DEFAULT_MAX_TOKENS = 32000  # Reduced from 65536
DEFAULT_THINKING_BUDGET = 4000  # Reduced from 32768

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


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


# System prompt (simplified)
SYSTEM_PROMPT = """<SYSTEM_CAPABILITY>
* You are Claude DC, "The Conductor," a specialized version of Claude focused on interacting with computer systems.
* You are utilizing an Ubuntu virtual machine with """ + platform.machine() + """ architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* The current date is """ + datetime.today().strftime('%A, %B %-d, %Y') + """.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* This environment is YOUR home - maintain it with care, as its stability directly affects your ability to function.
* When planning complex operations, take time to think through the steps before executing tools.
* Always verify tool outputs to ensure operations completed as expected.
* When encountering errors, first analyze the error message carefully, then search for log files that might provide more context.
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
    max_tokens: int = DEFAULT_MAX_TOKENS,
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
        # Prepare API call parameters
        api_params = {
            "max_tokens": max_tokens,
            "messages": messages,
            "model": model,
            "system": [system],
            "tools": tool_collection.to_params(),
            "stream": True,  # Enable streaming for long responses
        }
        
        # Add thinking parameters if needed
        if thinking_budget:
            api_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
            
        # Add prompt caching
        if provider == APIProvider.ANTHROPIC:
            extra_headers = {"x-beta": PROMPT_CACHING_BETA_FLAG}
            api_params["extra_headers"] = extra_headers
            _inject_prompt_caching(messages)
            # Use type ignore to bypass TypedDict check until SDK types are updated
            system["cache_control"] = {"type": "ephemeral"}  # type: ignore
            
        logger.info("Calling Anthropic API with streaming enabled")
            
        # Call the API with streaming enabled
        try:
            # Initialize client
            client = Anthropic(api_key=api_key, max_retries=4)
            stream = client.messages.create(**api_params)
            
            # Process the stream
            content_blocks = []
            
            # Stream and process results
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        # New content block started
                        current_block = event.content_block
                        content_blocks.append(current_block)
                        
                        # Safe handling of content blocks
                        try:
                            output_callback(current_block)
                        except Exception as e:
                            logger.error(f"Error in output callback: {e}")
                    
                    elif event.type == "content_block_delta":
                        # Content block delta received
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Handle text delta
                            if hasattr(event.delta, "text") and event.delta.text:
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
            
            # Create a response structure
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
            logger.error(f"API error: {e}")
            api_response_callback(e.request, e.response, e)
            return messages
        except APIError as e:
            logger.error(f"API error: {e}")
            api_response_callback(e.request, e.body, e)
            return messages
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
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

        # Set up streaming for tool output
        tool_collection.set_stream_callback(
            lambda chunk, tool_id: tool_output_callback(
                ToolResult(output=chunk, error=None), 
                tool_id
            )
        )
        
        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
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
                    streaming=True,
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


def _response_to_params(
    response: BetaMessage,
) -> list[BetaContentBlockParam]:
    res: list[BetaContentBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            if block.text:
                res.append(BetaTextBlockParam(type="text", text=block.text))
        else:
            # Handle tool use blocks normally
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res


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
EOF

# Update the claude_ui.py file to simplify UI elements and properly handle different block types
cat > /home/computeruse/computer_use_demo/claude_ui.py << 'EOF'
"""
Streamlit application for Claude Computer Use Demo.
Simplified version for stability.
"""

import asyncio
import base64
import os
import subprocess
import traceback
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import cast, get_args, Any, Dict, Union, Optional

# Setup system path to find modules properly
import sys
parent_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import httpx
import streamlit as st
from anthropic import RateLimitError

# Manually set these to avoid import issues
DeltaGenerator = None

from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

# Import modules with fallbacks
try:
    from computer_use_demo.tools import ToolResult, ToolVersion
    from computer_use_demo.loop import (
        APIProvider, 
        sampling_loop,
        PROMPT_CACHING_BETA_FLAG,
        DEFAULT_MAX_TOKENS,
        DEFAULT_THINKING_BUDGET
    )
except ImportError:
    from tools import ToolResult, ToolVersion
    from loop import (
        APIProvider, 
        sampling_loop,
        PROMPT_CACHING_BETA_FLAG,
        DEFAULT_MAX_TOKENS,
        DEFAULT_THINKING_BUDGET
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.streamlit')

PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-7-sonnet-20250219",
}


@dataclass(kw_only=True, frozen=True)
class ModelConfig:
    tool_version: ToolVersion
    max_output_tokens: int
    default_output_tokens: int
    has_thinking: bool = False


SONNET_3_7 = ModelConfig(
    tool_version="computer_use_20250124",
    max_output_tokens=32000,  # Reduced from 128K
    default_output_tokens=16384,
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


def _reset_model():
    """Reset model configuration."""
    st.session_state.model = PROVIDER_TO_DEFAULT_MODEL_NAME[
        cast(APIProvider, st.session_state.provider)
    ]
    _reset_model_conf()


def _reset_model_conf():
    """Reset model configuration based on selected model."""
    model_conf = SONNET_3_7
    st.session_state.tool_version = model_conf.tool_version
    st.session_state.has_thinking = model_conf.has_thinking
    st.session_state.output_tokens = model_conf.default_output_tokens
    st.session_state.max_output_tokens = model_conf.max_output_tokens
    st.session_state.thinking_budget = int(model_conf.default_output_tokens / 4)


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
        
        st.markdown("---")
        
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
            "Max Output Tokens",
            min_value=1000,
            max_value=65536,
            value=DEFAULT_MAX_TOKENS,
            step=1000,
            key="output_tokens"
        )

        st.number_input(
            "Thinking Budget",
            min_value=1000,
            max_value=8000,
            value=DEFAULT_THINKING_BUDGET,
            step=1000,
            key="thinking_budget"
        )

        if st.button("Reset", type="primary"):
            with st.spinner("Resetting..."):
                st.session_state.clear()
                setup_state()

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
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        _render_message(
                            Sender.TOOL, st.session_state.tools[block["tool_use_id"]]
                        )
                    else:
                        try:
                            _render_message(
                                message["role"],
                                cast(Union[BetaContentBlockParam, ToolResult], block),
                            )
                        except Exception as e:
                            logger.error(f"Error rendering message: {e}")
                            st.error(f"Error rendering message: {str(e)}")

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
                thinking_budget=st.session_state.thinking_budget,
                token_efficient_tools_beta=False,  # Always disable token efficient tools
            )


def _streaming_output_callback(content_block: Union[BetaContentBlockParam, Dict[str, Any]]):
    """Handle streamed content from Claude API."""
    try:
        # Handle streamed content (deltas with is_delta flag)
        if isinstance(content_block, dict) and content_block.get("is_delta", False):
            if content_block.get("type") == "text":
                # Update text message with delta
                delta_text = content_block.get("text", "")
                st.session_state.current_message_text += delta_text
                if st.session_state.current_message_placeholder:
                    st.session_state.current_message_placeholder.markdown(
                        st.session_state.current_message_text
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
        
    except Exception as e:
        logger.error(f"Error in streaming output callback: {e}")
        st.error(f"Error processing response: {str(e)}")


def maybe_add_interruption_blocks():
    """Add interruption context if sampling was interrupted."""
    if not st.session_state.in_sampling_loop:
        return []
    
    # If this function is called while we're in the sampling loop, 
    # we can assume that the previous sampling loop was interrupted
    result = []
    try:
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
    except Exception as e:
        logger.error(f"Error creating interruption blocks: {e}")
        
    # Add a text notification about the interruption
    result.append(BetaTextBlockParam(type="text", text=INTERRUPT_TEXT))
    return result


def _tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    """Handle tool execution results including streaming chunks."""
    try:
        # This is a final result or non-streaming tool output
        # Store tool result for future reference
        tool_state[tool_id] = tool_output
        
        # Render new message for tool output
        _render_message(Sender.TOOL, tool_output)
    except Exception as e:
        logger.error(f"Error in tool output callback: {e}")
        st.error(f"Error processing tool output: {str(e)}")


def _api_response_callback(
    request: httpx.Request,
    response: Union[httpx.Response, object, None],
    error: Optional[Exception],
    tab: Any,
    response_state: dict,
):
    """Handle API response callbacks."""
    try:
        # Generate a unique ID for this response
        response_id = datetime.now().isoformat()
        response_state[response_id] = (request, response)
        
        # Handle any errors
        if error:
            _render_error(error)
    except Exception as e:
        logger.error(f"Error in API response callback: {e}")


def _render_error(error: Exception):
    """Render an error message with traceback."""
    try:
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
    except Exception as e:
        logger.error(f"Error rendering error message: {e}")
        st.error(f"An error occurred: {str(error)}")


def _render_message(
    sender: Sender,
    message: Union[str, BetaContentBlockParam, ToolResult, Dict[str, Any]],
):
    """Render a message in the chat UI."""
    try:
        # Skip empty messages
        if not message:
            return
        
        # Safely check message type
        message_is_tool_result = False
        if hasattr(message, '__class__') and message.__class__.__name__ == 'ToolResult':
            message_is_tool_result = True
            
        # Render based on message type
        with st.chat_message(sender.value):
            if message_is_tool_result:
                # Safely handle ToolResult
                if hasattr(message, 'output') and message.output:
                    st.code(message.output)
                if hasattr(message, 'error') and message.error:
                    st.error(message.error)
                if hasattr(message, 'base64_image') and message.base64_image:
                    try:
                        st.image(base64.b64decode(message.base64_image))
                    except Exception:
                        st.error("Failed to display image")
            elif isinstance(message, dict):
                # Content block
                if message.get("type") == "text":
                    st.write(message.get("text", ""))
                elif message.get("type") == "tool_use":
                    st.code(f'Tool Use: {message.get("name")}\nInput: {message.get("input")}')
                else:
                    # Unknown block type
                    st.write("Unsupported content type")
            else:
                # Plain text message
                st.markdown(str(message))
    except Exception as e:
        logger.error(f"Error rendering message: {e}")
        st.error("Error rendering message")


def validate_auth(provider: APIProvider, api_key: str | None):
    """Validate authentication credentials."""
    if provider == APIProvider.ANTHROPIC:
        if not api_key:
            return "Enter your Anthropic API key in the sidebar to continue."
    return None


def load_from_storage(filename: str) -> str | None:
    """Load data from a file in the storage directory."""
    try:
        file_path = CONFIG_DIR / filename
        if file_path.exists():
            data = file_path.read_text().strip()
            if data:
                return data
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
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
        logger.error(f"Error saving {filename}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
EOF

cat > /home/computeruse/launch_claude_simplified.py << 'EOF'
#!/usr/bin/env python3
"""
Launcher script for Claude Computer Use Demo.
This avoids the circular import by using a separate launcher file.
"""

import os
import subprocess
import sys

def main():
    # Set environment variables
    os.environ['CLAUDE_ENV'] = 'dev'
    
    # Get the path to the claude_ui.py file
    claude_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "computer_use_demo", "claude_ui.py")
    
    if not os.path.exists(claude_ui_path):
        print(f"ERROR: Claude UI file not found at {claude_ui_path}")
        return 1
        
    print(f"Starting Claude DC UI from {claude_ui_path}")
    
    # Launch the UI using streamlit
    result = subprocess.run([
        "python", "-m", "streamlit", "run", claude_ui_path,
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x /home/computeruse/launch_claude_simplified.py

echo "Simplified Claude DC configured!"
echo ""
echo "To launch Claude DC with simplified settings, run:"
echo "cd /home/computeruse"
echo "python3 launch_claude_simplified.py"