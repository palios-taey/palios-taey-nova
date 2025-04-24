#!/usr/bin/env python3
"""
CLI script for running the DC agent loop.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to the system path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(current_dir / "logs" / "dc_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dc_cli")

# Import our agent loop
from dc_agent_loop import dc_main

if __name__ == "__main__":
    try:
        # Report startup
        logger.info("Starting DC CLI")
        
        # Create log directory if it doesn't exist
        log_dir = current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Run the main function
        asyncio.run(dc_main())
    except KeyboardInterrupt:
        logger.info("Exiting due to keyboard interrupt")
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\nUnexpected error: {str(e)}")