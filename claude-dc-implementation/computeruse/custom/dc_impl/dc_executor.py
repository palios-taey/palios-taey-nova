"""
Safe executor for tools with namespace isolation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

# Import from our namespace-isolated modules
from .models.dc_models import DCToolResult
from .registry.dc_registry import dc_get_tool_executor, dc_get_tool_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_executor")

async def dc_execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Execute a tool based on name and input parameters with namespace isolation.
    """
    logger.info(f"DC Execute Tool - Tool: {tool_name}")
    
    # Get the validator and executor functions
    validator = dc_get_tool_validator(tool_name)
    executor = dc_get_tool_executor(tool_name)
    
    # Check if tool exists
    if not validator or not executor:
        return DCToolResult(error=f"Unknown tool: {tool_name}")
    
    # Validate the parameters
    valid, error_msg = validator(tool_input)
    if not valid:
        return DCToolResult(error=f"Invalid parameters: {error_msg}")
    
    # Execute with fallback
    return await dc_execute_with_fallback(tool_name, tool_input, executor)

async def dc_execute_with_fallback(
    tool_name: str, 
    tool_input: Dict[str, Any],
    executor,
    max_retries: int = 1
) -> DCToolResult:
    """
    Execute a tool with retry logic and fallback strategies.
    Uses namespace isolation to avoid conflicts.
    """
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            logger.info(f"DC Execute With Fallback - Attempt {retries+1} for {tool_name}")
            result = await executor(tool_input)
            if not result.error:
                return result
            last_error = result.error
        except Exception as e:
            logger.error(f"DC Tool execution failed: {str(e)}")
            last_error = str(e)
        
        # Apply fallback strategy if needed
        if retries < max_retries:
            logger.info(f"Retrying tool {tool_name} (attempt {retries+1}/{max_retries})")
            await asyncio.sleep(0.5)
            # Simple fallback strategy - no modifications for now
        
        retries += 1
    
    return DCToolResult(error=f"Tool execution failed after retries: {last_error}")