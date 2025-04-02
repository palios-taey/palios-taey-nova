#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Start Script for Communication Dashboard
--------------------------------------
This script starts the Communication Dashboard and any required services
for the Palios-Taey-Nova integrated AI communication system.
"""

import os
import sys
import time
import json
import logging
import subprocess
import threading
import signal
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("start_dashboard")

# Default ports
DEFAULT_PORTS = {
    "mcp_server": 8001,
    "webhook": 8000,
    "demo_server": 8002,
    "dashboard": 8502
}

# Commands to start each service
SERVICE_COMMANDS = {
    "mcp_server": [
        "python", 
        "-m", 
        "src.mcp.mcp_server"
    ],
    "webhook": [
        "python", 
        "-m", 
        "src.webhook.server"
    ],
    "demo_server": [
        "python", 
        "demo_server.py"
    ],
    "dashboard": [
        "streamlit", 
        "run", 
        "communication_dashboard.py",
        "--server.port={port}",
        "--server.address=0.0.0.0"
    ]
}

# Global process dictionary
processes = {}

def start_service(service: str, port: int = None) -> Optional[subprocess.Popen]:
    """
    Start a service with the given port.
    
    Args:
        service: Name of the service to start
        port: Port to run the service on (or None for default)
        
    Returns:
        Subprocess Popen object or None if failed
    """
    if service not in SERVICE_COMMANDS:
        logger.error(f"Unknown service: {service}")
        return None
    
    # Check if MCP server exists
    if service == "mcp_server" and not os.path.exists("src/mcp/mcp_server.py"):
        logger.warning("MCP server not found. Creating a minimal placeholder...")
        
        # Create directory if it doesn't exist
        os.makedirs("src/mcp", exist_ok=True)
        
        # Create a minimal placeholder MCP server
        with open("src/mcp/mcp_server.py", "w") as f:
            f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal MCP Server Placeholder
This is a minimal placeholder for the MCP Server to allow the dashboard to start.
"""

import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server_placeholder")

# Create FastAPI app
app = FastAPI(title="MCP Server Placeholder")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": "MCP Server Placeholder"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "MCP Server Placeholder is running"}

@app.post("/api/context")
async def context(request: Request):
    data = await request.json()
    logger.info(f"Received request: {data}")
    return {
        "source_model": data.get("target_model", "placeholder"),
        "target_model": data.get("source_model", "dashboard"),
        "response_type": "chat",
        "content": "This is a placeholder MCP server. The actual MCP server implementation is not available.",
        "tokens_used": 0,
        "confidence": 0.0,
        "timestamp": "2025-04-02T12:00:00Z"
    }

@app.post("/api/bridge/claude-to-grok")
async def claude_to_grok(request: Request):
    data = await request.json()
    logger.info(f"Received Claude to Grok bridge request: {data}")
    return {
        "source_model": "grok",
        "target_model": "claude",
        "response_type": "bridge",
        "content": f"Claude to Grok bridge placeholder response for: {data.get('topic', 'unknown topic')}",
        "tokens_used": 0,
        "confidence": 0.0,
        "timestamp": "2025-04-02T12:00:00Z"
    }

@app.post("/api/bridge/grok-to-claude")
async def grok_to_claude(request: Request):
    data = await request.json()
    logger.info(f"Received Grok to Claude bridge request: {data}")
    return {
        "source_model": "claude",
        "target_model": "grok",
        "response_type": "bridge",
        "content": f"Grok to Claude bridge placeholder response for: {data.get('topic', 'unknown topic')}",
        "tokens_used": 0,
        "confidence": 0.0,
        "timestamp": "2025-04-02T12:00:00Z"
    }

@app.post("/api/wave")
async def wave(request: Request):
    data = await request.json()
    logger.info(f"Received wave request: {data}")
    return {
        "source_model": data.get("target_model", "placeholder"),
        "target_model": data.get("source_model", "dashboard"),
        "response_type": "wave",
        "content": "Wave communication placeholder response",
        "tokens_used": 0,
        "confidence": 0.0,
        "timestamp": "2025-04-02T12:00:00Z"
    }

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
''')
        
        # Create __init__.py if it doesn't exist
        if not os.path.exists("src/mcp/__init__.py"):
            with open("src/mcp/__init__.py", "w") as f:
                f.write("# MCP module\n")
        
        logger.info("Placeholder MCP server created successfully.")
    
    # Check if webhook server exists
    if service == "webhook" and not os.path.exists("src/webhook/server.py"):
        logger.warning("Webhook server not found. Creating a minimal placeholder...")
        
        # Create directory if it doesn't exist
        os.makedirs("src/webhook", exist_ok=True)
        
        # Create a minimal placeholder webhook server
        with open("src/webhook/server.py", "w") as f:
            f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal Webhook Server Placeholder
This is a minimal placeholder for the Webhook Server to allow the dashboard to start.
"""

import os
import json
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook_placeholder")

# Constants
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "user-family-community-society")

# Create FastAPI app
app = FastAPI(title="Webhook Server Placeholder")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_signature(request: Request, x_claude_signature: str = Header(None)):
    """Verify webhook signature."""
    if not x_claude_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get request body
    body = await request.body()
    
    # Compute expected signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(x_claude_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return await request.json()

@app.get("/")
async def root():
    return {"status": "online", "message": "Webhook Server Placeholder"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Webhook Server Placeholder is running"}

@app.post("/webhook")
async def webhook(data: dict = Depends(verify_signature)):
    logger.info(f"Received webhook: {data}")
    
    # Get operation type
    operation = data.get("operation")
    
    if operation == "deploy_code":
        return {"status": "success", "message": "Deploy code operation acknowledged (placeholder)"}
    elif operation == "modify_db":
        return {"status": "success", "message": "Modify DB operation acknowledged (placeholder)"}
    elif operation == "file_transfer":
        return {"status": "success", "message": "File transfer operation acknowledged (placeholder)"}
    elif operation == "run_command":
        return {"status": "success", "message": "Run command operation acknowledged (placeholder)"}
    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
''')
        
        # Create __init__.py if it doesn't exist
        if not os.path.exists("src/webhook/__init__.py"):
            with open("src/webhook/__init__.py", "w") as f:
                f.write("# Webhook module\n")
        
        logger.info("Placeholder webhook server created successfully.")
    
    # Get the command
    cmd = SERVICE_COMMANDS[service].copy()
    
    # Replace port placeholder if present
    if port:
        cmd = [c.format(port=port) if isinstance(c, str) and "{port}" in c else c for c in cmd]
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["DISPLAY"] = ":1"  # For GUI applications
    
    # Log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Log file
    log_file = log_dir / f"{service}.log"
    
    # Start the process
    try:
        logger.info(f"Starting {service} on port {port}...")
        
        # Open log file
        with open(log_file, "a") as log:
            # Start the process
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Wait a bit to see if it starts
            time.sleep(2)
            
            # Check if it's still running
            if process.poll() is not None:
                logger.error(f"Service {service} exited immediately with code {process.returncode}")
                with open(log_file, "r") as f:
                    logger.error(f"Last 10 lines of log:")
                    lines = f.readlines()
                    for line in lines[-10:]:
                        logger.error(line.strip())
                return None
            
            logger.info(f"Service {service} started successfully (PID: {process.pid})")
            return process
            
    except Exception as e:
        logger.error(f"Error starting {service}: {str(e)}")
        return None

def stop_service(service: str):
    """
    Stop a running service.
    
    Args:
        service: Name of the service to stop
    """
    if service in processes and processes[service]:
        logger.info(f"Stopping {service}...")
        
        # Get the process
        process = processes[service]
        
        # Send SIGTERM
        try:
            process.terminate()
            
            # Wait for it to exit
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it didn't exit, force kill
                logger.warning(f"{service} didn't exit gracefully, forcing...")
                process.kill()
            
            logger.info(f"{service} stopped")
            
        except Exception as e:
            logger.error(f"Error stopping {service}: {str(e)}")
        
        # Remove from processes
        processes[service] = None

def stop_all_services():
    """Stop all running services."""
    for service in list(processes.keys()):
        stop_service(service)

def signal_handler(sig, frame):
    """Handle signals to gracefully stop all services."""
    logger.info("Received shutdown signal, stopping all services...")
    stop_all_services()
    sys.exit(0)

def main():
    """Main function to start the dashboard and required services."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Start Communication Dashboard and services")
    
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=DEFAULT_PORTS["mcp_server"],
        help=f"Port for MCP server (default: {DEFAULT_PORTS['mcp_server']})"
    )
    
    parser.add_argument(
        "--webhook-port",
        type=int,
        default=DEFAULT_PORTS["webhook"],
        help=f"Port for webhook server (default: {DEFAULT_PORTS['webhook']})"
    )
    
    parser.add_argument(
        "--demo-port",
        type=int,
        default=DEFAULT_PORTS["demo_server"],
        help=f"Port for demo server (default: {DEFAULT_PORTS['demo_server']})"
    )
    
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=DEFAULT_PORTS["dashboard"],
        help=f"Port for Streamlit dashboard (default: {DEFAULT_PORTS['dashboard']})"
    )
    
    parser.add_argument(
        "--skip-services",
        action="store_true",
        help="Skip starting backend services (MCP, webhook, demo)"
    )
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start backend services if not skipped
        if not args.skip_services:
            # Start MCP server
            processes["mcp_server"] = start_service("mcp_server", args.mcp_port)
            
            # Start webhook server
            processes["webhook"] = start_service("webhook", args.webhook_port)
            
            # Start demo server
            processes["demo_server"] = start_service("demo_server", args.demo_port)
            
            # Give services time to initialize
            logger.info("Giving services time to initialize...")
            time.sleep(5)
        
        # Always start the dashboard
        processes["dashboard"] = start_service("dashboard", args.dashboard_port)
        
        # Keep running until interrupted
        logger.info("All services started. Press Ctrl+C to stop.")
        
        # Wait for dashboard to exit
        if processes["dashboard"]:
            processes["dashboard"].wait()
        
        # Stop all services when dashboard exits
        stop_all_services()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping all services...")
        stop_all_services()
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        stop_all_services()

if __name__ == "__main__":
    main()