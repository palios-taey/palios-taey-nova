"""
Integration module for streaming capabilities in Claude DC.

This module provides the integration between the original Claude DC implementation
and the streaming implementation. It allows for controlled deployment of streaming
features through feature toggles.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("claude_dc_streaming.log")
    ]
)
logger = logging.getLogger("streaming_integration")

# Load feature toggles
FEATURE_TOGGLES_PATH = Path(__file__).parent / "streaming" / "feature_toggles.json"

def load_feature_toggles() -> Dict[str, Any]:
    """Load feature toggles from the JSON configuration file."""
    try:
        if FEATURE_TOGGLES_PATH.exists():
            with open(FEATURE_TOGGLES_PATH, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Feature toggles file not found at {FEATURE_TOGGLES_PATH}")
            return {
                "use_streaming_bash": True,
                "use_streaming_file": True,
                "use_streaming_screenshot": False,
                "use_unified_streaming": True,
                "use_streaming_thinking": True,
                "max_thinking_tokens": 4000,
                "log_level": "INFO"
            }
    except Exception as e:
        logger.error(f"Error loading feature toggles: {str(e)}")
        return {
            "use_streaming_bash": True,
            "use_streaming_file": True,
            "use_streaming_screenshot": False,
            "use_unified_streaming": False,  # Default to False on error
            "use_streaming_thinking": True,
            "max_thinking_tokens": 4000,
            "log_level": "INFO"
        }

# Global feature toggle cache
_feature_toggles = None

def get_feature_toggles() -> Dict[str, Any]:
    """Get feature toggles, loading from file if not cached."""
    global _feature_toggles
    if _feature_toggles is None:
        _feature_toggles = load_feature_toggles()
    return _feature_toggles

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled in the toggles."""
    toggles = get_feature_toggles()
    return toggles.get(feature_name, False)

def get_feature_setting(setting_name: str, default_value: Any = None) -> Any:
    """Get a feature setting value from the toggles."""
    toggles = get_feature_toggles()
    return toggles.get(setting_name, default_value)

def reload_feature_toggles() -> Dict[str, Any]:
    """Force reload of feature toggles from file."""
    global _feature_toggles
    _feature_toggles = load_feature_toggles()
    return _feature_toggles

async def async_sampling_loop(*args, **kwargs):
    """
    Integration function that delegates to either the original sampling loop
    or the streaming implementation based on feature toggles.
    """
    
    # Check if unified streaming is enabled
    if is_feature_enabled("use_unified_streaming"):
        try:
            # Import the streaming implementation
            from streaming.unified_streaming_loop import unified_streaming_agent_loop
            
            logger.info("Using unified streaming implementation")
            return await unified_streaming_agent_loop(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in unified streaming implementation: {str(e)}")
            logger.exception("Streaming implementation failed, falling back to original")
            
            # Fall back to original implementation on error
            from loop import sampling_loop
            return await sampling_loop(*args, **kwargs)
    else:
        # Use the original implementation
        from loop import sampling_loop
        logger.info("Using original non-streaming implementation")
        return await sampling_loop(*args, **kwargs)

# For backward compatibility
sampling_loop = async_sampling_loop