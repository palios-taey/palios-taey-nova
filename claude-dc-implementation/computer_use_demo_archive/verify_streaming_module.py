"""
Verify the streaming module without changing any production files
"""
import sys
import os

# Add computer_use_demo to path
sys.path.append('/home/computeruse/computer_use_demo')

def verify_streaming_module():
    """Verify the streaming module can be imported and initialized"""
    try:
        print("Importing StreamingClient...")
        from streaming.streaming_client import StreamingClient
        print("u2705 StreamingClient imported successfully")
        
        print("\nImporting TokenManager...")
        from token_management.token_manager import token_manager
        print("u2705 TokenManager imported successfully")
        
        print("\nInitializing StreamingClient...")
        client = StreamingClient()
        print(f"u2705 StreamingClient initialized: {client}")
        
        print("\nChecking StreamingClient attributes:")
        methods = [attr for attr in dir(client) if not attr.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        return True
    except Exception as e:
        print(f"u274c Error verifying streaming module: {e}")
        return False

if __name__ == "__main__":
    print("Verifying streaming module...")
    success = verify_streaming_module()
    if success:
        print("\nu2705 Streaming module verification SUCCESSFUL")
    else:
        print("\nu274c Streaming module verification FAILED")