"""
Integration Framework for Anthropic Quickstarts and Custom Streaming

This module provides a bridge between the official Anthropic Quickstarts Computer Use Demo
and our custom streaming implementation. It allows using both implementations together
while maintaining stability and adding advanced features.

Usage:
- Import from official Anthropic implementation where stable
- Override specific functionality with our custom streaming implementation
- Use feature toggles to control which implementation is active
"""

import os
import sys
import asyncio
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dccc_integration")

# Set up paths to both implementations
ANTHROPIC_PATH = "/home/computeruse/computer_use_demo"
CUSTOM_PATH = "/home/computeruse/computer_use_demo_custom"

# Ensure paths are in sys.path
if ANTHROPIC_PATH not in sys.path:
    sys.path.insert(0, ANTHROPIC_PATH)
if CUSTOM_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_PATH)

# Feature toggles for controlling which implementation to use
class FeatureToggle(Enum):
    USE_STREAMING = "use_streaming"
    USE_THINKING = "use_thinking" 
    USE_ROSETTA_STONE = "use_rosetta_stone"
    USE_STREAMLIT_CONTINUITY = "use_streamlit_continuity"

# Default feature states
FEATURE_DEFAULTS = {
    FeatureToggle.USE_STREAMING: True,
    FeatureToggle.USE_THINKING: True,
    FeatureToggle.USE_ROSETTA_STONE: False,
    FeatureToggle.USE_STREAMLIT_CONTINUITY: True
}

class IntegrationBridge:
    """
    Bridge class that integrates the official Anthropic implementation with
    our custom streaming features.
    """
    
    def __init__(self, feature_toggles: Optional[Dict[FeatureToggle, bool]] = None):
        """
        Initialize the integration bridge with feature toggles.
        
        Args:
            feature_toggles: Optional dictionary of feature toggles to override defaults
        """
        self.features = dict(FEATURE_DEFAULTS)
        if feature_toggles:
            self.features.update(feature_toggles)
        
        self.logger = logger
        self.logger.info(f"Integration Bridge initialized with features: {self.features}")
        
        # Import both implementations
        self._import_implementations()
    
    def _import_implementations(self):
        """Import components from both implementations based on active features"""
        try:
            # Always import base components from Anthropic implementation
            import loop as anthropic_loop
            import streamlit as anthropic_streamlit
            from tools import ToolCollection, ToolResult
            
            self.anthropic_loop = anthropic_loop
            self.anthropic_streamlit = anthropic_streamlit
            self.ToolCollection = ToolCollection
            self.ToolResult = ToolResult
            
            self.logger.info("Successfully imported Anthropic implementation components")
            
            # Import custom implementation components if needed
            if any(self.features.values()):
                # Attempt to import our custom streaming implementation
                if self.features[FeatureToggle.USE_STREAMING]:
                    try:
                        from unified_streaming_loop import unified_streaming_agent_loop
                        self.unified_streaming_agent_loop = unified_streaming_agent_loop
                        self.logger.info("Successfully imported custom streaming implementation")
                    except ImportError as e:
                        self.logger.warning(f"Failed to import custom streaming: {str(e)}")
                        self.features[FeatureToggle.USE_STREAMING] = False
                
                # Import streamlit continuity if enabled
                if self.features[FeatureToggle.USE_STREAMLIT_CONTINUITY]:
                    try:
                        from continuity import save_state, restore_state
                        self.save_state = save_state
                        self.restore_state = restore_state
                        self.logger.info("Successfully imported streamlit continuity implementation")
                    except ImportError as e:
                        self.logger.warning(f"Failed to import streamlit continuity: {str(e)}")
                        self.features[FeatureToggle.USE_STREAMLIT_CONTINUITY] = False
                
                # Import ROSETTA STONE protocol if enabled
                if self.features[FeatureToggle.USE_ROSETTA_STONE]:
                    try:
                        from rosetta_stone import format_message, parse_message
                        self.format_message = format_message
                        self.parse_message = parse_message
                        self.logger.info("Successfully imported ROSETTA STONE protocol")
                    except ImportError as e:
                        self.logger.warning(f"Failed to import ROSETTA STONE protocol: {str(e)}")
                        self.features[FeatureToggle.USE_ROSETTA_STONE] = False
        
        except ImportError as e:
            self.logger.error(f"Failed to import required components: {str(e)}")
            raise
    
    async def sampling_loop(self, **kwargs):
        """
        Wrapper for the sampling loop function that chooses between implementations.
        
        This function will use either the official Anthropic implementation or our
        custom streaming implementation based on feature toggles.
        """
        if self.features[FeatureToggle.USE_STREAMING]:
            self.logger.info("Using custom streaming implementation for sampling loop")
            try:
                # Add thinking parameter if enabled
                if self.features[FeatureToggle.USE_THINKING] and "thinking_budget" not in kwargs:
                    kwargs["thinking_budget"] = 4000  # Default thinking budget
                
                # Call our custom streaming implementation
                return await self.unified_streaming_agent_loop(**kwargs)
            except Exception as e:
                self.logger.error(f"Error in custom streaming implementation: {str(e)}")
                self.logger.info("Falling back to Anthropic implementation")
                # Fall back to Anthropic implementation if our custom one fails
                return await self.anthropic_loop.sampling_loop(**kwargs)
        else:
            self.logger.info("Using Anthropic implementation for sampling loop")
            return await self.anthropic_loop.sampling_loop(**kwargs)
    
    def handle_streamlit_reload(self, st_session_state, filename):
        """
        Handle Streamlit reloading to maintain conversation state.
        
        Args:
            st_session_state: Streamlit session state
            filename: File that triggered the reload
        """
        if not self.features[FeatureToggle.USE_STREAMLIT_CONTINUITY]:
            self.logger.info("Streamlit continuity feature disabled, not handling reload")
            return
        
        try:
            self.logger.info(f"Handling Streamlit reload triggered by {filename}")
            # Save state before reload
            self.save_state(st_session_state)
            # State will be restored when Streamlit restarts
        except Exception as e:
            self.logger.error(f"Error handling Streamlit reload: {str(e)}")

    def format_rosetta_stone(self, sender, topic, message):
        """
        Format a message using the ROSETTA STONE protocol if enabled.
        
        Args:
            sender: The sender identifier
            topic: The message topic
            message: The message content
            
        Returns:
            Formatted message string
        """
        if not self.features[FeatureToggle.USE_ROSETTA_STONE]:
            return message
        
        try:
            return self.format_message(sender, topic, message)
        except Exception as e:
            self.logger.error(f"Error formatting ROSETTA STONE message: {str(e)}")
            return message

# Initialize the integration bridge
def create_bridge(feature_toggles=None):
    """Create and return an IntegrationBridge instance"""
    return IntegrationBridge(feature_toggles)

# Example usage
if __name__ == "__main__":
    bridge = create_bridge()
    print(f"Integration bridge initialized with features: {bridge.features}")
    
    # Example of using the bridge to run the sampling loop
    async def test_bridge():
        user_input = "Take a screenshot and describe what you see."
        messages = [{"role": "user", "content": user_input}]
        
        result = await bridge.sampling_loop(
            messages=messages,
            model="claude-3-7-sonnet-20250219",
            output_callback=lambda x: print(x.get("text", "") if x.get("type") == "text" else ""),
            tool_output_callback=lambda x, y: print(f"Tool output: {x.output}"),
            api_response_callback=lambda x, y, z: None,
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            thinking_budget=4000
        )
        print("Sampling loop completed:", result is not None)
    
    asyncio.run(test_bridge())