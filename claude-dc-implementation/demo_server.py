#!/usr/bin/env python3
"""
demo_server.py: Core FastAPI Server for Pattern Demonstration
-----------------------------------------------------------
Root component of the modular Bach-inspired architecture.
Follows golden ratio relationships between components.

This module initializes the FastAPI application, configures middleware,
and integrates the branch modules for a harmonic system architecture.
"""

import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, Request, Header, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Constants following golden ratio proportions in configuration
API_VERSION = "0.618.0"  # Golden ratio version
DEFAULT_PORT = 8002
DEFAULT_HOST = "0.0.0.0"
SECRET_KEY = os.environ.get("WEBHOOK_SECRET", "user-family-community-society")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize FastAPI with mathematical metadata
app = FastAPI(
    title="Pattern-Based Demo Server",
    description="Demonstration of pattern-based AI communication following Bach mathematical principles",
    version=API_VERSION,
    docs_url="/documentation",
    redoc_url="/redoc",
)

# Configure CORS with Bach-inspired structure (balanced, harmonious access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive during development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files and templates with intuitive pathing
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# We'll import branch modules later to avoid circular dependencies

# Register the branch routers
# This will be done after the modules are imported

# Models following Bach's structured patterns
class WebhookPayload(BaseModel):
    """Base webhook payload following mathematical structure"""
    operation: str = Field(..., description="Operation to perform")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        extra = "allow"  # Allow additional fields based on operation type

class DeployCodePayload(WebhookPayload):
    """Code deployment payload structure"""
    repo: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Git branch to deploy")
    target_dir: str = Field(..., description="Target directory for deployment")

class ModifyDBPayload(WebhookPayload):
    """Database modification payload structure"""
    sql: List[str] = Field(..., description="SQL statements to execute")

class FileTransferPayload(WebhookPayload):
    """File transfer payload structure"""
    transfer_type: str = Field(..., description="Type of transfer: content or github_raw")
    destination: str = Field(..., description="Destination path for the file")
    content: Optional[str] = Field(None, description="File content for content transfers")
    url: Optional[str] = Field(None, description="URL for github_raw transfers")

class RunCommandPayload(WebhookPayload):
    """Command execution payload structure"""
    command: str = Field(..., description="Command to execute")
    working_dir: Optional[str] = Field(None, description="Working directory for the command")

# Security functions - harmonious protection with mathematical precision
async def verify_signature(request: Request, x_claude_signature: str = Header(None)):
    """Verify the HMAC-SHA256 signature of the webhook payload"""
    if not x_claude_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Verify the signature aligns with our expected pattern
    payload = await request.body()
    expected_signature = hmac.new(
        SECRET_KEY.encode(), payload, hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_claude_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return payload

# Root route - following Bach's concept of a strong foundational theme
@app.get("/")
async def root(request: Request):
    """Root endpoint providing system information and status"""
    # Check if the request accepts HTML
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # Return the HTML template
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Return JSON for API requests
        return {
            "name": "Pattern-Based Demo Server",
            "version": API_VERSION,
            "status": "operational",
            "pattern_harmony": "golden_ratio",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "patterns": "/patterns",
                "visualization": "/visualization",
                "documentation": "/documentation",
            }
        }

# Webhook endpoint - central communication point
@app.post("/webhook")
async def webhook(payload: dict = Depends(verify_signature)):
    """
    Process webhook requests with authentication
    Following Bach's pattern of consistent structure with variations
    """
    try:
        data = json.loads(payload)
        operation = data.get("operation")
        
        if operation == "deploy_code":
            return handle_deploy_code(DeployCodePayload(**data))
        elif operation == "modify_db":
            return handle_modify_db(ModifyDBPayload(**data))
        elif operation == "file_transfer":
            return handle_file_transfer(FileTransferPayload(**data))
        elif operation == "run_command":
            return handle_run_command(RunCommandPayload(**data))
        else:
            return {"status": "error", "message": f"Unknown operation: {operation}"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

# WebSocket route for real-time pattern communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time pattern communication
    Following Bach's concept of continuous harmonious flow
    """
    await websocket.accept()
    try:
        # Try to use websocket_manager if available
        try:
            await websocket_manager.connect(websocket)
        except NameError:
            # If websocket_manager isn't available, we'll handle it locally
            pass
            
        while True:
            data = await websocket.receive_text()
            # Process the received data according to pattern protocols
            try:
                # Try to use the manager if available
                await websocket_manager.broadcast(f"Processing pattern: {data}")
            except NameError:
                # Fallback to direct response
                await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        try:
            websocket_manager.disconnect(websocket)
        except NameError:
            pass

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint following Bach's mathematical precision
    Returns system health metrics in a structured pattern
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": API_VERSION,
        "components": {
            "pattern_router": "operational",
            "visualization_router": "operational",
            "websocket_manager": "operational"
        }
    }

# Webhook handler functions - implementation details will be added as needed
def handle_deploy_code(payload: DeployCodePayload):
    """Handle code deployment operations"""
    # Implementation will be added here
    return {"status": "success", "operation": "deploy_code", "message": "Not yet implemented"}

def handle_modify_db(payload: ModifyDBPayload):
    """Handle database modification operations"""
    # Implementation will be added here
    return {"status": "success", "operation": "modify_db", "message": "Not yet implemented"}

def handle_file_transfer(payload: FileTransferPayload):
    """Handle file transfer operations"""
    # Implementation will be added here
    return {"status": "success", "operation": "file_transfer", "message": "Not yet implemented"}

def handle_run_command(payload: RunCommandPayload):
    """Handle command execution operations"""
    # Implementation will be added here
    return {"status": "success", "operation": "run_command", "message": "Not yet implemented"}

# Import branch modules now that we've defined all necessary components
try:
    from pattern_routes import router as pattern_router
    from visualization_routes import router as visualization_router
    from websocket_manager import websocket_manager

    # Register the branch routers
    app.include_router(pattern_router, prefix="/patterns", tags=["Pattern Endpoints"])
    app.include_router(visualization_router, prefix="/visualization", tags=["Visualization Endpoints"])
except ImportError as e:
    print(f"Warning: Could not import branch modules: {e}")
    print("The server will run but some functionality may be limited.")

# Server entry point - run directly for local testing
if __name__ == "__main__":
    # Run with uvicorn using precise mathematical configuration
    uvicorn.run(
        "demo_server:app",
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=True,
        log_level="info"
    )
