import sys; sys.path.insert(0, "/home/computeruse")
import os
import math
import streamlit as st
from computer_use_demo.loop import APIProvider, sampling_loop, ToolResult
from computer_use_demo.types import Sender
from anthropic.types.beta import BetaTextBlockParam, BetaToolResultBlockParam, BetaContentBlockParam, BetaToolUseBlockParam, BetaImageBlockParam
from token_manager import token_manager
import httpx
from streamlit.delta_generator import DeltaGenerator # Import the DeltaGenerator class

st.title("Claude DC – Streaming Chat Interface")
st.markdown("Enter a prompt for Claude and receive a streamed response. Token usage is tracked to avoid exceeding rate limits.")

# Ensure Anthropic API key is set
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    st.stop()
if "api_key" not in st.session_state:
    st.session_state.api_key = api_key

# Initialize session state for various settings
if "output_tokens" not in st.session_state:
    st.session_state.output_tokens = token_manager.get_safe_limits()["max_tokens"]
if "thinking" not in st.session_state:
    st.session_state.thinking = False
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = token_manager.safe_thinking_budget
if "only_n_most_recent_images" not in st.session_state:
    st.session_state.only_n_most_recent_images = 0
if "token_efficient_tools_beta" not in st.session_state:
    st.session_state.token_efficient_tools_beta = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "model" not in st.session_state:
    st.session_state.model = "claude-3-opus-20240229" # Default model
if "provider" not in st.session_state:
    st.session_state.provider = "anthropic" # Default provider
if "tool_version" not in st.session_state:
    st.session_state.tool_version = None # Default tool version


def _render_message(sender: Sender, content: str | list[BetaContentBlockParam]):
    """Render a single message to the chat window."""
    with st.chat_message(sender.value):
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, BetaTextBlockParam):
                    st.markdown(block.text)
                elif isinstance(block, BetaToolUseBlockParam):
                    st.markdown(f"Tool Use: `{block.name}` with ID `{block.id}`")
                    st.json(block.input)
                elif isinstance(block, BetaImageBlockParam):
                    st.image(base64.b64decode(block.base64), caption=block.alt_text)
                elif isinstance(block, dict) and block.get("type") == "tool_result":
                    st.markdown(f"Tool Result ID: `{block.get('tool_use_id', 'unknown')}`")
                    st.json(block.get("content", {}))
                elif isinstance(block, dict) and block.get("type") == "redacted_thinking":
                    st.markdown("(redacted thinking)")
                else:
                    st.write(block)
        else:
            st.write(content)

def _tool_output_callback(tool_result: ToolResult, tool_id: str):
    _render_message(Sender.TOOL, tool_result)

def _api_response_callback(request: httpx.Request | None, response: httpx.Response | dict | object | None, tab: DeltaGenerator, response_state: dict):
    """Log API response."""
    identity = str(math.floor(len(response_state)/2))
    response_state[identity] = (request, response)
    with tab:
        with st.expander(f"Request/Response ({identity})"):
            if request:
                newline = "\n\n"
                st.markdown(
                    f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
                )
                try:
                    st.json(request.read().decode())
                except Exception as e:
                    st.text(f"Could not display request content: {str(e)}")
            else:
                st.markdown("*No request data available*")
            st.markdown("---")
            if isinstance(response, httpx.Response):
                try:
                    st.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    if not getattr(response, '_stream', False):
                        response_text = response.text
                        st.text(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)
                    else:
                        st.text("Streaming response (content not available)")
                except Exception as e:
                    st.text(f"Could not display response content: {str(e)}")
            elif isinstance(response, dict):
                st.markdown(f"`{response.get('status_code', 'N/A')}`")
                headers = response.get('headers', {})
                if headers:
                    st.markdown(f"{newline.join(f'`{k}: {v}`' for k, v in headers.items())}")
                st.text("Response content processed")
            elif response is None:
                st.text("No response data available")
            else:
                st.write(f"Response type: {type(response)}")
                st.write(response)

def _render_messages():
    for message in st.session_state.messages:
        _render_message(message["role"], message["content"])

def setup_state():
    if "auth_validated" not in st.session_state:
        st.session_state.auth_validated = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "provider" not in st.session_state:
        st.session_state.provider = "anthropic"

def validate_auth(provider: str, api_key: str) -> str | None:
    if not api_key:
        return "Please enter your API key."
    return None

def track_sampling_loop():
    return st.empty()

async def main():
    setup_state()
    st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)
    st.title("PALIOS-AI-OS Chat")
    st.warning(WARNING_TEXT)

    if not st.session_state.auth_validated:
        st.session_state.api_key = st.text_input("Enter Anthropic API Key", type="password")
        if auth_error := validate_auth(st.session_state.provider, st.session_state.api_key):
            st.warning(f"Please resolve: {auth_error}")
            return
        st.session_state.auth_validated = True

    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input("Type a message to control the computer...")

    with chat:
        # Display existing messages
        for message in st.session_state.messages:
            _render_message(message["role"], message["content"])

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
            try:
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
                    tool_version=None,
                    max_tokens=st.session_state.output_tokens,
                    thinking_budget=(st.session_state.thinking_budget if st.session_state.thinking else None),
                    token_efficient_tools_beta=st.session_state.token_efficient_tools_beta,
                    stream=True,
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
