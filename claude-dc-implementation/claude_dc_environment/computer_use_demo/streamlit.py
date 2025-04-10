"""
Entrypoint for Streamlit app, integrating with Anthropic API and tools.
"""

import asyncio
import base64
from functools import partial
from pathlib import PosixPath
from typing import cast
from contextlib import contextmanager
from enum import StrEnum

import httpx
import streamlit as st
from anthropic.types.beta import BetaContentBlockParam, BetaTextBlockParam, BetaToolUseBlockParam
from streamlit.delta_generator import DeltaGenerator

# Change from relative import to absolute import
from loop import APIProvider, sampling_loop
from tools import ToolResult, ToolVersion

# Constants
CONFIG_DIR = PosixPath("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"
STREAMLIT_STYLE = """
<style>
    button[kind=header] { background-color: rgb(255, 75, 75); border: 1px solid rgb(255, 75, 75); color: rgb(255, 255, 255); }
    button[kind=header]:hover { background-color: rgb(255, 51, 51); }
    .stAppDeployButton { visibility: hidden; }
</style>
"""
WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data."
INTERRUPT_TEXT = "(user stopped or interrupted)"
INTERRUPT_TOOL_ERROR = "human stopped or interrupted tool execution"

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "auth_validated" not in st.session_state:
    st.session_state.auth_validated = False
if "model" not in st.session_state:
    st.session_state.model = "claude-3-7-sonnet-20250219"
if "provider" not in st.session_state:
    st.session_state.provider = APIProvider.ANTHROPIC
if "api_key" not in st.session_state:
    # REPLACE "your-api-key-here" WITH YOUR ACTUAL API KEY
    st.session_state.api_key = "your-api-key-here"  # <-- REPLACE THIS WITH YOUR ACTUAL API KEY
if "hide_images" not in st.session_state:
    st.session_state.hide_images = False
if "tool_version" not in st.session_state:
    st.session_state.tool_version = "computer_use_20250124"  # Set the correct tool version string
if "output_tokens" not in st.session_state:
    st.session_state.output_tokens = 64000  # Set to 64K for optimal use
if "thinking" not in st.session_state:
    st.session_state.thinking = True
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = 32000  # Set to 32K for optimal use
if "token_efficient_tools_beta" not in st.session_state:
    st.session_state.token_efficient_tools_beta = True

def validate_auth(provider: APIProvider, api_key: str) -> str | None:
    """Validate API authentication."""
    if provider == APIProvider.ANTHROPIC and not api_key:
        return "API key is required for Anthropic provider."
    return None

def _render_api_response(
    request: httpx.Request,
    response: httpx.Response | object | None,
    response_id: str,
    tab: DeltaGenerator,
):
    """Render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            
            # Safely display request information
            if request is None:
                st.markdown("*No request data available*")
            else:
                try:
                    st.markdown(
                        f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
                    )
                    st.json(request.read().decode())
                except Exception as e:
                    st.markdown(f"*Error displaying request: {str(e)}*")
            
            st.markdown("---")
            
            # Handle response display with careful type checking
            if isinstance(response, httpx.Response):
                # Safely handle streaming responses
                try:
                    st.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    response_text = response.text if hasattr(response, 'text') and callable(response.text) else str(response)
                    st.text(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)
                except Exception as e:
                    st.text(f"Streaming response (content not available): {type(response)}")
                    st.text(f"Headers: {dict(response.headers) if hasattr(response, 'headers') else 'N/A'}")
            elif isinstance(response, dict):
                # Handle our custom dictionary response
                st.markdown(f"`{response.get('status_code', 'N/A')}`")
                headers = response.get('headers', {})
                st.markdown(f"{newline.join(f'`{k}: {v}`' for k, v in headers.items())}")
                st.text("Streaming response (content being processed)")
            elif response is None:
                st.text("No response data available")
            else:
                st.write(response)

def _render_message(sender: Sender, message: str | dict | ToolResult):
    """Render a chat message or tool result."""
    is_tool_result = isinstance(message, ToolResult)
    if not message or (is_tool_result and st.session_state.hide_images and not hasattr(message, "error") and not hasattr(message, "output")):
        return
    with st.chat_message(sender):
        if is_tool_result:
            message = cast(ToolResult, message)
            if message.output:
                st.code(message.output) if message.__class__.__name__ == "CLIResult" else st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image and not st.session_state.hide_images:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict):
            block_type = message.get("type")
            if block_type == "text":
                st.write(message.get("text", ""))
            elif block_type == "tool_use":
                st.code(f'Tool Use: {message.get("name", "Unknown")}\nInput: {message.get("input", {})}')
            elif block_type == "thinking":
                st.markdown(f"[Thinking]\n\n{message.get('thinking', '')}")
            elif block_type == "redacted_thinking":
                st.markdown("[Redacted Thinking] - Encrypted for safety")
            elif block_type == "tool_result":
                st.write(f"Tool Result: {message.get('content', '')}")
            else:
                st.write(f"Unknown block type: {block_type}")
        else:
            st.markdown(message)

def _tool_output_callback(tool_result: ToolResult, tool_id: str, tool_state: dict):
    """Store tool output and render it."""
    tool_state[tool_id] = tool_result
    _render_message(Sender.TOOL, tool_result)

def _api_response_callback(request: httpx.Request | None, response: httpx.Response | dict | object | None, error: Exception | None, tab: DeltaGenerator, response_state: dict):
    """Log API response or error."""
    import uuid
    response_id = str(uuid.uuid4())
    response_state[response_id] = (request, response if not error else str(error))
    _render_api_response(request, response if not error else str(error), response_id, tab)

@contextmanager
def track_sampling_loop():
    """Context manager for tracking sampling loop execution."""
    try:
        yield
    except Exception as e:
        st.error(f"Error in sampling loop: {e}")

async def main():
    """Main Streamlit app entrypoint."""
    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)
    st.title("PALIOS-AI-OS Chat")
    
    # Display configuration information as simple text
    st.markdown("### Configuration")
    st.markdown(f"• Model: {st.session_state.model}")
    st.markdown(f"• Output tokens: {st.session_state.output_tokens}")
    st.markdown(f"• Thinking budget: {st.session_state.thinking_budget}")
    st.markdown(f"• Token-efficient tools: {'Enabled' if st.session_state.token_efficient_tools_beta else 'Disabled'}")
    st.markdown(f"• Tool version: {st.session_state.tool_version}")
    
    st.warning(WARNING_TEXT)

    # Always validate the API key
    if st.session_state.api_key != "your-api-key-here":
        st.session_state.auth_validated = True
    
    # If API key is hardcoded placeholder, show error
    if st.session_state.api_key == "your-api-key-here":
        st.error("Please edit streamlit.py to add your Anthropic API key in the hardcoded placeholder.")
        return
    
    # Create tabs for the application
    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input("Type a message to control the computer...")

    with chat:
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        _render_message(Sender.TOOL, st.session_state.tools.get(block["tool_use_id"]))
                    else:
                        _render_message(message["role"], cast(BetaContentBlockParam | ToolResult, block))

        if new_message:
            st.session_state.messages.append({"role": Sender.USER, "content": [BetaTextBlockParam(type="text", text=new_message)]})
            _render_message(Sender.USER, new_message)

            try:
                most_recent_message = st.session_state.messages[-1]
            except IndexError:
                return

            if most_recent_message["role"] != Sender.USER:
                return

            with track_sampling_loop():
                # Print API key length for debugging (without revealing the actual key)
                print(f"API Key length: {len(st.session_state.api_key)}")
                
                st.session_state.messages = await sampling_loop(
                    system_prompt_suffix="",
                    model=st.session_state.model,
                    provider=st.session_state.provider,
                    messages=st.session_state.messages,
                    output_callback=partial(_render_message, Sender.BOT),
                    tool_output_callback=partial(_tool_output_callback, tool_state=st.session_state.tools),
                    api_response_callback=partial(_api_response_callback, tab=http_logs, response_state=st.session_state.responses),
                    api_key=st.session_state.api_key,
                    only_n_most_recent_images=None,
                    tool_version=st.session_state.tool_version,
                    max_tokens=st.session_state.output_tokens,
                    thinking_budget=st.session_state.thinking_budget if st.session_state.thinking else None,
                    token_efficient_tools_beta=st.session_state.token_efficient_tools_beta,
                )

if __name__ == "__main__":
    asyncio.run(main())
