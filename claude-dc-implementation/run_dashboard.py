#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Run Dashboard
---------------------------------
This script starts the Streamlit dashboard for the Conductor Framework.
"""

import os
import sys
import subprocess
import argparse
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard")

def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) to gracefully stop services."""
    logger.info("Stopping dashboard...")
    sys.exit(0)

def main():
    """Main function to start the dashboard."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Start Conductor Framework dashboard")
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the dashboard on (default: 8501)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to run the dashboard on (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get the dashboard path
    dashboard_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "src",
        "dashboard",
        "app.py"
    )
    
    # Check if the dashboard file exists
    if not os.path.exists(dashboard_path):
        logger.error(f"Dashboard file not found: {dashboard_path}")
        sys.exit(1)
    
    # Start the dashboard
    logger.info(f"Starting dashboard on {args.host}:{args.port}")
    
    # Create the streamlit command
    cmd = [
        "streamlit",
        "run",
        dashboard_path,
        "--server.port",
        str(args.port),
        "--server.address",
        args.host
    ]
    
    try:
        # Run the command
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    main()