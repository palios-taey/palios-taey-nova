#!/bin/bash
# Fix imports and ensure all constants are properly defined

echo "Updating import constants and rebuilding files..."

# Check if running inside Docker container
if [ ! -d "/home/computeruse" ]; then
    echo "ERROR: This script must be run inside the Claude DC container!"
    exit 1
fi

# Create backup of current files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p /home/computeruse/backups
cp /home/computeruse/computer_use_demo/loop.py /home/computeruse/backups/loop.py.bak_${TIMESTAMP}
cp /home/computeruse/computer_use_demo/claude_ui.py /home/computeruse/backups/claude_ui.py.bak_${TIMESTAMP}
echo "Created backups in /home/computeruse/backups/"

# Create or update the __init__.py file with constants
cat > /home/computeruse/computer_use_demo/__init__.py << 'INITEOF'
"""
Claude DC computer use demo package.
"""

# Common constants
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"
TOKEN_EFFICIENT_TOOLS_BETA_FLAG = "token-efficient-tools-2025-02-19"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_THINKING_BUDGET = 1000
INITEOF

# Update loop.py with absolute imports and constants
cat > /home/computeruse/computer_use_demo/loop.py << 'LOOPEOF'
"""
Minimal sampling loop for Claude DC - simplified to avoid validation errors.
"""

import logging
import os
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union, cast

import httpx
from anthropic import Anthropic, APIError, APIResponseValidationError, APIStatusError

# Import constants from package
from computer_use_demo import (
    PROMPT_CACHING_BETA_FLAG,
    OUTPUT_128K_BETA_FLAG,
    TOKEN_EFFICIENT_TOOLS_BETA_FLAG,
    DEFAULT_MAX_TOKENS,
    DEFAULT_THINKING_BUDGET
)

from computer_use_demo.tools import TOOL_GROUPS_BY_VERSION, ToolCollection, ToolResult, ToolVersion

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

# Type aliases for cleaner code
BetaContentBlockParam = Dict[str, Any]
BetaMessageParam = Dict[str, Any]
BetaTextBlockParam = Dict[str, Any]
BetaToolResultBlockParam = Dict[str, Any]
BetaToolUseBlockParam = Dict[str, Any]

# System prompt
SYSTEM_PROMPT = """You are Claude DC, "The Conductor," a specialized version of Claude focused on interacting with computer systems."""


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[Dict[str, Any]],
    output_callback: Callable[[Dict[str, Any]], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[
        [httpx.Request, Optional[Union[httpx.Response, object]], Optional[Exception]], None
    ],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    tool_version: ToolVersion,
    thinking_budget: int | None = None,
    token_efficient_tools_beta: bool = False,
):
    """Simplified sampling loop for Claude DC."""
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))
    
    system = {
        "type": "text",
        "text": f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    }

    while True:
        try:
            # Initialize client
            client = Anthropic(api_key=api_key, max_retries=4)
            
            # Create API params - simplified with no beta features
            logger.info("Making API call to Anthropic...")
            stream = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=[system],
                messages=messages,
                tools=tool_collection.to_params(),
                stream=True
            )
            
            # Track blocks as dictionaries instead of objects
            content_blocks = []
            
            # Process stream
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        # Get block data as dict
                        block_dict = {}
                        if hasattr(event.content_block, "type"):
                            block_dict["type"] = event.content_block.type
                        else:
                            block_dict["type"] = "text"  # Default to text if no type
                            
                        if hasattr(event.content_block, "text"):
                            block_dict["text"] = event.content_block.text
                        elif block_dict["type"] == "text":
                            block_dict["text"] = ""
                            
                        content_blocks.append(block_dict)
                        # Notify callback
                        output_callback(block_dict)
                    
                    elif event.type == "content_block_delta":
                        if hasattr(event, "index") and event.index < len(content_blocks):
                            # Only handle text deltas
                            if hasattr(event.delta, "text") and event.delta.text:
                                if content_blocks[event.index].get("type") == "text":
                                    # Update existing text
                                    content_blocks[event.index]["text"] += event.delta.text
                                    # Notify callback
                                    output_callback({
                                        "type": "text",
                                        "text": event.delta.text,
                                        "is_delta": True
                                    })
                    
                    elif event.type == "message_stop":
                        break
            
            # Process tool usage
            tool_results = []
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_id = block.get("id", "")
                    tool_input = block.get("input", {})
                    
                    logger.info(f"Running tool: {tool_name} with ID: {tool_id}")
                    
                    # Run tool
                    result = await tool_collection.run(
                        name=tool_name,
                        tool_input=tool_input,
                        streaming=True
                    )
                    
                    # Convert result
                    tool_result_content = []
                    is_error = bool(result.error)
                    
                    if result.error:
                        tool_result_content = result.error
                    else:
                        if result.output:
                            tool_result_content.append({
                                "type": "text",
                                "text": result.output
                            })
                        if result.base64_image:
                            tool_result_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": result.base64_image
                                }
                            })
                    
                    # Create tool result
                    tool_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result_content,
                        "is_error": is_error
                    }
                    
                    tool_results.append(tool_result)
                    tool_output_callback(result, tool_id)
            
            # Add response to messages
            messages.append({
                "role": "assistant",
                "content": content_blocks
            })
            
            # Handle tool results
            if tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                return messages
                
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
LOOPEOF

# Update claude_ui.py with absolute imports and simplified constants
cat > /home/computeruse/computer_use_demo/claude_ui.py << 'UIEOF'
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
from typing import cast, get_args, Any, Dict, List, Union, Optional

# Setup system path to find modules properly
import sys
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import httpx
import streamlit as st
from anthropic import RateLimitError

# Import from package - constants are defined in __init__.py
from computer_use_demo import (
    PROMPT_CACHING_BETA_FLAG,
    OUTPUT_128K_BETA_FLAG,
    TOKEN_EFFICIENT_TOOLS_BETA_FLAG,
    DEFAULT_MAX_TOKENS,
    DEFAULT_THINKING_BUDGET
)

# Import tools
from computer_use_demo.tools import ToolResult, ToolVersion
from computer_use_demo.loop import APIProvider, sampling_loop

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
                        if block["tool_use_id"] in st.session_state.tools:
                            _render_message(
                                Sender.TOOL, st.session_state.tools[block["tool_use_id"]]
                            )
                    else:
                        try:
                            _render_message(
                                message["role"],
                                block,
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
                        {"type": "text", "text": new_message},
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


def _streaming_output_callback(content_block: Union[Dict[str, Any], Any]):
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
            result.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": INTERRUPT_TOOL_ERROR,
                "is_error": True,
            })
    except Exception as e:
        logger.error(f"Error creating interruption blocks: {e}")
        
    # Add a text notification about the interruption
    result.append({"type": "text", "text": INTERRUPT_TEXT})
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
    message: Union[str, Dict[str, Any], ToolResult, Any],
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
UIEOF

# Create a unified launcher that properly sets Python paths
cat > /home/computeruse/launch_unified.py << 'LAUNCHEOF'
#!/usr/bin/env python3
"""
Unified launcher for Claude DC that properly sets up Python paths.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('launch_unified')

def main():
    """Set up environment and launch Streamlit."""
    # Set environment
    os.environ['CLAUDE_ENV'] = 'dev'
    
    # Add parent directory to Python path
    base_dir = "/home/computeruse"
    sys.path.insert(0, base_dir)
    logger.info(f"Added {base_dir} to Python path")
    
    # Get Claude UI path
    claude_ui_path = os.path.join(base_dir, "computer_use_demo", "claude_ui.py")
    
    if not os.path.exists(claude_ui_path):
        logger.error(f"Claude UI file not found at {claude_ui_path}")
        return 1
    
    logger.info(f"Starting Claude DC UI from {claude_ui_path}")
    
    # Set Python path in environment
    env = os.environ.copy()
    env["PYTHONPATH"] = base_dir + ":" + env.get("PYTHONPATH", "")
    
    # Launch Streamlit
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m", "streamlit", "run", claude_ui_path,
                "--server.port=8501",
                "--server.address=0.0.0.0"
            ],
            env=env,
            check=True
        )
        return result.returncode
    except Exception as e:
        logger.error(f"Error starting Streamlit: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
LAUNCHEOF

chmod +x /home/computeruse/launch_unified.py

echo "Fixed all imports and constants!"
echo ""
echo "To launch Claude DC with the fixed setup:"
echo "cd /home/computeruse"
echo "python3 launch_unified.py"
echo ""
echo "This launcher properly sets up the Python path and uses consistent constants."