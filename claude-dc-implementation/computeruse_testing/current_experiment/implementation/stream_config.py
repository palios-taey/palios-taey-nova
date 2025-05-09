"""
Configuration module for streaming experiments.
Contains constants and settings for the streaming tests.
"""

import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stream_experiment')

# Ensure logs directory exists
EXPERIMENT_DIR = Path(__file__).parent.parent
LOGS_DIR = EXPERIMENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure file handler for logging
file_handler = logging.FileHandler(LOGS_DIR / "streaming_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Core constants
DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
COMPUTER_USE_BETA = "computer-use-2025-01-24"
TOOL_VERSION = "computer_use_20250124"

# Feature flags - All beta features disabled except for basic streaming
ENABLE_STREAMING = True  # Always enable streaming
ENABLE_THINKING = True   # Enable thinking tokens
ENABLE_PROMPT_CACHING = False
ENABLE_EXTENDED_OUTPUT = False
ENABLE_TOKEN_EFFICIENT = False

# Test parameters
MAX_TOKENS = 4096  # Small limit for test
THINKING_BUDGET = 2048 if ENABLE_THINKING else None

# Simple test prompt that encourages Claude to use a tool
TEST_PROMPT = "Hello Claude! Could you please run the 'date' command to show me the current date and time? Then explain what day of the week it is."

# API provider
API_PROVIDER = "anthropic"

logger.info(f"Configuration loaded with streaming: {ENABLE_STREAMING}")
logger.info(f"Using model: {DEFAULT_MODEL}")
logger.info(f"Beta features: Prompt Caching={ENABLE_PROMPT_CACHING}, Extended Output={ENABLE_EXTENDED_OUTPUT}, Token Efficient={ENABLE_TOKEN_EFFICIENT}")