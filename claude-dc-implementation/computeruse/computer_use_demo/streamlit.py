"""
Ultra-simple Streamlit app for Anthropic API - Just the essentials
"""

import asyncio
import base64
from functools import partial
from typing import cast

import httpx
import streamlit as st
from anthropic.types.beta import BetaContentBlockParam, BetaTextBlockParam
from streamlit.delta_generator import DeltaGenerator

# Change from relative import to absolute import
from loop import APIProvider, sampling_loop
from tools import ToolResult, ToolVersion

# Initialize session state variables directly
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "model" not in st.session_state:
    st.session_state.model = "claude-3-7-sonnet-20250219"
if "provider" not in st.session_state:
    st.session_state.provider = APIProvider.ANTHROPIC
if "tool_version" not in st.session_state:
    st.session_state.tool_version = "computer_use_20250124"
if "output_tokens" not in st.session_state:
    st.session_state.output_tokens = 64000
if "thinking" not in st.session_state:
    st.session_state.thinking = True
if "thinking_budget" not in st.session_state:
    st.session_state.thinking_budget = 32000
if "token_efficient_tools_beta" not in st.session_state:
    st.session_state.token_efficient_tools_beta = True

# Simple callback functions
def render_message(sender, message):
    """Render a chat message or tool result."""
    with st.chat_message(sender):
        if isinstance(message, ToolResult):
            if message.output:
                st.code(message.output) if message.__class__.__name__ == "CLIResult" else st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict):
            block_type = message.get("type")
            if block_type == "text":
                st.write(message.get("text", ""))
            elif block_type == "tool_use":
                st.code(f'Tool Use: {message.get("name", "Unknown")}\nInput: {message.get("input", {})}')
            elif block_type == "thinking":
                st.markdown(f"[Thinking]\n\n{message.get('thinking', '')}")
            else:
                st.write(f"Block type: {block_type}")
        else:
            st.markdown(message)

def tool_output_callback(tool_result, tool_id, tool_state):
    """Store tool output and render it."""
    tool_state[tool_id] = tool_result
    render_message("tool", tool_result)

def api_response_callback(request, response, error, responses_state):
    """Simple callback for API responses."""
    responses_state["last_response"] = (request, response, error)
    if error:
        st.error(f"API Error: {error}")

async def main():
    """Ultra-simplified main Streamlit app."""
    st.title("PALIOS-AI-OS Chat")
    
    # Display configuration information
    st.markdown("### Configuration")
    st.markdown(f"* Model: {st.session_state.model}")
    st.markdown(f"* Output tokens: {st.session_state.output_tokens}")
    st.markdown(f"* Thinking budget: {st.session_state.thinking_budget}")
    st.markdown(f"* Token-efficient tools: Enabled")
    st.markdown(f"* Tool version: {st.session_state.tool_version}")
    
    # API Key input
    api_key = st.text_input("Enter Anthropic API Key", type="password")
    submit = st.button("Submit")
    
    if submit and api_key:
        # Store API key
        st.session_state.api_key = api_key
        st.success("API key saved! You can now start chatting.")
    
    # Only show chat if API key is provided
    if "api_key" in st.session_state and st.session_state.api_key:
        # Display past messages
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        render_message("tool", st.session_state.tools.get(block["tool_use_id"]))
                    else:
                        render_message(message["role"], cast(BetaContentBlockParam | ToolResult, block))
        
        # Chat input
        user_input = st.chat_input("Type a message to control the computer...")
        
        if user_input:
            # Display user message
            render_message("user", user_input)
            
            # Add to message history
            st.session_state.messages.append({
                "role": "user", 
                "content": [BetaTextBlockParam(type="text", text=user_input)]
            })
            
            try:
                # Call sampling loop with fixed parameters
                st.session_state.messages = await sampling_loop(
                    system_prompt_suffix="",
                    model=st.session_state.model,
                    provider=st.session_state.provider,
                    messages=st.session_state.messages,
                    output_callback=partial(render_message, "assistant"),
                    tool_output_callback=partial(tool_output_callback, tool_state=st.session_state.tools),
                    api_response_callback=partial(api_response_callback, responses_state=st.session_state.responses),
                    api_key=st.session_state.api_key,
                    only_n_most_recent_images=None,
                    tool_version=st.session_state.tool_version,
                    max_tokens=st.session_state.output_tokens,
                    thinking_budget=st.session_state.thinking_budget if st.session_state.thinking else None,
                    token_efficient_tools_beta=st.session_state.token_efficient_tools_beta,
                )
            except Exception as e:
                st.error(f"Error in chat: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
