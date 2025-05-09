"""
Feature toggle management for the streaming implementation.

This module provides functions to get feature toggles from the JSON configuration file
and check if specific features are enabled.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger("feature_toggles")

# Path to feature toggles JSON file
FEATURE_TOGGLES_PATH = Path(__file__).parent / "feature_toggles.json"

# Default feature toggle values
DEFAULT_FEATURE_TOGGLES = {
    "use_streaming_thinking": True,
    "enable_tool_thinking": True,
    "tool_thinking_budget": 2000,
    "api_model": "claude-3-7-sonnet-20250219",
    "use_xml_prompts": True,
    "enable_buffer_delay": True,
    "buffer_delay_ms": 1000,
    "max_tokens": 64000,
    "enable_tool_buffer": True,
    "debug_logging": True,
    "use_response_chunking": True
}

def get_feature_toggles() -> Dict[str, Any]:
    """
    Get feature toggle configuration from JSON file.
    
    Returns:
        Dict with feature toggle values.
    """
    try:
        # Try to load from JSON file
        if FEATURE_TOGGLES_PATH.exists():
            with open(FEATURE_TOGGLES_PATH, "r") as f:
                feature_toggles = json.load(f)
                logger.info(f"Loaded feature toggles from {FEATURE_TOGGLES_PATH}")
                return feature_toggles
    except Exception as e:
        logger.warning(f"Error loading feature toggles: {str(e)}")
    
    # Fall back to defaults
    logger.info("Using default feature toggles")
    return DEFAULT_FEATURE_TOGGLES.copy()

def is_feature_enabled(feature_name: str, default: bool = False) -> bool:
    """
    Check if a specific feature is enabled.
    
    Args:
        feature_name: Name of the feature to check
        default: Default value if feature is not found
        
    Returns:
        True if feature is enabled, False otherwise
    """
    try:
        feature_toggles = get_feature_toggles()
        return bool(feature_toggles.get(feature_name, default))
    except Exception as e:
        logger.error(f"Error checking feature {feature_name}: {str(e)}")
        return default

def get_feature_value(feature_name: str, default: Any = None) -> Any:
    """
    Get the value of a specific feature.
    
    Args:
        feature_name: Name of the feature to get
        default: Default value if feature is not found
        
    Returns:
        Value of the feature or default
    """
    try:
        feature_toggles = get_feature_toggles()
        return feature_toggles.get(feature_name, default)
    except Exception as e:
        logger.error(f"Error getting feature {feature_name}: {str(e)}")
        return default