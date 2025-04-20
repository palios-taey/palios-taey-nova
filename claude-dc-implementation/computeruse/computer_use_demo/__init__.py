"""
Claude DC Computer Use Demo
This module contains the constants and imports needed for the Claude DC implementation.
"""

import os
import logging
from typing import Literal, get_args

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

# API provider enumeration
class APIProvider:
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

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
    "APIProvider"
]