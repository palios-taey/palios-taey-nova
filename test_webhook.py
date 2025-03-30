import requests
import hmac
import hashlib
import json
import sys

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhook"
SECRET_KEY = "user-family-community-society"  # This should match the one in webhook_server.py

def test_status_check():
    """Test the status check endpoint"""
    operation = {
        "operation": "status_check",
        "check_type": "all"
    }
    
    response = call_webhook(operation)
    print("Status Check Test:")
    print(json.dumps(response, indent=2))
    print("\n")
    return response["status"] == "success"

def test_file_transfer():
    """Test the file transfer endpoint"""
    operation = {
        "operation": "file_transfer",
        "transfer_type": "content",
        "destination": "test/webhook_test.txt",
        "content": "This is a test file created by the webhook test script.\nIf you can see this, the webhook is working correctly!"
    }
    
    response = call_webhook(operation)
    print("File Transfer Test:")
    print(json.dumps(response, indent=2))
    print("\n")
    return response["status"] == "success"

def test_db_access():
    """Test database access"""
    operation = {
        "operation": "modify_db",
        "sql": [
            "SELECT count(*) FROM sqlite_master WHERE type='table'"
        ]
    }
    
    response = call_webhook(operation)
    print("Database Access Test:")
    print(json.dumps(response, indent=2))
    print("\n")
    return response["status"] == "success"

def call_webhook(operation_data):
    """Call the webhook with appropriate authentication"""
    payload = json.dumps(operation_data)
    
    # Generate signature
    signature = hmac.new(
        SECRET_KEY.encode(), 
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Send request
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Claude-Signature': signature
            }
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the webhook server. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Testing webhook server...")
    print("-------------------------\n")
    
    # Create test directory if needed
    import os
    os.makedirs(os.path.join(os.path.expanduser("~/projects/palios-taey-nova"), "test"), exist_ok=True)
    
    # Run tests
    status_test = test_status_check()
    file_test = test_file_transfer()
    db_test = test_db_access()
    
    # Print summary
    print("Test Summary:")
    print(f"Status Check: {'PASS' if status_test else 'FAIL'}")
    print(f"File Transfer: {'PASS' if file_test else 'FAIL'}")
    print(f"Database Access: {'PASS' if db_test else 'FAIL'}")
    
    if status_test and file_test and db_test:
        print("\nAll tests PASSED! The webhook server is configured correctly.")
    else:
        print("\nSome tests FAILED. Please check the webhook server configuration.")
