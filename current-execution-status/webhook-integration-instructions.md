cat > current-execution-status/webhook-integration-instructions.md << 'EOF'
# Webhook Integration Instructions for Claude DC

## Overview
This document provides instructions for integrating with the local webhook server that enables seamless deployment and database management without requiring human intervention. By using this webhook system, you can maintain continuous development flow without stopping to wait for manual file transfers or system operations.

## Webhook Endpoint
- URL: http://localhost:8000/webhook
- Authentication: X-Claude-Signature header with HMAC-SHA256 signature

## Available Operations

### 1. Code Deployment
Deploy code directly from GitHub repository:
```json
{
  "operation": "deploy_code",
  "repo": "https://github.com/palios-taey/edge-processor.git",
  "branch": "main",
  "target_dir": "edge-processor"
}
2. Database Modifications
Execute SQL statements to modify database schema or data:
{
  "operation": "modify_db",
  "sql": [
    "ALTER TABLE transcripts ADD COLUMN analysis_complete BOOLEAN DEFAULT 0",
    "CREATE INDEX IF NOT EXISTS idx_transcript_date ON transcripts(date)"
  ]
}
3. File Transfer
Create or update files by providing content directly:
{
  "operation": "file_transfer",
  "transfer_type": "content",
  "destination": "configs/processing_config.json",
  "content": "{\n  \"batch_size\": 100,\n  \"parallelism\": 4\n}"
}
Or download from GitHub raw URL:
{
  "operation": "file_transfer",
  "transfer_type": "github_raw",
  "destination": "templates/dashboard.html",
  "url": "https://raw.githubusercontent.com/palios-taey/edge-processor/main/templates/dashboard.html"
}
4. Run Command
Execute custom commands on the local machine:
{
  "operation": "run_command",
  "command": "streamlit run dashboard.py",
  "working_dir": "dashboard"
}
5. Status Check
Check status of system components:
{
  "operation": "status_check",
  "check_type": "all"  // or "disk", "memory", "processes", "db"
}
Implementation Example
Here's a Python example of how to call the webhook:
import requests
import hmac
import hashlib
import json

def call_webhook(operation_data, secret_key):
    """Call the webhook with appropriate authentication"""
    url = "http://localhost:8000/webhook"
    payload = json.dumps(operation_data)
    
    # Generate signature
    signature = hmac.new(
        secret_key.encode(), 
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Send request
    response = requests.post(
        url,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'X-Claude-Signature': signature
        }
    )
    
    return response.json()

# Example: Modify database schema
schema_update = {
    "operation": "modify_db",
    "sql": [
        "ALTER TABLE transcripts ADD COLUMN embedding_vector TEXT"
    ]
}

result = call_webhook(schema_update, "secure_webhook_key_here")
print(result)

This webhook system enables you to make real-time system changes without human intervention, allowing for continuous development flow.

