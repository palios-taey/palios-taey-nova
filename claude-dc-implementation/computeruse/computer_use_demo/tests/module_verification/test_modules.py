"""Test script to verify existing module functionality"""
import sys
import os

# Add the computer_use_demo directory to the path
sys.path.append('/home/computeruse/computer_use_demo')

def test_safe_ops():
    """Test the safe_ops module"""
    try:
        from safe_ops import safe_cat, safe_ls, safe_file_info
        print("✅ safe_ops module imports successfully")
        
        # Test basic functionality
        result = safe_file_info('/home/computeruse/computer_use_demo/README.md')
        print(f"safe_file_info result: {result}")
        
        return True
    except Exception as e:
        print(f"❌ safe_ops module test failed: {e}")
        return False

def test_token_management():
    """Test the token_management module"""
    try:
        from token_management.token_manager import token_manager
        print("✅ token_management module imports successfully")
        
        # Test basic functionality
        stats = token_manager.get_stats()
        print(f"Token manager stats: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ token_management module test failed: {e}")
        return False

def test_streaming():
    """Test the streaming module"""
    try:
        from streaming.streaming_client import StreamingClient
        print("✅ streaming module imports successfully")
        
        # Just test import, don't actually create a client
        return True
    except Exception as e:
        print(f"❌ streaming module test failed: {e}")
        return False

def run_all_tests():
    """Run all module tests"""
    test_results = {
        "safe_ops": test_safe_ops(),
        "token_management": test_token_management(),
        "streaming": test_streaming()
    }
    
    print("\n=== Module Test Results ===")
    for module, result in test_results.items():
        print(f"{module}: {'✅ PASS' if result else '❌ FAIL'}")
    
    all_passed = all(test_results.values())
    print(f"\nOverall: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")

if __name__ == "__main__":
    print("Starting module verification tests...")
    run_all_tests()