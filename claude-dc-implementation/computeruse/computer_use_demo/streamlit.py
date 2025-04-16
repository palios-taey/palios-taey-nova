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

