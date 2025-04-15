"""
Streamlit interface for Claude Computer Use with enhanced protection
"""
import os
import sys
import json
import base64
import asyncio
import streamlit as st
from enum import Enum, auto
from typing import List, Dict, Any, Optional

# Configure paths
sys.path.append('/home/computeruse/computer_use_demo')

# Import modules (in correct order)
# Import tool intercept FIRST to ensure it's active for all operations
try:
    from tool_intercept import tool_intercept
    has_tool_intercept = True
except ImportError:
    has_tool_intercept = False

# Import other modules
from safe_ops import safe_cat, safe_ls, safe_file_info
from token_management.token_manager import token_manager
from streaming.streaming_client import StreamingClient

# Import exceptions for error handling
from anthropic import RateLimitError, APIStatusError

# Import loop module
from loop import sampling_loop

# After all imports, initialize streaming client
streaming_client = StreamingClient(token_manager=token_manager)

# Configuration
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
MAX_TOKENS = 128000
THINKING_BUDGET = 32000
DEFAULT_PROVIDER = "anthropic"
TOOL_VERSION = "20250124"
TOKEN_EFFICIENT_TOOLS = True

# Sender enum for chat UI
class Sender(str, Enum):
    HUMAN = "human"
    BOT = "ai"

class ContentBlockType(str, Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    IMAGE = "image"

# Page configuration
st.set_page_config(
    page_title="Claude Computer Use",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "token_usage" not in st.session_state:
    st.session_state.token_usage = {"input": 0, "output": 0}

if "system_prompt_suffix" not in st.session_state:
    st.session_state.system_prompt_suffix = ""

# UI components
st.title("Claude Computer Use")

# Sidebar for configuration and stats
with st.sidebar:
    st.header("Settings")
    
    # Model selection
    model_options = ["claude-3-7-sonnet-20250219", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    selected_model = st.selectbox("Model", model_options, index=0)
    
    # Provider selection
    provider_options = ["anthropic", "vertex", "bedrock"]
    selected_provider = st.selectbox("Provider", provider_options, index=0)
    
    # Advanced settings expandable section
    with st.expander("Advanced Settings"):
        selected_max_tokens = st.slider("Max Tokens", 1000, MAX_TOKENS, MAX_TOKENS, 1000)
        selected_thinking_budget = st.slider("Thinking Budget", 0, THINKING_BUDGET, THINKING_BUDGET, 1000)
        token_efficient = st.checkbox("Token Efficient Tools", value=TOKEN_EFFICIENT_TOOLS)
    
    # Token management stats
    st.header("Token Usage")
    token_stats = token_manager.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Input Tokens", f"{st.session_state.token_usage.get('input', 0):,}")
    with col2:
        st.metric("Output Tokens", f"{st.session_state.token_usage.get('output', 0):,}")
    
    # Rate limit status
    st.header("Rate Limit Status")
    input_percent = token_stats.get("input_percent", 0)
    output_percent = token_stats.get("output_percent", 0)
    
    st.progress(min(input_percent / 100, 1.0), text=f"Input: {input_percent:.1f}%")
    st.progress(min(output_percent / 100, 1.0), text=f"Output: {output_percent:.1f}%")
    
    # System information
    st.header("System Info")
    st.write(f"Tool interception: {'Active' if has_tool_intercept else 'Inactive'}")
    st.write(f"Streaming: {'Enabled' if streaming_client else 'Disabled'}")
    st.write(f"Protection: {'Active' if 'token_manager' in sys.modules else 'Inactive'}")

# Display chat history
for i, message in enumerate(st.session_state.messages):
    role = message.get("role", "user")
    sender = Sender.HUMAN if role == "user" else Sender.BOT
    
    with st.chat_message(sender):
        if isinstance(message.get("content"), list):
            # Handle content blocks
            for block in message.get("content", []):
                block_type = block.get("type", "")
                
                if block_type == ContentBlockType.TEXT:
                    st.write(block.get("text", ""))
                
                elif block_type == ContentBlockType.IMAGE:
                    source = block.get("source", {})
                    if source.get("type") == "base64" and source.get("data"):
                        st.image(f"data:image/png;base64,{source['data']}")
                
                elif block_type == ContentBlockType.TOOL_USE:
                    tool_name = block.get("name", "unknown")
                    st.info(f"Using tool: {tool_name}")
                
                elif block_type == ContentBlockType.TOOL_RESULT:
                    tool_content = block.get("content", [])
                    is_error = block.get("is_error", False)
                    
                    if isinstance(tool_content, list):
                        for item in tool_content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                if is_error:
                                    st.error(item.get("text", ""))
                                else:
                                    st.code(item.get("text", ""))
                            elif isinstance(item, dict) and item.get("type") == "image":
                                source = item.get("source", {})
                                if source.get("type") == "base64" and source.get("data"):
                                    st.image(f"data:image/png;base64,{source['data']}")
                    else:
                        if is_error:
                            st.error(tool_content)
                        else:
                            st.code(tool_content)
                
                elif block_type == ContentBlockType.THINKING:
                    thinking_text = block.get("thinking", "")
                    if thinking_text:
                        with st.expander("Thinking Process"):
                            st.write(thinking_text)
        else:
            # Simple text content
            st.write(message.get("content", ""))

# Chat input
prompt = st.chat_input("Message Claude...")

# Process user input
if prompt:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
    with st.chat_message(Sender.HUMAN):
        st.write(prompt)
    
    # Process with Claude
    with st.spinner("Claude is thinking..."):
        assistant_response_container = st.container()
        
        # Define callback functions
        def output_callback(content_block):
            """Handle output from Claude"""
            with assistant_response_container:
                with st.chat_message(Sender.BOT):
                    if content_block.get("type") == ContentBlockType.TEXT:
                        st.write(content_block.get("text", ""))
                    elif content_block.get("type") == ContentBlockType.THINKING:
                        with st.expander("Thinking Process"):
                            st.write(content_block.get("thinking", ""))
        
        def tool_output_callback(result, tool_use_id):
            """Handle tool output"""
            with assistant_response_container:
                with st.chat_message(Sender.BOT):
                    if result.error:
                        st.error(result.error)
                    else:
                        if result.output:
                            st.code(result.output)
                        if result.base64_image:
                            st.image(f"data:image/png;base64,{result.base64_image}")
        
        def api_response_callback(request, response, error):
            """Handle API response"""
            if error:
                st.error(f"API Error: {error}")
                return
            
            # Update token usage if response headers exist
            if response and hasattr(response, 'headers'):
                headers = response.headers
                input_tokens = int(headers.get("anthropic-input-tokens", 0))
                output_tokens = int(headers.get("anthropic-output-tokens", 0))
                
                st.session_state.token_usage["input"] = st.session_state.token_usage.get("input", 0) + input_tokens
                st.session_state.token_usage["output"] = st.session_state.token_usage.get("output", 0) + output_tokens
                
                # Update token manager
                token_manager.process_response_headers(dict(headers))
        
        try:
            # Process the message
            updated_messages = await sampling_loop(
                model=selected_model,
                provider=selected_provider,
                system_prompt_suffix=st.session_state.system_prompt_suffix,
                messages=st.session_state.messages,
                output_callback=output_callback,
                tool_output_callback=tool_output_callback,
                api_response_callback=api_response_callback,
                api_key=API_KEY,
                max_tokens=selected_max_tokens,
                thinking_budget=selected_thinking_budget,
                tool_version=TOOL_VERSION,
                token_efficient_tools_beta=token_efficient,
            )
            
            # Update messages with Claude's response
            st.session_state.messages = updated_messages
            
        except RateLimitError as e:
            st.error(f"Rate limit exceeded: {str(e)}")
            retry_after = getattr(e, "retry_after", None)
            if retry_after:
                st.info(f"Please wait {retry_after} seconds before trying again.")
        
        except APIStatusError as e:
            st.error(f"API error: {str(e)}")
        
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")

# Main function for Streamlit
async def main():
    # Any async initialization
    pass

if __name__ == "__main__":
    asyncio.run(main())
