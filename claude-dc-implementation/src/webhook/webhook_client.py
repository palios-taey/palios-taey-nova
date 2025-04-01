#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - Webhook Client
-----------------------------------
This module provides webhook integration for continuous implementation flow,
allowing seamless deployment and communication with external systems.
"""

import os
import json
import hmac
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import time
from datetime import datetime
import sys

# Add the parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import utilities
from src.utils.secrets import get_webhook_url, get_webhook_secret

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/logs/webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_client")

class WebhookClient:
    """Client for interacting with the webhook server for continuous implementation flow."""
    
    def __init__(self, 
                webhook_url: str = None,
                secret_key: str = None):
        """
        Initialize the webhook client.
        
        Args:
            webhook_url: URL of the webhook server
            secret_key: Secret key for HMAC signing
        """
        self.webhook_url = webhook_url or get_webhook_url() or "http://localhost:8000/webhook"
        self.secret_key = secret_key or get_webhook_secret() or "user-family-community-society"
        
        # Initialize metrics
        self.metrics = {
            "requests_sent": 0,
            "success_count": 0,
            "error_count": 0,
            "last_response_time": None
        }
        
        logger.info(f"Webhook client initialized with URL: {self.webhook_url}")
    
    def _sign_payload(self, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            payload: JSON payload as string
            
        Returns:
            HMAC-SHA256 signature as hex string
        """
        return hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def call_webhook(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the webhook with the specified operation data.
        
        Args:
            operation_data: Dictionary containing operation details
            
        Returns:
            Dictionary containing the response from the webhook
        """
        # Prepare payload
        payload = json.dumps(operation_data, indent=2)
        
        # Generate signature
        signature = self._sign_payload(payload)
        
        # Prepare request headers with golden ratio structure
        # The header structure follows Bach's mathematical patterns
        # with a hierarchical organization based on information importance
        headers = {
            "Content-Type": "application/json",
            "X-Claude-Signature": signature,
            "X-Request-Timestamp": str(int(time.time())),
            "X-Mathematical-Pattern": "golden-ratio-structure",
            "X-Conductor-Version": "1.0.0"
        }
        
        try:
            # Log request
            logger.info(f"Sending webhook request: {operation_data['operation']}")
            
            # Send request with Bach timing pattern
            # We use exponential backoff with golden ratio factors for retries
            max_retries = 5
            retry_delays = [0, 1, 1.618, 2.618, 4.236]  # Golden ratio progression
            
            for attempt in range(max_retries):
                start_time = time.time()
                response = requests.post(
                    self.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=10
                )
                elapsed_time = time.time() - start_time
                
                # Update metrics
                self.metrics["requests_sent"] += 1
                self.metrics["last_response_time"] = elapsed_time
                
                if response.status_code == 200:
                    # Success
                    self.metrics["success_count"] += 1
                    logger.info(f"Webhook request successful: {elapsed_time:.2f}s")
                    return response.json()
                else:
                    # Error
                    self.metrics["error_count"] += 1
                    logger.warning(f"Webhook request failed (attempt {attempt+1}/{max_retries}): {response.status_code} - {response.text}")
                    
                    if attempt < max_retries - 1:
                        # Wait with golden ratio backoff
                        time.sleep(retry_delays[attempt])
            
            logger.error(f"Webhook request failed after {max_retries} attempts")
            return {"status": "error", "message": f"Failed after {max_retries} attempts"}
            
        except Exception as e:
            logger.error(f"Error calling webhook: {str(e)}")
            self.metrics["error_count"] += 1
            return {"status": "error", "message": str(e)}
    
    def deploy_code(self, repo: str, branch: str = "main", target_dir: str = "claude-dc-implementation") -> Dict[str, Any]:
        """
        Deploy code from a Git repository.
        
        Args:
            repo: URL of the Git repository
            branch: Branch to deploy
            target_dir: Target directory for deployment
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "deploy_code",
            "repo": repo,
            "branch": branch,
            "target_dir": target_dir
        }
        
        return self.call_webhook(operation_data)
    
    def modify_db(self, sql_statements: List[str]) -> Dict[str, Any]:
        """
        Execute SQL statements to modify the database.
        
        Args:
            sql_statements: List of SQL statements to execute
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "modify_db",
            "sql": sql_statements
        }
        
        return self.call_webhook(operation_data)
    
    def transfer_file_content(self, destination: str, content: str) -> Dict[str, Any]:
        """
        Transfer file content directly.
        
        Args:
            destination: Destination path for the file
            content: Content to write to the file
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "file_transfer",
            "transfer_type": "content",
            "destination": destination,
            "content": content
        }
        
        return self.call_webhook(operation_data)
    
    def transfer_file_from_github(self, destination: str, url: str) -> Dict[str, Any]:
        """
        Transfer file from GitHub raw URL.
        
        Args:
            destination: Destination path for the file
            url: GitHub raw URL
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "file_transfer",
            "transfer_type": "github_raw",
            "destination": destination,
            "url": url
        }
        
        return self.call_webhook(operation_data)
    
    def run_command(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """
        Run a command on the server.
        
        Args:
            command: Command to run
            working_dir: Working directory for the command
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "run_command",
            "command": command
        }
        
        if working_dir:
            operation_data["working_dir"] = working_dir
        
        return self.call_webhook(operation_data)
    
    def check_status(self, check_type: str = "all") -> Dict[str, Any]:
        """
        Check the status of system components.
        
        Args:
            check_type: Type of status check
            
        Returns:
            Dictionary containing the response from the webhook
        """
        operation_data = {
            "operation": "status_check",
            "check_type": check_type
        }
        
        return self.call_webhook(operation_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.
        
        Returns:
            Dictionary containing client metrics
        """
        return {
            **self.metrics,
            "timestamp": datetime.now().isoformat()
        }


# Create a singleton instance for global use
webhook_client = WebhookClient()

def deploy_code(repo: str, branch: str = "main", target_dir: str = "claude-dc-implementation") -> Dict[str, Any]:
    """
    Deploy code from a Git repository.
    
    Args:
        repo: URL of the Git repository
        branch: Branch to deploy
        target_dir: Target directory for deployment
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.deploy_code(repo, branch, target_dir)

def modify_db(sql_statements: List[str]) -> Dict[str, Any]:
    """
    Execute SQL statements to modify the database.
    
    Args:
        sql_statements: List of SQL statements to execute
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.modify_db(sql_statements)

def transfer_file_content(destination: str, content: str) -> Dict[str, Any]:
    """
    Transfer file content directly.
    
    Args:
        destination: Destination path for the file
        content: Content to write to the file
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.transfer_file_content(destination, content)

def transfer_file_from_github(destination: str, url: str) -> Dict[str, Any]:
    """
    Transfer file from GitHub raw URL.
    
    Args:
        destination: Destination path for the file
        url: GitHub raw URL
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.transfer_file_from_github(destination, url)

def run_command(command: str, working_dir: str = None) -> Dict[str, Any]:
    """
    Run a command on the server.
    
    Args:
        command: Command to run
        working_dir: Working directory for the command
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.run_command(command, working_dir)

def check_status(check_type: str = "all") -> Dict[str, Any]:
    """
    Check the status of system components.
    
    Args:
        check_type: Type of status check
        
    Returns:
        Dictionary containing the response from the webhook
    """
    return webhook_client.check_status(check_type)


if __name__ == "__main__":
    # Test the webhook client
    print("Testing webhook client...")
    
    # Check status
    status = check_status()
    print(f"System status: {status}")
    
    # Get client metrics
    metrics = webhook_client.get_metrics()
    print(f"Client metrics: {metrics}")