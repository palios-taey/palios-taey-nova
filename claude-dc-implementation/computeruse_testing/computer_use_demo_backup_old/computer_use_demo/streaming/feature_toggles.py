"""
Feature toggle module for the streaming implementation.
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger("feature_toggles")

# Load feature toggles from the JSON file
FEATURE_TOGGLES_PATH = Path(__file__).parent / "feature_toggles.json"

def load_feature_toggles():
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

def get_feature_toggles():
    """Get feature toggles, loading from file if not cached."""
    global _feature_toggles
    if _feature_toggles is None:
        _feature_toggles = load_feature_toggles()
    return _feature_toggles

def is_feature_enabled(feature_name):
    """Check if a feature is enabled in the toggles."""
    toggles = get_feature_toggles()
    return toggles.get(feature_name, False)

def get_feature_setting(setting_name, default_value=None):
    """Get a feature setting value from the toggles."""
    toggles = get_feature_toggles()
    return toggles.get(setting_name, default_value)

def reload_feature_toggles():
    """Force reload of feature toggles from file."""
    global _feature_toggles
    _feature_toggles = load_feature_toggles()
    return _feature_toggles