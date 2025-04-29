"""
Test script for tool implementations.
Tests the functionality of all tool implementations.
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_tools")

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    logger.error("nest_asyncio not installed. Install with: pip install nest_asyncio")
    sys.exit(1)

# Import tool implementations
try:
    from tools import execute_bash_tool, execute_computer_tool, execute_edit_tool
    logger.info("Successfully imported tool implementations")
except ImportError as e:
    logger.error(f"Failed to import tool implementations: {e}")
    sys.exit(1)

async def test_bash_tool():
    """Test the bash tool implementation"""
    logger.info("Testing bash tool...")
    
    # Test with valid command
    cmd_result = await execute_bash_tool({
        "name": "bash",
        "input": {"command": "echo 'Hello from bash tool test'"}
    })
    
    if not cmd_result or "error" in cmd_result and cmd_result["error"]:
        logger.error(f"Bash tool test failed: {cmd_result.get('error', 'Unknown error')}")
        return False
        
    # Check output content
    if "Hello from bash tool test" not in cmd_result.get("output", ""):
        logger.error(f"Bash tool output incorrect: {cmd_result.get('output', '')}")
        return False
        
    # Test with invalid command
    invalid_result = await execute_bash_tool({
        "name": "bash",
        "input": {}  # Missing command parameter
    })
    
    if not invalid_result or "error" not in invalid_result:
        logger.error("Bash tool did not handle missing command parameter correctly")
        return False
    
    # Test timeout parameter
    timeout_result = await execute_bash_tool({
        "name": "bash",
        "input": {"command": "sleep 3", "timeout": 1}
    })
    
    if not timeout_result or "error" not in timeout_result or "timed out" not in timeout_result["error"]:
        logger.error("Bash tool did not handle timeout correctly")
        return False
        
    logger.info("Bash tool tests passed!")
    return True

async def test_edit_tool():
    """Test the edit tool implementation"""
    logger.info("Testing edit tool...")
    test_file_path = "test_edit_tool.txt"
    test_content = "This is a test file created by the edit tool test."
    
    # Test write operation
    write_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "write",
            "path": test_file_path,
            "content": test_content
        }
    })
    
    if not write_result or not write_result.get("success"):
        logger.error(f"Edit tool write operation failed: {write_result.get('error', 'Unknown error')}")
        return False
        
    # Test read operation
    read_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read",
            "path": test_file_path
        }
    })
    
    if not read_result or not read_result.get("success"):
        logger.error(f"Edit tool read operation failed: {read_result.get('error', 'Unknown error')}")
        return False
        
    # Verify content
    if read_result.get("content") != test_content:
        logger.error(f"Edit tool content mismatch. Expected: '{test_content}', Got: '{read_result.get('content')}'")
        return False
        
    # Test append operation
    append_content = "\nThis is appended content."
    append_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "append",
            "path": test_file_path,
            "content": append_content
        }
    })
    
    if not append_result or not append_result.get("success"):
        logger.error(f"Edit tool append operation failed: {append_result.get('error', 'Unknown error')}")
        return False
        
    # Verify appended content
    verify_append = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read",
            "path": test_file_path
        }
    })
    
    expected_content = test_content + append_content
    if verify_append.get("content") != expected_content:
        logger.error(f"Edit tool append content mismatch. Expected: '{expected_content}', Got: '{verify_append.get('content')}'")
        return False
        
    # Test delete operation
    delete_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "delete",
            "path": test_file_path
        }
    })
    
    if not delete_result or not delete_result.get("success"):
        logger.error(f"Edit tool delete operation failed: {delete_result.get('error', 'Unknown error')}")
        return False
        
    # Verify file was deleted
    verify_delete = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read",
            "path": test_file_path
        }
    })
    
    if "error" not in verify_delete or "not found" not in verify_delete["error"]:
        logger.error("Edit tool delete operation did not actually delete the file")
        return False
        
    # Test invalid action
    invalid_action = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "invalid_action",
            "path": test_file_path
        }
    })
    
    if not invalid_action or "error" not in invalid_action:
        logger.error("Edit tool did not handle invalid action correctly")
        return False
        
    logger.info("Edit tool tests passed!")
    return True

async def test_parameter_validation():
    """Test parameter validation in tools"""
    logger.info("Testing parameter validation...")
    
    # Test bash tool with missing command
    bash_result = await execute_bash_tool({
        "name": "bash",
        "input": {}  # Missing command
    })
    
    if "error" not in bash_result or "required" not in bash_result["error"].lower():
        logger.error(f"Bash tool didn't validate missing command: {bash_result}")
        return False
        
    # Test edit tool with missing path
    edit_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read"
            # Missing path
        }
    })
    
    if "error" not in edit_result or "required" not in edit_result["error"].lower():
        logger.error(f"Edit tool didn't validate missing path: {edit_result}")
        return False
        
    # Test edit tool with missing content for write
    write_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "write",
            "path": "test.txt"
            # Missing content
        }
    })
    
    if "error" not in write_result or "required" not in write_result["error"].lower():
        logger.error(f"Edit tool didn't validate missing content: {write_result}")
        return False
        
    # Test computer tool with missing action
    computer_result = await execute_computer_tool({
        "name": "computer",
        "input": {}  # Missing action
    })
    
    if "error" not in computer_result or "required" not in computer_result["error"].lower():
        logger.error(f"Computer tool didn't validate missing action: {computer_result}")
        return False
        
    logger.info("Parameter validation tests passed!")
    return True

async def test_tool_error_handling():
    """Test error handling in tools"""
    logger.info("Testing error handling...")
    
    # Test bash tool with command that fails
    bash_result = await execute_bash_tool({
        "name": "bash",
        "input": {"command": "nonexistentcommand"}
    })
    
    if not bash_result.get("error") and bash_result.get("status", 0) == 0:
        logger.error(f"Bash tool didn't handle command failure correctly: {bash_result}")
        return False
    
    # Test edit tool with nonexistent file
    nonexistent_file = "/path/to/nonexistent/file.txt"
    read_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "read",
            "path": nonexistent_file
        }
    })
    
    if "error" not in read_result or "not found" not in read_result["error"]:
        logger.error(f"Edit tool didn't handle nonexistent file correctly: {read_result}")
        return False
        
    # Test delete on nonexistent file
    delete_result = await execute_edit_tool({
        "name": "edit",
        "input": {
            "action": "delete",
            "path": nonexistent_file
        }
    })
    
    if "error" not in delete_result or "not found" not in delete_result["error"]:
        logger.error(f"Edit tool didn't handle delete on nonexistent file correctly: {delete_result}")
        return False
    
    logger.info("Error handling tests passed!")
    return True

async def run_all_tests():
    """Run all tool tests"""
    results = {}
    
    results["bash_tool"] = await test_bash_tool()
    results["edit_tool"] = await test_edit_tool()
    results["parameter_validation"] = await test_parameter_validation()
    results["error_handling"] = await test_tool_error_handling()
    
    # Skip computer tool tests as they require GUI
    logger.info("Skipping computer tool tests as they require GUI interaction")
    
    # Print summary
    print("\n" + "=" * 60)
    print(" Tool Tests Results ".center(60, "="))
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.ljust(20)}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    print(f" Overall: {'✅ PASSED' if all_passed else '❌ FAILED'} ".center(60, "="))
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)