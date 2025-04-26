"""
NOTE: This file was renamed from streamlit.py to claude_ui.py to avoid conflicts with the streamlit package.

Streamlit UI for Claude DC with streaming support.

This module provides a clean, modern UI for interacting with Claude DC,
featuring real-time streaming of responses, tool execution progress,
and thinking visualization.
"""

import os
import sys
import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
import traceback

# Configure logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "streamlit_debug.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("streamlit_ui")
logger.info("Claude UI module loaded")

# Set up exception hook to log all uncaught exceptions
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # Call the default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = log_uncaught_exceptions

# Import Streamlit
try:
    logger.debug("Attempting to import streamlit")
    import streamlit as st
    logger.debug("Basic streamlit import successful")
    
    # Try importing specific components - these can sometimes fail even when basic import works
    try:
        from streamlit.delta_generator import DeltaGenerator
        logger.debug("Imported DeltaGenerator successfully")
    except ImportError as e:
        logger.warning(f"Could not import DeltaGenerator: {e}")
        # Create a placeholder if needed
        class DeltaGenerator:
            pass
        
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx
        logger.debug("Imported add_script_run_ctx successfully")
    except ImportError as e:
        logger.warning(f"Could not import add_script_run_ctx: {e}")
        # Create a placeholder if needed
        def add_script_run_ctx(func):
            return func
    
    logger.info("All streamlit imports completed")
    HAS_STREAMLIT = True
except ImportError as e:
    logger.error(f"Streamlit not installed. Error: {e}")
    logger.error("Install with: pip install streamlit")
    HAS_STREAMLIT = False

# Import the agent loop
try:
    from loop import agent_loop, StreamingSession
except ImportError:
    logger.error("Could not import agent_loop from loop.py")
    # Create placeholder
    async def agent_loop(*args, **kwargs):
        return []
    
    class StreamingSession:
        pass

# Set page configuration if Streamlit is available
if HAS_STREAMLIT:
    st.set_page_config(
        page_title="Claude DC - Computer Use",
        page_icon=":brain:",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Main UI class
class ClaudeUI:
    """
    Streamlit UI for Claude DC with streaming support.
    
    This class provides a clean, modern UI for interacting with Claude DC,
    featuring real-time streaming of responses, tool execution progress,
    and thinking visualization.
    """
    
    def __init__(self):
        """Initialize the UI."""
        if not HAS_STREAMLIT:
            logger.error("Streamlit not available. UI cannot be initialized.")
            return
        
        # Initialize session state
        if "conversation" not in st.session_state:
            st.session_state.conversation = []
        
        if "streaming" not in st.session_state:
            st.session_state.streaming = {
                "active": False,
                "container": None,
                "text": "",
                "tool_active": False,
                "tool_name": "",
                "tool_input": {},
                "tool_output": "",
                "tool_progress": 0.0,
                "thinking": ""
            }
        
        if "api_key" not in st.session_state:
            st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        
        if "model" not in st.session_state:
            st.session_state.model = "claude-3-7-sonnet-20250219"
        
        if "max_tokens" not in st.session_state:
            st.session_state.max_tokens = 16000
        
        if "thinking_budget" not in st.session_state:
            st.session_state.thinking_budget = 4000
        
        if "show_thinking" not in st.session_state:
            st.session_state.show_thinking = False
        
        # Set up the UI layout
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        # Title
        st.title("Claude DC - Computer Use")
        
        # Sidebar for settings
        with st.sidebar:
            st.header("Settings")
            
            # API key
            st.session_state.api_key = st.text_input(
                "Anthropic API Key",
                value=st.session_state.api_key,
                type="password",
                key="api_key_input"
            )
            
            # Model selection
            st.session_state.model = st.selectbox(
                "Model",
                ["claude-3-7-opus-20240229", "claude-3-7-haiku-20240307", "claude-3-7-sonnet-20250219"],
                index=2,
                key="model_input"
            )
            
            # Max tokens
            st.session_state.max_tokens = st.slider(
                "Max Tokens",
                min_value=1000,
                max_value=128000,
                value=st.session_state.max_tokens,
                step=1000,
                key="max_tokens_input"
            )
            
            # Thinking budget
            st.session_state.thinking_budget = st.slider(
                "Thinking Budget",
                min_value=0,
                max_value=32000,
                value=st.session_state.thinking_budget,
                step=1000,
                key="thinking_budget_input"
            )
            
            # Show thinking toggle
            st.session_state.show_thinking = st.checkbox(
                "Show Thinking",
                value=st.session_state.show_thinking,
                key="show_thinking_input"
            )
            
            # Clear conversation button
            if st.button("Clear Conversation"):
                st.session_state.conversation = []
                st.session_state.streaming["text"] = ""
                st.session_state.streaming["tool_output"] = ""
                st.session_state.streaming["thinking"] = ""
                st.rerun()
        
        # Main conversation area
        conversation_container = st.container()
        
        # Display the conversation history
        with conversation_container:
            for i, message in enumerate(st.session_state.conversation):
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "user":
                    with st.chat_message("user"):
                        # Handle different content formats
                        if isinstance(content, str):
                            st.write(content)
                        elif isinstance(content, list):
                            for item in content:
                                if item.get("type") == "text":
                                    st.write(item.get("text", ""))
                                elif item.get("type") == "tool_result":
                                    st.info(f"Tool Result: {item.get('content', '')}")
                
                elif role == "assistant":
                    with st.chat_message("assistant"):
                        # Handle different content formats
                        if isinstance(content, str):
                            st.write(content)
                        elif isinstance(content, list):
                            for item in content:
                                if item.get("type") == "text":
                                    st.write(item.get("text", ""))
                                elif item.get("type") == "tool_use":
                                    st.info(f"Using tool: {item.get('name', '')}")
            
            # Display streaming content if active
            if st.session_state.streaming["active"]:
                with st.chat_message("assistant"):
                    st.write(st.session_state.streaming["text"])
                    
                    # Show tool information if a tool is active
                    if st.session_state.streaming["tool_active"]:
                        tool_name = st.session_state.streaming["tool_name"]
                        tool_input = st.session_state.streaming["tool_input"]
                        
                        st.info(f"Using tool: {tool_name}")
                        st.json(tool_input)
                        
                        # Show progress bar for the tool
                        st.progress(st.session_state.streaming["tool_progress"])
                        
                        # Show tool output if available
                        if st.session_state.streaming["tool_output"]:
                            st.code(st.session_state.streaming["tool_output"])
                    
                    # Show thinking if enabled
                    if st.session_state.show_thinking and st.session_state.streaming["thinking"]:
                        with st.expander("Thinking", expanded=True):
                            st.write(st.session_state.streaming["thinking"])
        
        # User input
        user_input = st.chat_input("Type your message here...", disabled=st.session_state.streaming["active"])
        
        # Handle user input
        logger.info(f"Received user input: {user_input[:100] if user_input else 'None'}...")
        if user_input:
            # Add user message to conversation
            st.session_state.conversation.append({
                "role": "user",
                "content": user_input
            })
            
            # Clear streaming state
            st.session_state.streaming = {
                "active": True,
                "container": None,
                "text": "",
                "tool_active": False,
                "tool_name": "",
                "tool_input": {},
                "tool_output": "",
                "tool_progress": 0.0,
                "thinking": ""
            }
            
            # Store the user input in session state to be processed after rerun
            st.session_state.last_input = user_input
            
            logger.warning(f"*** IMPORTANT: Stored user input in session state: '{user_input}'")
            logger.warning(f"*** Session state keys: {list(st.session_state.keys())}")
            logger.warning(f"*** Session streaming active: {st.session_state.streaming['active']}")
            
            try:
                # Test if we can skip the rerun and process directly
                if False:  # Set to True to test direct processing
                    logger.warning("*** DIRECT PROCESSING MODE ENABLED ***")
                    
                    async def direct_process():
                        await ui.process_user_input(user_input)
                    
                    asyncio.run(direct_process())
                else:
                    logger.warning("*** RERUN MODE ENABLED - Will process after rerun ***")
                    # Rerun to show the user message
                    st.rerun()
            except Exception as e:
                logger.error(f"Error in user input handling: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def update_streaming_text(self, text: str):
        """
        Update the streaming text in the UI.
        
        Args:
            text: The text to append
        """
        if not HAS_STREAMLIT:
            return
        
        # Append text to the streaming state
        st.session_state.streaming["text"] += text
        
        # Force update
        st.session_state.force_update = time.time()
        st.rerun()
    
    def update_tool_status(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        status: str,
        progress: float
    ):
        """
        Update the tool status in the UI.
        
        Args:
            tool_name: The name of the tool
            tool_input: The tool input parameters
            status: The current status of the tool
            progress: The current progress (0.0 to 1.0)
        """
        if not HAS_STREAMLIT:
            return
        
        # Update tool information in the streaming state
        st.session_state.streaming["tool_active"] = True
        st.session_state.streaming["tool_name"] = tool_name
        st.session_state.streaming["tool_input"] = tool_input
        st.session_state.streaming["tool_progress"] = progress
        
        # Force update
        st.session_state.force_update = time.time()
        st.rerun()
    
    def update_tool_output(self, output: str):
        """
        Update the tool output in the UI.
        
        Args:
            output: The tool output
        """
        if not HAS_STREAMLIT:
            return
        
        # Update tool output in the streaming state
        st.session_state.streaming["tool_output"] = output
        
        # Force update
        st.session_state.force_update = time.time()
        st.rerun()
    
    def update_thinking(self, thinking: str):
        """
        Update the thinking text in the UI.
        
        Args:
            thinking: The thinking text
        """
        if not HAS_STREAMLIT:
            return
        
        # Update thinking in the streaming state
        st.session_state.streaming["thinking"] = thinking
        
        # Force update if showing thinking
        if st.session_state.show_thinking:
            st.session_state.force_update = time.time()
            st.rerun()
    
    def finish_streaming(self):
        """Finish streaming and update conversation history."""
        if not HAS_STREAMLIT:
            return
        
        # Add the streamed content to the conversation history
        if st.session_state.streaming["text"]:
            st.session_state.conversation.append({
                "role": "assistant",
                "content": st.session_state.streaming["text"]
            })
        
        # Reset streaming state
        st.session_state.streaming["active"] = False
        st.session_state.streaming["text"] = ""
        st.session_state.streaming["tool_active"] = False
        st.session_state.streaming["tool_name"] = ""
        st.session_state.streaming["tool_input"] = {}
        st.session_state.streaming["tool_output"] = ""
        st.session_state.streaming["tool_progress"] = 0.0
        st.session_state.streaming["thinking"] = ""
        
        # Force update
        st.session_state.force_update = time.time()
        st.rerun()
    
    async def process_user_input(self, user_input: str):
        """
        Process user input and generate a response.
        
        Args:
            user_input: The user's message
        """
        if not HAS_STREAMLIT:
            return
        
        # Check for API key
        if not st.session_state.api_key:
            self.update_streaming_text("Please enter your Anthropic API key in the sidebar.")
            self.finish_streaming()
            return
        
        # Set up callbacks
        callbacks = {
            "on_text": self.update_streaming_text,
            "on_tool_use": lambda name, input: self.update_tool_status(name, input, "Starting", 0.0),
            "on_tool_progress": lambda name, input, status, progress: self.update_tool_status(name, input, status, progress),
            "on_tool_result": lambda name, input, result: self.update_tool_output(result.output or result.error or ""),
            "on_thinking": self.update_thinking
        }
        
        try:
            # Call the agent loop with streaming
            st.session_state.conversation = await agent_loop(
                user_input=user_input,
                conversation_history=st.session_state.conversation,
                api_key=st.session_state.api_key,
                model=st.session_state.model,
                max_tokens=st.session_state.max_tokens,
                thinking_budget=st.session_state.thinking_budget if st.session_state.thinking_budget > 0 else None,
                callbacks=callbacks
            )
        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}")
            self.update_streaming_text(f"Error: {str(e)}")
        finally:
            # Finish streaming
            self.finish_streaming()

# Main function to run the Streamlit app
def main():
    logger.info("Starting Claude UI main function")
    """Main function to run the Streamlit app."""
    if not HAS_STREAMLIT:
        print("Streamlit not available. Please install Streamlit with: pip install streamlit")
        return
    
    # Initialize the UI
    ui = ClaudeUI()
    
    # Check if there's a user input to process
    logger.info(f"Checking session state: active={st.session_state.streaming.get('active')}, has_last_input={'last_input' in st.session_state}")
    if st.session_state.streaming["active"] and "last_input" in st.session_state:
        logger.info(f"Processing user input: {st.session_state.last_input[:50]}...")
        
        # Create and run the async task
        async def process_input():
            try:
                logger.info("Starting async processing task")
                await ui.process_user_input(st.session_state.last_input)
                logger.info("Finished async processing task")
                # Only delete if processing completes successfully
                if "last_input" in st.session_state:
                    del st.session_state.last_input
                    logger.info("Deleted last_input from session state")
            except Exception as e:
                logger.error(f"Error in async process_input: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Run the async task
        logger.info("Running async task to process user input")
        try:
            asyncio.run(process_input())
            logger.info("Async task completed")
        except Exception as e:
            logger.error(f"Error running async task: {e}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()