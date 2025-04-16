"""
Test script for Safe File Operations
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the safe file operations
from test_rate_protection import safe_cat, safe_ls, safe_file_info

def test_safe_ls():
    """Test listing a directory safely"""
    print("Testing safe_ls...")
    result = safe_ls("/home/computeruse/computer_use_demo")
    print(f"Found {len(result.split('\n'))} items")
    print("safe_ls test complete")

def test_safe_file_info():
    """Test getting file information safely"""
    print("Testing safe_file_info...")
    # Try with a medium-sized file
    result = safe_file_info("/home/computeruse/computer_use_demo/loop.py")
    print(result)
    print("safe_file_info test complete")

def test_safe_cat():
    """Test reading a file safely"""
    print("Testing safe_cat with a small file...")
    # Test with a small file first
    content = safe_cat("/home/computeruse/computer_use_demo/README.md")
    print(f"Read {len(content)} characters")
    
    print("Testing safe_cat with a large file...")
    # Test with a larger file to trigger chunking
    large_file = "/home/computeruse/computer_use_demo/loop.py"
    content = safe_cat(large_file)
    print(f"Read {len(content)} characters from {large_file}")
    print("safe_cat test complete")

if __name__ == "__main__":
    print("Starting Safe File Operations tests...")
    test_safe_ls()
    test_safe_file_info()
    test_safe_cat()
    print("All tests completed successfully")
