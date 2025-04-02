#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Start Services
----------------------------------
This script starts the required services for the Conductor Framework,
including the EVE-OS Manager and MCP Server.
"""

import os
import sys
import logging
import argparse
import threading
import time
import signal
import uvicorn
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import modules from conductor framework
from src.eve.eve_manager import EVEManager
from src.mcp.mcp_server import app as mcp_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/services.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("services")

# Global variables for service threads
threads = []
stop_event = threading.Event()

def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) to gracefully stop services."""
    logger.info("Stopping services...")
    stop_event.set()
    
    # Wait for threads to finish
    for thread in threads:
        thread.join()
    
    logger.info("All services stopped")
    sys.exit(0)

def run_eve_manager():
    """Run the EVE-OS Manager."""
    logger.info("Starting EVE-OS Manager...")
    
    try:
        # Initialize EVE Manager
        eve_manager = EVEManager()
        eve_manager.initialize_eve_os()
        
        logger.info("EVE-OS Manager initialized")
        
        # Keep running until stop event is set
        while not stop_event.is_set():
            # Check system status periodically
            status = eve_manager.get_system_status()
            logger.debug(f"EVE-OS status: {status}")
            
            # Wait for stop event or timeout
            stop_event.wait(60)  # Check every 60 seconds
            
    except Exception as e:
        logger.error(f"Error in EVE-OS Manager: {e}")

def run_mcp_server():
    """Run the MCP Server."""
    logger.info("Starting MCP Server...")
    
    # Create uvicorn config
    config = uvicorn.Config(
        app=mcp_app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    
    # Create server
    server = uvicorn.Server(config)
    
    try:
        # Run server
        server.run()
    except Exception as e:
        logger.error(f"Error in MCP Server: {e}")

def main():
    """Main function to start services."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Start Conductor Framework services")
    parser.add_argument(
        "--services",
        nargs="+",
        choices=["all", "eve", "mcp"],
        default=["all"],
        help="Services to start (default: all)"
    )
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Determine which services to start
    start_eve = "all" in args.services or "eve" in args.services
    start_mcp = "all" in args.services or "mcp" in args.services
    
    # Start services
    if start_eve:
        eve_thread = threading.Thread(target=run_eve_manager)
        eve_thread.daemon = True
        eve_thread.start()
        threads.append(eve_thread)
    
    if start_mcp:
        # Run MCP server in the main thread
        # This is because uvicorn needs to be in the main thread
        if start_eve:
            # If EVE is also running, start MCP in a subprocess
            import subprocess
            
            logger.info("Starting MCP Server in a subprocess...")
            mcp_process = subprocess.Popen([
                sys.executable,
                "-m",
                "uvicorn",
                "src.mcp.mcp_server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001"
            ])
            
            # Wait for stop event
            try:
                while not stop_event.is_set():
                    time.sleep(1)
            finally:
                # Stop MCP process
                mcp_process.terminate()
                mcp_process.wait()
        else:
            # If only MCP is running, start it in the main thread
            run_mcp_server()
    
    logger.info("All services started")
    
    # Keep main thread alive
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    main()
