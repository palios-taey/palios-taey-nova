"""
Main event loop for Claude Computer Use

This module handles the main execution loop for processing user requests and managing
the state of the computer use environment.
"""
import os
import sys
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple

# Configure core system paths
sys.path.append('/home/computeruse/computer_use_demo')

# Import dependencies
# Import streaming client
from streaming.streaming_client import StreamingClient
from token_management.token_manager import TokenManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('computer_use.loop')

class ComputerUseLoop:
    """Main event loop handler for Computer Use"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the event loop with configuration"""
        self.config = config or {}
        self.running = False
        self.token_manager = TokenManager()
        self.streaming_client = StreamingClient()
        
        # Track execution states
        self.current_request = None
        self.last_execution_time = 0
        self.execution_count = 0
        
        logger.info("ComputerUseLoop initialized with streaming support")
    
    def start(self):
        """Start the main event loop"""
        self.running = True
        logger.info("Starting main event loop with streaming enabled")
        
        try:
            self._run_loop()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            self.running = False
            raise