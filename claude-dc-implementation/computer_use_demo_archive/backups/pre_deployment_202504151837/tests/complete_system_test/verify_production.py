"""Production verification script"""
import sys
import os
import traceback

def verify_production():
    """Verify that the production environment is working correctly"""
    # Test importing all modules
    print("Testing imports...")
    try:
        from tool_intercept import initialize_interception
        # Call the function for good measure
        initialize_interception()
        print("✅ tool_intercept module imports successfully")
        
        from safe_ops import safe_cat, safe_ls, safe_file_info
        print("u2705 safe_ops module imports successfully")
        
        from token_management.token_manager import token_manager
        print("u2705 token_management module imports successfully")
        
        from streaming.streaming_client import StreamingClient
        print("u2705 streaming module imports successfully")
        
        # Test a simple file operation
        print("\nTesting file operation...")
        readme_path = '/home/computeruse/computer_use_demo/README.md'
        if not os.path.exists(readme_path):
            print(f"u274c Test file {readme_path} does not exist, using a different file...")
            # Try to find an existing file
            readme_path = '/etc/hosts'
            
        info = safe_file_info(readme_path)
        print(f"File info retrieved: {info}")
        
        # Test token manager
        stats = token_manager.get_stats()
        print("\nToken manager stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nu2705 PRODUCTION ENVIRONMENT VERIFIED SUCCESSFULLY!")
        return True
    except Exception as e:
        print(f"\nu274c VERIFICATION FAILURE: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_production()