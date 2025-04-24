"""
Simple test script for streaming file operations.
"""

import os
import asyncio
import tempfile
from pathlib import Path

# Import the streaming file tool
from tools.dc_file import dc_execute_file_tool_streaming

async def test_file_view():
    """Test streaming view operation on a file."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("Line 1: Test content\n")
        test_file.write("Line 2: More test content\n")
        test_file.write("Line 3: Final test content\n")
        test_path = test_file.name
    
    try:
        print(f"Testing view operation on {test_path}")
        print("-" * 50)
        
        # Progress tracking
        async def progress_callback(message, progress):
            print(f"Progress: {message} - {progress:.0%}")
        
        # Collect output
        output = []
        async for chunk in dc_execute_file_tool_streaming(
            {"command": "view", "path": test_path},
            progress_callback=progress_callback
        ):
            print(f"CHUNK: {chunk!r}")
            output.append(chunk)
        
        print("\n\nOutput collected:")
        
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
            print(f"Deleted test file: {test_path}")
        except:
            pass

async def test_file_create():
    """Test streaming create operation."""
    # Define a temporary file path
    test_path = tempfile.gettempdir() + "/streaming_create_test.txt"
    
    try:
        # Make sure file doesn't exist
        if os.path.exists(test_path):
            os.unlink(test_path)
        
        print(f"Testing create operation on {test_path}")
        print("-" * 50)
        
        # Progress tracking
        async def progress_callback(message, progress):
            print(f"Progress: {message} - {progress:.0%}")
        
        # Test content
        test_content = "This is line 1\nThis is line 2\nThis is line 3\n"
        
        # Execute the command
        async for chunk in dc_execute_file_tool_streaming(
            {"command": "create", "path": test_path, "file_text": test_content},
            progress_callback=progress_callback
        ):
            print(chunk, end="", flush=True)
        
        print("\n\nVerifying file was created...")
        if os.path.exists(test_path):
            with open(test_path, "r") as f:
                content = f.read()
                print(f"File content ({len(content)} bytes):\n{content}")
        else:
            print("Error: File was not created!")
    
    finally:
        # Clean up the test file
        try:
            if os.path.exists(test_path):
                os.unlink(test_path)
                print(f"Deleted test file: {test_path}")
        except:
            pass

async def main():
    print("\n=== Testing File View Operation ===\n")
    await test_file_view()
    
    print("\n=== Testing File Create Operation ===\n")
    await test_file_create()

if __name__ == "__main__":
    asyncio.run(main())