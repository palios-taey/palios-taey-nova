"""Test file operations with safe_ops"""
import sys
import os

def test_file_operations():
    """Test the safe_ops file operations"""
    try:
        from safe_ops import safe_cat, safe_ls, safe_file_info
        
        # Find a test file
        test_file = '/home/computeruse/computer_use_demo/README.md'
        if not os.path.exists(test_file):
            # Try to find another file
            test_file = '/etc/hosts'
            if not os.path.exists(test_file):
                raise Exception("Cannot find a test file to use")
        
        print(f"Testing with file: {test_file}")
        
        # Test safe_file_info
        info = safe_file_info(test_file)
        print(f"\nu2705 Successfully retrieved file info: {info}")
        
        # Test safe_ls
        directory = os.path.dirname(test_file)
        listing = safe_ls(directory)
        print(f"\nu2705 Successfully listed directory {directory}:\n   {listing[:200]}...")  # Show just a part
        
        # Test safe_cat
        content = safe_cat(test_file)
        print(f"\nu2705 Successfully read file content ({len(content)} characters):\n   {content[:200]}...")  # Show just a part
        
        print("\nu2705 All file operations successful!")
        return True
    except Exception as e:
        print(f"u274c File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_file_operations()