# streamlit.py
import sys
sys.path.insert(0, "/home/computeruse")  # Ensure the package root is on path
import os
import json
import math
import asyncio
import base64
import streamlit as st
from functools import partial
from streamlit.delta_generator import DeltaGenerator
from anthropic.types.beta import BetaTextBlockParam, BetaToolUseBlockParam, BetaImageBlockParam
from computer_use_demo.loop import APIProvider, sampling_loop
from computer_use_demo.types import Sender, ToolResult
from computer_use_demo.token_manager import token_manager

# Inject custom style for Streamlit UI
STREAMLIT_STYLE = """
<style>
    button[kind=header] {
        background-color: rgb(255, 75, 75);
        border: 1px solid rgb(255, 75, 75);
        color: white;
    }
    button[kind=header]:hover {
        background-color: rgb(255, 51, 51);
    }
    .stAppDeployButton {
        visibility: hidden;
    }
</style>
"""
WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data."

# Initialize or retrieve session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "thinking" not in st.session_state:
    st.session_state.thinking = False
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = token_manager.safe_thinking_budget
if "only_n_most_recent_images" not in st.session_state:
    st.session_state.only_n_most_recent_images = 0  # 0 means keep all images
if "model" not in st.session_state:
    st.session_state.model = "claude-3-7-sonnet-20250219"
if "provider" not in st.session_state:
    st.session_state.provider = APIProvider.ANTHROPIC

# Load Anthropic API key from env or secrets file
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    try:
        with open("/home/computeruse/secrets/palios-taey-secrets.json") as f:
            secrets = json.load(f)
            api_key = secrets.get("api_keys", {}).get("anthropic", "")
    except Exception:
        api_key = ""
if not api_key:
    st.error("Anthropic API key not found. Set ANTHROPIC_API_KEY or configure secrets file.")
    st.stop()
st.session_state.api_key = api_key

# Apply custom styles and render UI header
st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)
st.title("PALIOS-AI-OS Chat")
st.warning(WARNING_TEXT)

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    st.session_state.output_tokens = st.slider(
        "Max Output Tokens", min_value=256, max_value=32768,
        value=token_manager.get_safe_limits()["max_tokens"], step=256
    )
    st.session_state.thinking = st.checkbox("Enable Chain-of-Thought (thinking)", value=st.session_state.thinking)
    st.session_state.thinking_budget = st.slider(
        "Thinking Token Budget", min_value=0, max_value=10000,
        value=st.session_state.thinking_budget, step=100
    )
    images_keep = st.number_input(
        "Images to keep in history", min_value=0, max_value=10,
        value=int(st.session_state.only_n_most_recent_images)
    )
    st.session_state.only_n_most_recent_images = None if images_keep == 0 else images_keep

def _render_message(sender: Sender, content):
    """Render a single message (user, assistant, or tool output) in the chat."""
    with st.chat_message(sender.value):
        if isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, ToolResult):
            # Show tool outputs or errors in a readable format
            if content.output:
                st.code(content.output)
            if content.error:
                st.markdown(f"**Tool Error:** {content.error}")
            if content.base64_image:
                try:
                    st.image(base64.b64decode(content.base64_image))
                except Exception:
                    st.write("*(Unable to display image)*")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, BetaTextBlockParam):
                    st.markdown(block.text)
                elif isinstance(block, BetaToolUseBlockParam):
                    st.markdown(f"**Tool Use:** `{block.name}` (ID {block.id})")
                    st.json(block.input)
                elif isinstance(block, BetaImageBlockParam):
                    # Display image content
                    st.image(base64.b64decode(block.base64), caption=(block.alt_text or "image"))
                elif isinstance(block, dict):
                    btype = block.get("type")
                    if btype == "text":
                        st.markdown(block.get("data", ""))
                    elif btype == "tool_use":
                        st.markdown(f"**Tool Use:** `{block.get('name')}` (ID {block.get('id')})")
                        st.json(block.get("input", {}))
                    elif btype == "tool_result":
                        st.markdown(f"**Tool Result (ID {block.get('tool_use_id', 'N/A')})**:")
                        result_content = block.get("content", "")
                        if isinstance(result_content, str):
                            # Display large text outputs in a scrollable code block
                            snippet = result_content[:10000] + ("..." if len(result_content) > 10000 else "")
                            st.code(snippet)
                        else:
                            st.write(result_content)
                    elif btype == "redacted_thinking":
                        st.markdown("*(redacted thinking)*")
                    else:
                        st.write(block)
        else:
            # Fallback for any content not caught above
            st.write(content)

def _tool_output_callback(tool_result: ToolResult, tool_id: str):
    # Render tool execution result as a message from the "tool"
    _render_message(Sender.TOOL, tool_result)

def _api_response_callback(request, response, error: Exception | None = None, *, tab: DeltaGenerator, response_state: dict):
    # Log the HTTP request/response in the separate tab for debugging
    idx = str(len(response_state))
    response_state[idx] = (request, response, error)
    with tab:
        with st.expander(f"Request/Response {idx}"):
            # Show request details
            if request is not None and hasattr(request, "method"):
                st.markdown(f"`{getattr(request, 'method', '')} {getattr(request, 'url', '')}`")
                for k, v in getattr(request, "headers", {}).items():
                    st.markdown(f"`{k}: {v}`")
            else:
                st.markdown("*No request data*")
            st.markdown("---")
            # Show response or error details
            if response is not None and hasattr(response, "status_code"):
                st.markdown(f"**Status Code:** {getattr(response, 'status_code', '')}")
                try:
                    for k, v in getattr(response, "headers", {}).items():
                        st.markdown(f"`{k}: {v}`")
                    if not getattr(response, "_stream", False):
                        text = response.text
                        snippet = text[:1000] + ("..." if len(text) > 1000 else "")
                        st.text(snippet)
                    else:
                        st.text("(streaming response)")
                except Exception as e:
                    st.write(f"Could not parse response content: {e}")
            elif isinstance(response, dict):
                st.markdown(f"**Status Code:** {response.get('status_code', 'N/A')}")
                for k, v in response.get("headers", {}).items():
                    st.markdown(f"`{k}: {v}`")
                st.text("(streamed response)")
            if error:
                st.error(f"Error: {error}")

async def main():
    chat_tab, http_logs_tab = st.tabs(["Chat", "HTTP Exchange Logs"])
    new_message = st.chat_input("Type a message to control the computer...")
    # Display chat history and any new user message
    with chat_tab:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                _render_message(msg["role"], msg["content"])
        if new_message:
            # Append and display the new user message
            st.session_state.messages.append({"role": Sender.USER, "content": [{"type": "text", "data": new_message}]})
            _render_message(Sender.USER, new_message)
    # If a new user message was added, invoke the Claude API for a response
    if new_message and st.session_state.messages[-1]["role"] == Sender.USER:
        try:
            st.session_state.messages = await sampling_loop(
                model=st.session_state.model,
                provider=st.session_state.provider,
                system_prompt_suffix="",
                messages=st.session_state.messages,
                output_callback=partial(_render_message, Sender.BOT),
                tool_output_callback=_tool_output_callback,
                api_response_callback=partial(_api_response_callback, tab=http_logs_tab, response_state=st.session_state.responses),
                api_key=st.session_state.api_key,
                only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                max_tokens=st.session_state.output_tokens,
                thinking_budget=(st.session_state.thinking_budget if st.session_state.thinking else None),
                token_efficient_tools_beta=False,
                stream=True
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

