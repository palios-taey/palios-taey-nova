"""
Direct test for streaming file operations.
"""

import os
import asyncio
import tempfile
from pathlib import Path

# Import the streaming file tool directly
from tools.dc_file import dc_file_view_streaming

async def main():
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("Line 1: Test content\n")
        test_file.write("Line 2: More test content\n")
        test_file.write("Line 3: Final test content\n")
        test_path = test_file.name
    
    try:
        print(f"Testing file view streaming on {test_path}")
        
        # Progress tracking
        async def progress_callback(message, progress):
            print(f"Progress: {message} - {progress:.0%}")
        
        # Collect output
        print("\nReceiving chunks:")
        async for chunk in dc_file_view_streaming(test_path, progress_callback=progress_callback):
            print(f"CHUNK: {chunk!r}")
        
        print("\nTest completed")
    finally:
        # Clean up the test file
        try:
            os.unlink(test_path)
            print(f"Deleted test file: {test_path}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())