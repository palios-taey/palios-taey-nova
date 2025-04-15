"""Simple test script for the complete system"""
import os
import sys

# Add the test environment to the path
sys.path.insert(0, "/home/computeruse/computer_use_demo/tests/complete_system_test")

# Check if critical files exist
def check_files():
    print("Checking critical files...")
    
    files = [
        "/home/computeruse/computer_use_demo/tests/complete_system_test/loop.py",
        "/home/computeruse/computer_use_demo/tests/complete_system_test/streamlit.py",
        "/home/computeruse/computer_use_demo/tests/complete_system_test/safe_ops/__init__.py",
        "/home/computeruse/computer_use_demo/tests/complete_system_test/token_management/token_manager.py",
        "/home/computeruse/computer_use_demo/tests/complete_system_test/streaming/streaming_client.py",
        "/home/computeruse/computer_use_demo/tests/complete_system_test/tool_intercept/__init__.py"
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"u2705 {file} exists")
        else:
            print(f"u274c {file} does not exist")
            all_exist = False
    
    return all_exist

# Check if we can import critical modules
def test_imports():
    print("\nTesting imports...")
    
    success = True
    try:
        from safe_ops import safe_cat, safe_ls, safe_file_info
        print("u2705 safe_ops module imports successfully")
    except Exception as e:
        print(f"u274c safe_ops module import failed: {e}")
        success = False
    
    try:
        from token_management.token_manager import token_manager
        print("u2705 token_management module imports successfully")
    except Exception as e:
        print(f"u274c token_management module import failed: {e}")
        success = False
    
    try:
        from streaming.streaming_client import StreamingClient
        print("u2705 streaming module imports successfully")
    except Exception as e:
        print(f"u274c streaming module import failed: {e}")
        success = False
    
    try:
        from tool_intercept import initialize_interception
        print("u2705 tool_intercept module imports successfully")
    except Exception as e:
        print(f"u274c tool_intercept module import failed: {e}")
        success = False
    
    return success

# Run checks
def run_tests():
    print("Running simple system tests...")
    files_ok = check_files()
    imports_ok = test_imports()
    
    print("\n=== Test Summary ===")
    print(f"Files check: {'u2705 PASS' if files_ok else 'u274c FAIL'}")
    print(f"Imports check: {'u2705 PASS' if imports_ok else 'u274c FAIL'}")
    
    all_passed = files_ok and imports_ok
    print(f"\nOverall: {'u2705 ALL TESTS PASSED!' if all_passed else 'u274c SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    run_tests()