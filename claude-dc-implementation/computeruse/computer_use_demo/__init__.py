"""
Claude DC Computer Use Demo
This module contains the constants and imports needed for the Claude DC implementation.
"""

import os
import logging
import sys
from typing import Literal, get_args
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc')

# Beta feature flags
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"
TOKEN_EFFICIENT_TOOLS_BETA_FLAG = "token-efficient-tools-2025-02-19"

# Default token settings for output
DEFAULT_MAX_TOKENS = 65536  # ~64k max output
DEFAULT_THINKING_BUDGET = 32768  # ~32k thinking budget

# Tool versions
ToolVersion = Literal["computer_use_20241022", "computer_use_20250124"]

# Environment-specific paths
MODE = os.getenv('CLAUDE_ENV', 'live')

# Detect container environment
running_in_container = os.path.exists("/home/computeruse")

# Configure directories based on environment
if running_in_container:
    # We're inside the container, use the container paths
    if MODE == "dev":
        BACKUP_DIR = "/home/computeruse/dev_backups/"
        LOG_DIR = "/home/computeruse/dev_logs/"
    else:
        BACKUP_DIR = "/home/computeruse/my_stable_backup_complete/"
        LOG_DIR = "/home/computeruse/logs/"
    
    # Create directories if they don't exist
    for directory in [BACKUP_DIR, LOG_DIR]:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create directory {directory}: {e}")
else:
    # We're on the host machine, use temporary paths for validation
    temp_dir = str(Path.home() / ".claude_dc_temp")
    BACKUP_DIR = f"{temp_dir}/backups/"
    LOG_DIR = f"{temp_dir}/logs/"
    
    # Create local temp directories for validation
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception as e:
        logger.warning(f"Failed to create local directory: {e}")

# Parse boolean environment variables safely
def get_bool_env(name, default=False):
    """Parse boolean environment variables with proper error handling."""
    value = os.getenv(name)
    if value is None:
        return default
    
    value = value.lower()
    if value in ('true', 't', 'yes', 'y', '1'):
        return True
    elif value in ('false', 'f', 'no', 'n', '0'):
        return False
    else:
        logger.warning(f"Invalid boolean value for {name}: '{value}', using default: {default}")
        return default

# Feature flags - control which features are enabled
# Read from environment with fallbacks - with explicit defaults
try:
    # Set conservative defaults
    ENABLE_PROMPT_CACHING = get_bool_env('ENABLE_PROMPT_CACHING', False)
    ENABLE_EXTENDED_OUTPUT = get_bool_env('ENABLE_EXTENDED_OUTPUT', False)
    ENABLE_THINKING = get_bool_env('ENABLE_THINKING', True)  # Thinking is always useful
    ENABLE_TOKEN_EFFICIENT = get_bool_env('ENABLE_TOKEN_EFFICIENT', False)  # Default to False for stability
    
    # Streaming is now a core feature, not a beta flag
    ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to True - this is a key feature
except Exception as e:
    # If there's any error reading environment, use safe defaults
    logger.error(f"Error reading feature flags from environment: {e}")
    logger.warning("Using safe default feature flag configuration")
    ENABLE_PROMPT_CACHING = False
    ENABLE_EXTENDED_OUTPUT = False
    ENABLE_THINKING = True
    ENABLE_TOKEN_EFFICIENT = False
    ENABLE_STREAMING = True  # Always enable streaming by default

# Log feature flag status
logger.info(f"Feature Flags => Streaming: {ENABLE_STREAMING}, Prompt Caching: {ENABLE_PROMPT_CACHING}, "
            f"Extended Output: {ENABLE_EXTENDED_OUTPUT}, Thinking: {ENABLE_THINKING}, "
            f"Token-Efficient: {ENABLE_TOKEN_EFFICIENT}")

# Let's print these to stdout too so they're visible in the UI
print(f"Claude DC Enabled Features:")
print(f"- Streaming Responses: {'✅ enabled' if ENABLE_STREAMING else '❌ disabled'}")
print(f"- Prompt Caching: {'✅ enabled' if ENABLE_PROMPT_CACHING else '❌ disabled'}")
print(f"- Extended Output: {'✅ enabled' if ENABLE_EXTENDED_OUTPUT else '❌ disabled'}")
print(f"- Thinking: {'✅ enabled' if ENABLE_THINKING else '❌ disabled'}")
print(f"- Token-Efficient: {'✅ enabled' if ENABLE_TOKEN_EFFICIENT else '❌ disabled'}")

# API provider enumeration
class APIProvider:
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

# Get provider from environment with fallback
DEFAULT_PROVIDER = os.getenv('API_PROVIDER', APIProvider.ANTHROPIC)

# Exported variables
__all__ = [
    "PROMPT_CACHING_BETA_FLAG",
    "OUTPUT_128K_BETA_FLAG", 
    "TOKEN_EFFICIENT_TOOLS_BETA_FLAG",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_THINKING_BUDGET",
    "ToolVersion",
    "BACKUP_DIR",
    "LOG_DIR", 
    "MODE",
    "APIProvider",
    "DEFAULT_PROVIDER",
    "ENABLE_PROMPT_CACHING",
    "ENABLE_EXTENDED_OUTPUT",
    "ENABLE_THINKING",
    "ENABLE_TOKEN_EFFICIENT",
    "ENABLE_STREAMING",  # Added this to exports
    "get_bool_env"
]