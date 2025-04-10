"""
Minimal Streamlit app for Anthropic API
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
WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data."

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

# Configure Session State (Very Simple)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tools" not in st.session_state:
    st.session_state.tools = {}
if "api_key" not in st.session_state:
    # REPLACE WITH YOUR API KEY
    st.session_state.api_key = "YOUR_API_KEY_HERE"

def _render_message(sender: Sender, message: str | dict | ToolResult):
    """Render a chat message or tool result."""
    is_tool_result = isinstance(message, ToolResult)
    if not message:
        return
    with st.chat_message(sender):
        if is_tool_result:
            message = cast(ToolResult, message)
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

def _api_response_callback(request: httpx.Request | None, response: httpx.Response | dict | object | None, error: Exception | None, responses_state: dict):
    """Simple callback for API responses."""
    responses_state["last_response"] = (request, response, error)

async def main():
    """Very simplified main Streamlit app."""
    st.title("PALIOS-AI-OS Chat")
    st.warning(WARNING_TEXT)
    
    # Display fixed configuration
    st.markdown("### PALIOS-AI-OS Configuration")
    st.markdown("* Model: claude-3-7-sonnet-20250219")
    st.markdown("* Output tokens: 64000")
    st.markdown("* Thinking budget: 32000")
    st.markdown("* Token-efficient tools: Enabled")
    st.markdown("* Tool version: computer_use_20250124")
    
    # Only check for API key validity (no input UI)
    if st.session_state.api_key == "YOUR_API_KEY_HERE":
        st.error("Please update the streamlit.py file with your Anthropic API key")
        return
    
    # Simple Chat UI
    chat_tab, http_tab = st.tabs(["Chat", "HTTP Logs"])
    new_message = st.chat_input("Type a message to control the computer...")
    
    with chat_tab:
        # Display existing messages
        for message in st.session_state.messages:
            if isinstance(message["content"], str):
                _render_message(message["role"], message["content"])
            elif isinstance(message["content"], list):
                for block in message["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        _render_message(Sender.TOOL, st.session_state.tools.get(block["tool_use_id"]))
                    else:
                        _render_message(message["role"], cast(BetaContentBlockParam | ToolResult, block))
        
        # Handle new message from user
        if new_message:
            # Display the message
            _render_message(Sender.USER, new_message)
            
            # Add message to state
            st.session_state.messages.append({
                "role": "user", 
                "content": [BetaTextBlockParam(type="text", text=new_message)]
            })
            
            # Create a simple dict to store responses
            responses = {}
            
            try:
                # Call sampling loop with fixed parameters
                st.session_state.messages = await sampling_loop(
                    system_prompt_suffix="",
                    model="claude-3-7-sonnet-20250219",
                    provider=APIProvider.ANTHROPIC,
                    messages=st.session_state.messages,
                    output_callback=partial(_render_message, Sender.BOT),
                    tool_output_callback=partial(_tool_output_callback, tool_state=st.session_state.tools),
                    api_response_callback=partial(_api_response_callback, responses_state=responses),
                    api_key=st.session_state.api_key,
                    only_n_most_recent_images=None,
                    tool_version="computer_use_20250124",
                    max_tokens=64000,
                    thinking_budget=32000,
                    token_efficient_tools_beta=True,
                )
            except Exception as e:
                st.error(f"Error in chat: {str(e)}")
    
    # Display HTTP logs in the other tab
    with http_tab:
        if "last_response" in responses:
            req, resp, err = responses["last_response"]
            if err:
                st.error(f"Error: {str(err)}")
            if req:
                st.code(f"Request: {req.method} {req.url}")
            if resp:
                st.code(f"Response: {resp}")

if __name__ == "__main__":
    asyncio.run(main())
