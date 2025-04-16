"""Simple verification script for the production environment"""
import sys
import os

def verify_modules():
    """Simply verify that modules can be imported"""
    try:
        # Try to import safe_ops module
        from safe_ops import safe_cat, safe_ls, safe_file_info
        print("✅ Successfully imported safe_ops with safe_cat, safe_ls and safe_file_info")
        
        # Try to import token_management module
        from token_management.token_manager import token_manager
        print("✅ Successfully imported token_manager")
        
        # Try to import streaming module
        from streaming.streaming_client import StreamingClient
        print("✅ Successfully imported StreamingClient")
        
        print("\n✅ All modules successfully imported!")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_modules()