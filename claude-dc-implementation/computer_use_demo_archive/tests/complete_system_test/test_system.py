"""Comprehensive system test for the complete environment"""
import os
import sys
import time
import traceback

# Set up the path to use our test environment
os.environ["PYTHONPATH"] = "/home/computeruse/computer_use_demo/tests/complete_system_test"
sys.path.insert(0, "/home/computeruse/computer_use_demo/tests/complete_system_test")

# Test imports - these should all work without errors
def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")
    
    try:
        # Test tool intercept
        from tool_intercept import initialize_interception
        # Call the function for good measure
        initialize_interception()
        print("✅ tool_intercept module imports successfully")
        
        # Test safe_ops
        from safe_ops import safe_cat, safe_ls, safe_file_info
        print("✅ safe_ops module imports successfully")
        
        # Test token_management
        from token_management.token_manager import token_manager
        print("✅ token_management module imports successfully")
        
        # Test streaming
        from streaming.streaming_client import StreamingClient
        print("✅ streaming module imports successfully")
        
        # Test loop and streamlit (just import, don't run)
        import loop
        print("✅ loop module imports successfully")
        import streamlit
        print("✅ streamlit module imports successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

# Test file operations
def test_file_operations():
    """Test file operations with intercept protection"""
    print("\nTesting file operations...")
    
    try:
        # Test direct file access (should be intercepted)
        readme_path = '/home/computeruse/computer_use_demo/README.md'
        if not os.path.exists(readme_path):
            print(f"❌ Test file {readme_path} does not exist, using a different file...")
            # Try to find an existing file
            readme_path = '/etc/hosts'
        
        with open(readme_path, 'r') as f:
            content = f.read()
            print(f"Read {len(content)} characters with open()")
        
        # Test safe_ops functions
        from safe_ops import safe_cat, safe_ls, safe_file_info
        
        # Test safe_file_info
        info = safe_file_info(readme_path)
        print(f"File info retrieved: {info}")
        
        # Test safe_ls
        directory = os.path.dirname(readme_path)
        listing = safe_ls(directory)
        print(f"Directory listing retrieved: {len(listing)} items")
        
        # Test safe_cat
        content = safe_cat(readme_path)
        print(f"File content retrieved: {len(content)} characters")
        
        return True
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        traceback.print_exc()
        return False

# Test token manager
def test_token_manager():
    """Test token manager functionality"""
    print("\nTesting token manager...")
    
    try:
        from token_management.token_manager import token_manager
        
        # Get initial stats
        initial_stats = token_manager.get_stats()
        print("Initial token manager stats:")
        for key, value in initial_stats.items():
            print(f"  {key}: {value}")
        
        # Simulate some token usage
        token_manager.track_tokens(1000, 500)
        
        # Get updated stats
        updated_stats = token_manager.get_stats()
        print("\nUpdated token manager stats after tracking tokens:")
        for key, value in updated_stats.items():
            print(f"  {key}: {value}")
        
        # Test delay function (with minimal delay)
        print("\nTesting delay function with small token count...")
        start_time = time.time()
        token_manager.delay_if_needed(100, 50)
        end_time = time.time()
        print(f"Delay took {end_time - start_time:.4f} seconds")
        
        return True
    except Exception as e:
        print(f"❌ Token manager test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    results = {}
    
    # Run import tests
    results['imports'] = test_imports()
    
    # If imports pass, run the rest of the tests
    if results['imports']:
        results['file_operations'] = test_file_operations()
        results['token_manager'] = test_token_manager()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASS' if result else '❌ FAIL'}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    print("Running comprehensive system test...")
    run_all_tests()