"""Bash tool implementation for Claude DC."""
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tools.bash")

async def execute_bash_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a bash command and return the result.
    
    Args:
        tool_input: Tool input with command and optional timeout
        
    Returns:
        Tool execution result with output and status
    """
    try:
        # Handle different input formats
        if "parameters" in tool_input:
            # New tool format (tool_type format)
            params = tool_input.get("parameters", {})
        else:
            # Old format (function format) or direct input
            params = tool_input.get("input", {})
            if not params:
                # Handle direct parameters case
                params = tool_input
                
        if not isinstance(params, dict):
            return {"error": "Invalid input format, expected dictionary"}
            
        command = params.get("command")
        if not command:
            return {"error": "Command parameter is required"}
        
        timeout = params.get("timeout", 30)  # Default 30 seconds timeout
        
        # Log command execution
        logger.info(f"Executing bash command: {command}")
        
        # Execute the command with timeout
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            return {
                "output": stdout_str,
                "error": stderr_str if stderr_str else None,
                "status": process.returncode
            }
        except asyncio.TimeoutError:
            try:
                process.kill()
                return {"error": f"Command timed out after {timeout} seconds"}
            except Exception as e:
                return {"error": f"Command timed out and couldn't be killed: {str(e)}"}
                
    except Exception as e:
        logger.error(f"Error executing bash command: {e}")
        return {"error": f"Command execution failed: {str(e)}"}

if __name__ == "__main__":
    # Simple test
    import nest_asyncio
    nest_asyncio.apply()
    
    async def test_bash():
        result = await execute_bash_tool({
            "name": "bash",
            "input": {"command": "echo 'Hello from bash tool'"}  
        })
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_bash())