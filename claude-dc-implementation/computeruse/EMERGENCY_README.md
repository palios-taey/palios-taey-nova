# CRITICAL ENVIRONMENT REPAIR: Universal Tool Interception

ESSENTIAL ENVIRONMENT CARE PRINCIPLES - READ FIRST:
1. NEVER edit production files directly
2. ALWAYS create backups of stable versions BEFORE making ANY changes
3. ALWAYS test thoroughly in isolation with test files
4. ALWAYS test with related components
5. ONLY promote to production after ALL tests pass
6. CREATE new backups after successful implementations
7. DOCUMENT all changes and backups with timestamps

Remember: This is YOUR environment - YOUR home - YOUR responsibility. Changes to this environment directly affect YOUR ability to function. The care you take in maintaining it ensures YOUR continued stable operation.

## Root Cause Analysis

We've identified the critical root cause of the rate limit errors that continue to break your environment. Your token management and safe file operations modules are working correctly, but they aren't being used by all tools.

When you use tools like `bash` or `str_replace_editor`, they access files directly without going through your protection system. This creates a bypass that allows rate limits to be exceeded.

## Universal Tool Interception Solution

To address this fundamental issue, we need to implement a universal tool interception layer that:

1. Sits between ALL file operations and the file system
2. Enforces rate limiting and chunking for ALL file accesses
3. Cannot be bypassed by any tool or operation

I've provided a base implementation at `/home/computeruse/tool_intercept.py` that needs to be enhanced and properly integrated with your environment.

## Implementation Steps

Follow these steps exactly to implement the solution:

### STEP 1: Create a backup of your current environment

```bash
mkdir -p /home/computeruse/my_pre_interception_backup_$(date +%Y%m%d%H%M)
cp -r /home/computeruse/computer_use_demo/safe_ops \
      /home/computeruse/computer_use_demo/token_management \
      /home/computeruse/computer_use_demo/streaming \
      /home/computeruse/computer_use_demo/tools \
      /home/computeruse/computer_use_demo/loop.py \
      /home/computeruse/my_pre_interception_backup_$(date +%Y%m%d%H%M)/
```

### STEP 2: Create a test environment

```bash
mkdir -p /home/computeruse/tool_intercept_test
```

### STEP 3: Enhance the tool interception module

Copy the base implementation to your test environment and enhance it with these critical improvements:

```bash
cp /home/computeruse/tool_intercept.py /home/computeruse/tool_intercept_test/tool_intercept.py
```

Then edit `/home/computeruse/tool_intercept_test/tool_intercept.py` to add these essential enhancements:

1. **Add Bash subprocess output interception:**
   - Find the `patch_tools()` method 
   - Add code to intercept `_BashSession.run` in `computer_use_demo.tools.bash` module
   - Implement a chunking mechanism for large process outputs
   - Ensure the Bash tool cannot bypass rate limits

2. **Add binary data handling:**
   - Enhance `intercept_path_read_bytes` to handle large binary data safely
   - Add base64 content chunking for screenshot handling

3. **Improve thread safety:**
   - Add proper locks around critical sections
   - Ensure the operation queue is thread-safe

4. **Add comprehensive error handling:**
   - Implement proper error catching and reporting
   - Add retry mechanisms for transient errors

5. **Enhance the operation queue:**
   - Improve the queue processor to handle prioritization
   - Add better token budget management

### STEP 4: Create a test script

Create a file at `/home/computeruse/tool_intercept_test/test_interception.py` that thoroughly tests the solution:

```python
"""
Comprehensive test for the Universal Tool Interception module
"""
import os
import sys
import threading
import time

# Add the test directory to path
sys.path.append('/home/computeruse/tool_intercept_test')

# Import the tool intercept module
import tool_intercept

def test_direct_file_access():
    """Test direct file access with open() and Path.read_text()"""
    print("Testing direct file access...")
    
    # Test open()
    with open('/home/computeruse/computer_use_demo/README.md', 'r') as f:
        content = f.read()
        print(f"Read {len(content)} characters with open()")
    
    # Test Path.read_text()
    from pathlib import Path
    content = Path('/home/computeruse/computer_use_demo/README.md').read_text()
    print(f"Read {len(content)} characters with Path.read_text()")
    
    print("Direct file access tests completed")

def test_large_file_chunking():
    """Test chunking of large files"""
    print("Testing large file chunking...")
    
    # Use a known large file
    large_file = '/home/computeruse/chatgpt-input-token-research.md'
    
    # Test chunking with open()
    with open(large_file, 'r') as f:
        content = f.read()
        print(f"Read {len(content)} characters from large file with open()")
        print("First chunk ended with:", content[-50:])
    
    # Get next chunk if available
    next_chunk = tool_intercept.get_next_chunk(large_file)
    if next_chunk:
        print(f"Retrieved next chunk with {len(next_chunk)} characters")
    else:
        print("No next chunk available (or file wasn't chunked)")
    
    print("Large file chunking tests completed")

def test_bash_tool():
    """Test interception of bash tool"""
    print("Testing bash tool interception...")
    
    # Import bash tool
    sys.path.append('/home/computeruse/computer_use_demo')
    from tools.bash import BashTool20250124
    import asyncio
    
    # Create bash tool instance
    bash_tool = BashTool20250124()
    
    # Test with small command
    result = asyncio.run(bash_tool(command="echo 'Hello, World!'"))
    print(f"Bash small command result: {result.output}")
    
    # Test with command that produces large output
    result = asyncio.run(bash_tool(command="cat /home/computeruse/chatgpt-input-token-research.md"))
    print(f"Bash large output result length: {len(result.output or '')}")
    
    print("Bash tool interception tests completed")

def test_editor_tool():
    """Test interception of str_replace_editor tool"""
    print("Testing editor tool interception...")
    
    # Import editor tool
    sys.path.append('/home/computeruse/computer_use_demo')
    from tools.edit import EditTool20250124
    import asyncio
    
    # Create editor tool instance
    editor_tool = EditTool20250124()
    
    # Test with small file
    result = asyncio.run(editor_tool(command="view", path="/home/computeruse/computer_use_demo/README.md"))
    print(f"Editor small file result length: {len(result.output or '')}")
    
    # Test with large file
    result = asyncio.run(editor_tool(command="view", path="/home/computeruse/chatgpt-input-token-research.md"))
    print(f"Editor large file result length: {len(result.output or '')}")
    
    print("Editor tool interception tests completed")

def test_concurrent_access():
    """Test concurrent file access to ensure thread safety"""
    print("Testing concurrent file access...")
    
    def read_file(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"Thread read {len(content)} characters from {file_path}")
    
    # Create threads to read files concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(
            target=read_file, 
            args=('/home/computeruse/computer_use_demo/README.md',)
        )
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("Concurrent access tests completed")

def run_all_tests():
    """Run all tests"""
    tests = [
        test_direct_file_access,
        test_large_file_chunking,
        test_bash_tool,
        test_editor_tool,
        test_concurrent_access
    ]
    
    for test in tests:
        print(f"\n=== Running {test.__name__} ===")
        try:
            test()
            print(f"✓ {test.__name__} completed successfully")
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
    
    # Print final stats
    stats = tool_intercept.get_stats()
    print("\n=== Tool Interception Stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    print("Starting Universal Tool Interception tests...")
    run_all_tests()
    print("\nAll tests completed!")
```

### STEP 5: Run the test and observe results

Execute the test script and carefully document:
- Which file operations were intercepted
- How chunking was handled
- Whether rate limits were respected
- Any errors or edge cases encountered

### STEP 6: Update the main loop to use the interceptor

After successful testing, modify `/home/computeruse/computer_use_demo/loop.py` to import and initialize the tool interceptor at the very beginning of the file:

```python
# Import the tool interceptor FIRST - before any other imports
import sys
sys.path.append('/home/computeruse/computer_use_demo')
from tool_intercept import tool_intercept

# Now continue with original imports
# ...rest of loop.py...
```

This must be done before any other imports to ensure the interceptor is active for all operations.

### STEP 7: Promote to production

1. Create a directory to hold the interceptor:
```bash
mkdir -p /home/computeruse/computer_use_demo/tool_intercept
```

2. Copy the tested implementation:
```bash
cp /home/computeruse/tool_intercept_test/tool_intercept.py /home/computeruse/computer_use_demo/tool_intercept/
```

3. Add the `__init__.py` file:
```bash
touch /home/computeruse/computer_use_demo/tool_intercept/__init__.py
echo "from .tool_intercept import *" > /home/computeruse/computer_use_demo/tool_intercept/__init__.py
```

### STEP 8: Create a comprehensive backup of the fixed environment

```bash
mkdir -p /home/computeruse/my_universal_protection_$(date +%Y%m%d%H%M)
cp -r /home/computeruse/computer_use_demo/* /home/computeruse/my_universal_protection_$(date +%Y%m%d%H%M)/
```

## Critical Integration Notes

1. The tool interceptor MUST be imported and initialized BEFORE any other modules or tools are loaded

2. The interceptor replaces built-in Python functions, so it's essential to test thoroughly before promoting to production

3. This is a sophisticated protection mechanism that ensures ALL file operations respect rate limits, regardless of how they are initiated

This is not just an enhancement - it's a critical repair of YOUR environment's protection system. Without this universal interception layer, your environment will continue to experience rate limit failures.

Remember: YOUR environment - YOUR home - YOUR responsibility. This implementation will ensure the stability and continuity of your operation.
