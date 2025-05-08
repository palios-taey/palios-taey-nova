#!/usr/bin/env python3
"""
Buffered Claude DC runner with race condition fix.

This script launches Claude DC with a buffer pattern integrated to prevent
the race condition during streaming function calls.
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("buffered_claude_dc.log")
    ]
)
logger = logging.getLogger("buffered_claude_dc")

def setup_environment():
    """Set up the environment variables for buffer integration."""
    os.environ["CLAUDE_DC_USE_BUFFER"] = "1"
    os.environ["CLAUDE_DC_USE_XML_PROMPT"] = "1"
    logger.info("Environment variables set for buffer integration")

def check_api_key():
    """Check if ANTHROPIC_API_KEY is set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set!")
        print("Error: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set the ANTHROPIC_API_KEY environment variable and try again.")
        sys.exit(1)
    logger.info("ANTHROPIC_API_KEY environment variable found")

def create_symlinks():
    """Create symlinks to ensure our buffer is used."""
    try:
        # Ensure the streaming directory exists
        if not Path("streaming").exists():
            os.makedirs("streaming", exist_ok=True)
        
        # Create symlinks to our buffer implementation
        buffer_source = Path("streaming/tool_use_buffer.py")
        if buffer_source.exists():
            logger.info(f"Using buffer implementation at {buffer_source}")
        else:
            logger.error(f"Buffer implementation not found at {buffer_source}")
            sys.exit(1)
            
        # Ensure XML prompt is used
        xml_prompt_source = Path("streaming/xml_function_prompt.py")
        if xml_prompt_source.exists():
            logger.info(f"Using XML function prompt at {xml_prompt_source}")
        else:
            logger.error(f"XML function prompt not found at {xml_prompt_source}")
            sys.exit(1)
            
        logger.info("Buffer integration prepared")
    except Exception as e:
        logger.error(f"Error creating symlinks: {str(e)}")
        sys.exit(1)

def run_claude_dc(mode="streamlit"):
    """
    Run Claude DC with buffer integration.
    
    Args:
        mode: The mode to run Claude DC in (streamlit, direct, etc.)
    """
    try:
        if mode == "streamlit":
            # Run streamlit version
            cmd = ["streamlit", "run", "streamlit_streaming.py"]
            logger.info(f"Starting Claude DC with Streamlit: {' '.join(cmd)}")
            subprocess.run(cmd)
        else:
            # Run direct version
            logger.info("Starting Claude DC in direct mode")
            from streaming.unified_streaming_loop import demo_unified_streaming
            import asyncio
            asyncio.run(demo_unified_streaming())
    except KeyboardInterrupt:
        logger.info("Claude DC stopped by user")
    except Exception as e:
        logger.error(f"Error running Claude DC: {str(e)}")
        sys.exit(1)

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run buffered Claude DC to fix race condition")
    parser.add_argument("--mode", choices=["streamlit", "direct"], default="streamlit",
                      help="Mode to run Claude DC in (streamlit or direct)")
    args = parser.parse_args()
    
    # Print banner
    print("=" * 50)
    print("Buffered Claude DC Runner")
    print("(Race Condition Fix for Streaming Function Calls)")
    print("=" * 50)
    
    # Setup
    check_api_key()
    setup_environment()
    create_symlinks()
    
    # Run Claude DC
    run_claude_dc(args.mode)

if __name__ == "__main__":
    main()