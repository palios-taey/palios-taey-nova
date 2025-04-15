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
sys.path.append("/home/computeruse/computer_use_demo")

# Import dependencies
# Import streaming client
from streaming.streaming_client import StreamingClient
from token_management.token_manager import TokenManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("computer_use.loop")

class ComputerUseLoop:
    """Main event loop handler for Computer Use"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the event loop with configuration"""
        self.config = config or {}
        self.running = False
        self.token_manager = TokenManager()
        self.streaming_client = StreamingClient(token_manager=self.token_manager)
        
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
    
    def stop(self):
        """Stop the main event loop"""
        logger.info("Stopping main event loop")
        self.running = False
    
    def _run_loop(self):
        """Execute the main event processing loop"""
        while self.running:
            try:
                # Process any pending requests using streaming
                self._process_pending_requests()
                
                # Use streaming for long-running operations
                if self.current_request and self.current_request.get("long_running"):
                    self._handle_long_running_request_with_streaming()
                
                # Perform periodic maintenance
                self._perform_maintenance()
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in loop iteration: {str(e)}")
                # Dont crash the loop on individual request errors
                time.sleep(1)  # Delay before retry on error
    
    def _process_pending_requests(self):
        """Process any pending requests in the queue"""
        # Implementation would check for new requests
        # And process them with streaming support
        pass
    
    def _handle_long_running_request_with_streaming(self):
        """Use streaming client to handle long-running operations"""
        try:
            # Example of using streaming client for long operations
            response_stream = self.streaming_client.get_completion(
                messages=self.current_request.get("messages", []),
                max_tokens=self.current_request.get("max_tokens", 4000)
            )
            
            # Process the streaming response
            for chunk in response_stream:
                self.streaming_client.process_streaming_chunk(chunk)
                
                # Update UI with streaming chunks via streamlit
                self._update_ui_with_chunk(chunk)
                
            logger.info("Completed streaming operation")
        except Exception as e:
            logger.error(f"Error in streaming operation: {str(e)}")
    
    def _update_ui_with_chunk(self, chunk):
        """Send streaming chunk to UI"""
        # Would implement UI update mechanism
        # Streamlit would receive this update
        pass
    
    def _perform_maintenance(self):
        """Perform periodic system maintenance"""
        current_time = time.time()
        
        # Only run maintenance every 5 minutes
        if current_time - self.last_execution_time > 300:
            logger.info("Performing system maintenance")
            
            # Maintain streaming connection
            self.streaming_client.maintain_stream_connection()
            
            # Check token limits
            self.streaming_client.check_token_limits()
            
            self.last_execution_time = current_time

# Global instance that can be imported by other modules
loop_instance = ComputerUseLoop()

def start_loop():
    """Start the main event loop with streaming enabled"""
    loop_instance.start()

def stop_loop():
    """Stop the main event loop"""
    loop_instance.stop()

if __name__ == "__main__":
    logger.info("Starting Computer Use Loop directly")
    start_loop()
