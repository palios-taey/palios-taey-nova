"""
Entrypoint for streamlit, safe implementation compatible with GROK.
"""

import asyncio
import os
import json
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Union, cast

# Configure logging first
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("claude_dc.log")
    ]
)
logger = logging.getLogger("streamlit_ui")

import streamlit as st
import nest_asyncio
import httpx

# Apply nest_asyncio to run asyncio in Streamlit
nest_asyncio.apply()

# Import from our loop.py
from loop import agent_loop, AVAILABLE_TOOLS, APIProvider

# Check anthropic version
try:
    import anthropic
    from anthropic import AsyncAnthropic, RateLimitError
    
    anthropic_version = getattr(anthropic, "__version__", "unknown")
    logger.info(f"Using Anthropic SDK version: {anthropic_version}")
    
    if anthropic_version != "0.50.0":
        logger.warning(f"WARNING: Expected Anthropic SDK v0.50.0, but found v{anthropic_version}.")
        warning_message = f"""
        ⚠️ Version Mismatch: Expected Anthropic SDK v0.50.0, found v{anthropic_version} ⚠️
        
        This may cause compatibility issues. To fix:
        
        1. Run: `pip uninstall -y anthropic`
        2. Then: `pip install anthropic==0.50.0`
        """
        st.warning(warning_message)
        
except ImportError:
    # Log error but don't exit - we'll handle this in the UI
    logger.error("Failed to import AsyncAnthropic. Please install with: pip install anthropic==0.50.0")
    st.error("Anthropic SDK not installed. Please run: pip install anthropic==0.50.0")
    
    # Define a placeholder for RateLimitError
    class RateLimitError(Exception):
        """Placeholder for RateLimitError when anthropic is not installed."""
        pass

# Sender enum for chat messages
class Sender(str, Enum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "thinking" not in st.session_state:
    st.session_state.thinking = None

if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

if "responses" not in st.session_state:
    st.session_state.responses = {}

if "tools" not in st.session_state:
    st.session_state.tools = {}

if "provider" not in st.session_state:
    st.session_state.provider = APIProvider.ANTHROPIC

if "auth_validated" not in st.session_state:
    st.session_state.auth_validated = False
    
if "api_client" not in st.session_state:
    # Create client with beta flags in header
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        st.session_state.api_client = AsyncAnthropic(
            api_key=api_key,
            default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
        )
    else:
        logger.error("ANTHROPIC_API_KEY environment variable not set!")

async def main():
    """Main function for the Streamlit app."""
    st.title("Claude DC - GROK Streaming Implementation")
    st.caption("Custom Claude DC implementation with streaming and tool use")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Settings")
        
        # API key input
        api_key = st.text_input("Anthropic API Key", 
                              value=os.environ.get("ANTHROPIC_API_KEY", ""), 
                              type="password",
                              help="Enter your Anthropic API key")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            st.session_state.api_client = AsyncAnthropic(
                api_key=api_key,
                default_headers={"anthropic-beta": "tools-2024-05-16,output-128k-2025-02-19"}
            )
        
        # Model selection
        model = st.selectbox(
            "Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20240620"],
            index=0
        )
        
        # Max tokens
        max_tokens = st.slider("Max Tokens", min_value=1000, max_value=64000, value=4000, step=1000)
        
        # Temperature
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        
        # Thinking parameter
        thinking_enabled = st.checkbox("Enable Thinking", value=True)
        thinking_budget = st.slider("Thinking Budget (tokens)", min_value=256, max_value=8192, value=1024, step=256,
                                   disabled=not thinking_enabled)
        
        # Show thinking toggle
        show_thinking = st.checkbox("Show Thinking", value=False)
        
        st.divider()
        
        # Conversation management
        st.header("Conversation")
        
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.thinking = None
            st.rerun()
        
        # Save conversation
        if st.button("Save Conversation"):
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"conversation_{timestamp}.json"
            try:
                with open(filename, "w") as f:
                    json.dump(st.session_state.conversation_history, f, indent=2)
                st.success(f"Conversation saved to {filename}")
            except Exception as e:
                st.error(f"Error saving conversation: {e}")
        
    # Chat interface
    chat, http_logs = st.tabs(["Chat", "HTTP Exchange Logs"])
    
    with chat:
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Display thinking if enabled
        if show_thinking and st.session_state.thinking:
            with st.expander("Claude's Thinking Process", expanded=True):
                st.write(st.session_state.thinking)
        
        # Handle user input
        prompt = st.chat_input("Message Claude...")
        
        if prompt:
            # Add user message to UI and history
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.conversation_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Set up thinking parameter if enabled
            thinking = None
            if thinking_enabled:
                thinking = {"type": "enabled", "budget_tokens": thinking_budget}
            
            # Create placeholder for streaming response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Create container for tool use outputs
                tool_container = st.container()
                
                # Start streaming with placeholder
                current_response_text = ""
                
                # Set streaming active flag
                st.session_state.streaming_active = True
                
                # Define stream handler function
                async def stream_handler(event):
                    # Use the properly scoped variable
                    nonlocal current_response_text
                    
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        current_response_text += event.delta.text
                        message_placeholder.markdown(current_response_text)
                    
                    elif event.type == "content_block_stop" and event.content_block.type == "tool_use":
                        # Display tool use in the UI
                        with tool_container:
                            if hasattr(event.content_block.tool_use, "get"):
                                tool_info = event.content_block.tool_use.get('type', 
                                    event.content_block.tool_use.get('name', 'unknown'))
                            else:
                                tool_info = "unknown tool"
                            st.info(f"Using tool: {tool_info}")
                            st.json(event.content_block.tool_use)
                    
                    elif event.type == "message_delta" and event.delta.thinking:
                        # Store thinking content
                        st.session_state.thinking = event.delta.thinking
                        # Update thinking display if enabled
                        if show_thinking:
                            with st.sidebar:
                                with st.expander("Claude's Thinking Process", expanded=True):
                                    st.write(event.delta.thinking)
                
                # Run agent loop in async function
                async def run_agent():
                    try:
                        response = await agent_loop(
                            client=st.session_state.api_client,
                            messages=st.session_state.conversation_history,
                            model=model,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            thinking=thinking,
                            stream_handler=stream_handler,
                            tools=AVAILABLE_TOOLS,
                            save_conversation=True
                        )
                        
                        # Extract text content from response
                        text_content = ""
                        for block in response["content"]:
                            if block["type"] == "text" and block["text"]:
                                text_content += block["text"]
                        
                        # Add assistant response to history
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "content": text_content
                        })
                        
                        # Add to UI message history
                        st.session_state.messages.append({"role": "assistant", "content": text_content})
                        
                        # Set streaming flag to False
                        st.session_state.streaming_active = False
                        
                        # Record API response in debug log
                        response_id = datetime.now().isoformat()
                        st.session_state.responses[response_id] = (None, response)
                        
                        # Render response on HTTP logs tab
                        _render_api_response(None, response, response_id, http_logs)
                        
                    except Exception as e:
                        logger.error(f"Error in agent loop: {e}")
                        message_placeholder.error(f"Error: {str(e)}")
                        st.session_state.streaming_active = False
                        
                        # Record error in debug log
                        response_id = datetime.now().isoformat()
                        st.session_state.responses[response_id] = (None, str(e))
                        
                        # Render error on HTTP logs tab
                        _render_error(e)
                
                # Run in asyncio
                asyncio.run(run_agent())

    # Add footer
    st.divider()
    try:
        import anthropic
        st.caption(f"Claude DC GROK Implementation | Anthropic SDK v{anthropic.__version__} | Streamlit v{st.__version__}")
    except:
        st.caption("Claude DC GROK Implementation")

def _render_api_response(
    request: Optional[httpx.Request],
    response: Union[httpx.Response, object, None],
    response_id: str,
    tab: st.delta_generator.DeltaGenerator
):
    """Safely render an API response to a streamlit tab"""
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            
            # Safely handle request which might be None
            if request:
                try:
                    st.markdown(
                        f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
                    )
                    st.json(request.read().decode())
                except Exception as e:
                    st.error(f"Error rendering request: {str(e)}")
            else:
                st.info("No request information available")
            
            st.markdown("---")
            
            # Safely handle response
            if isinstance(response, httpx.Response):
                try:
                    st.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    st.json(response.text)
                except Exception as e:
                    st.error(f"Error rendering response: {str(e)}")
            else:
                st.write(response)

def _render_error(error: Exception):
    """Safely render an error"""
    if isinstance(error, RateLimitError):
        body = "You have been rate limited."
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            retry_after = error.response.headers.get("retry-after")
            if retry_after:
                body += f" **Retry after {str(timedelta(seconds=int(retry_after)))} (HH:MM:SS).** See API documentation for more details."
        if hasattr(error, 'message'):
            body += f"\n\n{error.message}"
    else:
        body = str(error)
        body += "\n\n**Traceback:**"
        lines = "\n".join(traceback.format_exception(error))
        body += f"\n\n```{lines}```"
    
    st.error(f"**{error.__class__.__name__}**\n\n{body}")

if __name__ == "__main__":
    asyncio.run(main())