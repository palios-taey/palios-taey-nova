"""Edit tool implementation for Claude DC."""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tools.edit")

async def execute_edit_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file operations such as read, write, append, delete.
    
    Args:
        tool_input: Tool input with action, path, and optional content
        
    Returns:
        Tool execution result
    """
    try:
        # Log received tool input for debugging
        logger.info(f"Edit tool received input: {json.dumps(tool_input, default=str)}")
        
        # Handle different input formats
        if "parameters" in tool_input:
            # New tool format (tool_type format)
            params = tool_input.get("parameters", {})
            logger.info(f"Using parameters from tool_input.parameters: {json.dumps(params, default=str)}")
        else:
            # Old format (function format) or direct input
            params = tool_input.get("input", {})
            if not params:
                # Handle direct parameters case
                params = tool_input
            logger.info(f"Using parameters from input or direct: {json.dumps(params, default=str)}")
    
        # Validate input format
        if not isinstance(params, dict):
            return {"error": "Invalid input format, expected dictionary"}
            
        action = params.get("action")
        if not action:
            return {"error": "Action parameter is required"}
            
        path = params.get("path")
        if not path:
            return {"error": "Path parameter is required"}
            
        # Make path absolute if it's not already
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Log the action
        logger.info(f"Executing file {action} operation on {path}")
        
        if action == "read":
            # Read file
            try:
                if not os.path.exists(path):
                    return {"error": f"File not found: {path}"}
                    
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                return {
                    "success": True,
                    "content": content,
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}
                
        elif action == "write":
            # Write file (overwrites existing)
            content = params.get("content")
            if content is None:
                return {"error": "Content parameter is required for write action"}
                
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                    
                return {
                    "success": True,
                    "message": f"File written successfully: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to write file: {str(e)}"}
                
        elif action == "append":
            # Append to file
            content = params.get("content")
            if content is None:
                return {"error": "Content parameter is required for append action"}
                
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'a', encoding='utf-8') as file:
                    file.write(content)
                    
                return {
                    "success": True,
                    "message": f"Content appended successfully to: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to append to file: {str(e)}"}
                
        elif action == "delete":
            # Delete file
            try:
                if not os.path.exists(path):
                    return {"error": f"File not found: {path}"}
                    
                os.remove(path)
                
                return {
                    "success": True,
                    "message": f"File deleted successfully: {path}",
                    "path": path
                }
            except Exception as e:
                return {"error": f"Failed to delete file: {str(e)}"}
                
        else:
            return {"error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"Error executing file operation: {e}")
        return {"error": f"Operation failed: {str(e)}"}

if __name__ == "__main__":
    # Simple test
    import nest_asyncio
    nest_asyncio.apply()
    
    async def test_edit():
        # Write test
        write_result = await execute_edit_tool({
            "name": "edit",
            "input": {
                "action": "write",
                "path": "test_file.txt",
                "content": "This is a test file created by the edit tool."
            }
        })
        print("Write result:", json.dumps(write_result, indent=2))
        
        # Read test
        read_result = await execute_edit_tool({
            "name": "edit",
            "input": {
                "action": "read",
                "path": "test_file.txt"
            }
        })
        print("\nRead result:", json.dumps(read_result, indent=2))
        
        # Delete test
        delete_result = await execute_edit_tool({
            "name": "edit",
            "input": {
                "action": "delete",
                "path": "test_file.txt"
            }
        })
        print("\nDelete result:", json.dumps(delete_result, indent=2))
    
    asyncio.run(test_edit())