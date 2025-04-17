import sys; sys.path.insert(0, "/home/computeruse")
import os
import math
import streamlit as st
from computer_use_demo.loop import APIProvider, sampling_loop, ToolResult
from computer_use_demo.types import Sender
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

# Clamp output and thinking token values within allowed ranges
model_max_tokens = 128000 if token_manager.extended_output_beta else 8192
if st.session_state.output_tokens < 1:
    st.session_state.output_tokens = 1
if st.session_state.output_tokens > model_max_tokens:
    st.session_state.output_tokens = model_max_tokens
if st.session_state.thinking_budget < 1:
    st.session_state.thinking_budget = 1
if st.session_state.thinking_budget > model_max_tokens:
    st.session_state.thinking_budget = model_max_tokens

# User-adjustable token settings
with st.sidebar:
    st.number_input("Max Output Tokens", min_value=1, max_value=model_max_tokens, step=1, key="output_tokens")
    st.checkbox("Thinking Enabled", key="thinking")
    st.number_input("Thinking Budget", min_value=1, max_value=model_max_tokens, step=1, key="thinking_budget", disabled=not st.session_state.thinking)

# Helper for rendering messages
def _render_message(role, content):
    """Render a message block in the Streamlit app."""
    role_name = role.name.lower() if hasattr(role, "name") else str(role)
    if isinstance(content, str):
        st.markdown(content)
    elif isinstance(content, BetaTextBlockParam):
        st.markdown(content.text)
    elif isinstance(content, BetaToolUseBlockParam):
        st.markdown(f"Tool Use: `{content.name}` with ID `{content.id}`")
        st.json(content.input)
    elif isinstance(content, BetaImageBlockParam):
        st.image(base64.b64decode(content.base64), caption=content.alt_text)
    elif isinstance(content, dict) and content.get("type") == "tool_result":
        st.markdown(f"Tool Result ID: `{content.get('tool_use_id', 'unknown')}`")
        st.json(content.get("content", {}))
    elif isinstance(content, dict) and content.get("type") == "redacted_thinking":
        st.markdown("(redacted thinking)")
    else:
        st.write(content)

def _render_messages():
    """Render all conversation messages in the Streamlit app."""
    for message in st.session_state.messages:
        _render_message(message["role"], message["content"])

# Initialize conversation state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "in_sampling_loop" not in st.session_state:
    st.session_state.in_sampling_loop = False

# Accept user input and trigger Claude's response
user_input = st.text_input("Your Prompt:", "")
if user_input:
    # Append user message to conversation history
    st.session_state.messages.append({"role": Sender.USER, "content": user_input})
    _render_message(Sender.USER, user_input)
    # Run the sampling loop to get Claude's response (with streaming output)
    try:
        with st.spinner("Claude is responding..."):
            # Execute Claude's agent loop asynchronously and stream result
            st.session_state.messages = sampling_loop(
                model="claude",  # Using default model (Anthropic Claude)
                provider=APIProvider.ANTHROPIC,
                system_prompt_suffix="",  # No extra system prompt suffix
                messages=st.session_state.messages,
                output_callback=lambda text: st.write(text, end=""),
                tool_output_callback=lambda result, tool_id: st.session_state.tools.update({tool_id: result}) or _render_message(Sender.TOOL, result),
                api_response_callback=lambda req, resp, err: st.session_state.responses.update({math.floor(len(st.session_state.responses)/2): (req, resp)}),
                api_key=st.session_state.api_key,
                only_n_most_recent_images=st.session_state.only_n_most_recent_images,
                max_tokens=st.session_state.output_tokens,
                tool_version=None,  # default tool version
                thinking_budget=(st.session_state.thinking_budget if st.session_state.thinking else None),
                token_efficient_tools_beta=st.session_state.token_efficient_tools_beta,
            )
    except Exception as e:
        st.error(f"An error occurred: {e}")
    # Render all messages including the new assistant response
    _render_messages()

