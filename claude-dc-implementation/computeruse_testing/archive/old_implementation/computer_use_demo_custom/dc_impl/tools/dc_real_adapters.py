"""
Real tool adapters for integration with production tools.
This module provides adapter functions that safely connect to the existing
tool implementations from the production environment.
"""

import logging
import time
import asyncio
import traceback
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Fix imports to work both as relative import and direct import
try:
    # When imported directly (for tests)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.dc_models import DCToolResult
except ImportError:
    # When imported as a package
    from ..models.dc_models import DCToolResult

# Configure logging with namespace isolation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dc_real_adapters")

# Create a safe log directory
LOG_DIR = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/logs")
LOG_DIR.mkdir(exist_ok=True)

# Add file handler for adapter logs
file_handler = logging.FileHandler(LOG_DIR / "dc_real_adapters.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Paths to the original tools - will be lazy-loaded to avoid import conflicts
_computer_tool = None
_bash_tool = None
_edit_tool = None

def _safely_import_production_tools():
    """Safely import production tools without namespace conflicts."""
    global _computer_tool, _bash_tool, _edit_tool
    
    # Only import if not already imported
    if _computer_tool is not None and _bash_tool is not None and _edit_tool is not None:
        return
    
    try:
        # Use dynamic imports to avoid namespace conflicts
        import importlib.util
        
        # Store the current sys.path
        original_path = sys.path.copy()
        
        # Temporarily modify sys.path to include production path
        prod_path = "/home/computeruse/computer_use_demo"
        if prod_path not in sys.path:
            sys.path.insert(0, prod_path)
        
        # Import the tools module
        try:
            # First try normal import
            import tools.computer
            import tools.bash
            import tools.edit
            
            # Initialize tool instances
            _computer_tool = tools.computer.ComputerTool20250124()
            _bash_tool = tools.bash.BashTool20250124()
            _edit_tool = tools.edit.EditTool20250124()
            
            logger.info("Successfully imported production tools via direct import")
        except Exception as e:
            # If that fails, try spec-based import
            logger.warning(f"Direct import failed: {str(e)}, trying spec-based import")
            
            # Computer tool
            computer_spec = importlib.util.spec_from_file_location(
                "computer", 
                os.path.join(prod_path, "tools", "computer.py")
            )
            computer_module = importlib.util.module_from_spec(computer_spec)
            computer_spec.loader.exec_module(computer_module)
            
            # Bash tool
            bash_spec = importlib.util.spec_from_file_location(
                "bash", 
                os.path.join(prod_path, "tools", "bash.py")
            )
            bash_module = importlib.util.module_from_spec(bash_spec)
            bash_spec.loader.exec_module(bash_module)
            
            # Edit tool
            edit_spec = importlib.util.spec_from_file_location(
                "edit", 
                os.path.join(prod_path, "tools", "edit.py")
            )
            edit_module = importlib.util.module_from_spec(edit_spec)
            edit_spec.loader.exec_module(edit_module)
            
            # Initialize tool instances
            _computer_tool = computer_module.ComputerTool20250124()
            _bash_tool = bash_module.BashTool20250124()
            _edit_tool = edit_module.EditTool20250124()
            
            logger.info("Successfully imported production tools via spec-based import")
        
        # Restore the original sys.path
        sys.path = original_path
        
    except Exception as e:
        logger.error(f"Failed to import production tools: {str(e)}")
        logger.error(traceback.format_exc())
        # Fall back to mock implementations
        _computer_tool = None
        _bash_tool = None
        _edit_tool = None
        raise ImportError(f"Failed to import production tools: {str(e)}")

async def dc_execute_computer_tool_real(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Adapter for real computer tool implementation with namespace isolation.
    
    Args:
        tool_input: Parameters for the computer tool
        
    Returns:
        DCToolResult containing output, error, or image data
    """
    logger.info(f"DC Real Computer Tool - Action: {tool_input.get('action')}")
    start_time = time.time()
    
    try:
        # Try to import production tools if not already imported
        _safely_import_production_tools()
        
        if _computer_tool is None:
            return DCToolResult(error="Computer tool not available")
        
        # Transform parameters to production format
        kwargs = _transform_computer_parameters(tool_input)
        
        # Call the real tool implementation with appropriate error handling
        try:
            result = await _computer_tool(**kwargs)
            
            # Transform result back to our format
            dc_result = DCToolResult(
                output=result.output,
                error=result.error,
                base64_image=result.base64_image
            )
            
            # Log success
            execution_time = time.time() - start_time
            logger.info(f"Computer tool executed in {execution_time:.2f}s")
            
            return dc_result
            
        except Exception as e:
            logger.error(f"Error executing computer tool: {str(e)}")
            logger.error(traceback.format_exc())
            return DCToolResult(error=f"Computer tool execution error: {str(e)}")
    
    except ImportError as e:
        # Fall back to mock implementation if import fails
        logger.warning(f"Using mock implementation due to import error: {str(e)}")
        from .dc_adapters import dc_execute_computer_tool
        return await dc_execute_computer_tool(tool_input)

async def dc_execute_bash_tool_real(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Adapter for real bash tool implementation with namespace isolation.
    
    Args:
        tool_input: Parameters for the bash tool
        
    Returns:
        DCToolResult containing output or error
    """
    logger.info(f"DC Real Bash Tool - Command: {tool_input.get('command')}")
    start_time = time.time()
    
    try:
        # Try to import production tools if not already imported
        _safely_import_production_tools()
        
        if _bash_tool is None:
            return DCToolResult(error="Bash tool not available")
        
        # Call the real tool implementation with appropriate error handling
        try:
            result = await _bash_tool(**tool_input)
            
            # Transform result back to our format
            dc_result = DCToolResult(
                output=result.output,
                error=result.error
            )
            
            # Log success
            execution_time = time.time() - start_time
            logger.info(f"Bash tool executed in {execution_time:.2f}s")
            
            return dc_result
            
        except Exception as e:
            logger.error(f"Error executing bash tool: {str(e)}")
            logger.error(traceback.format_exc())
            return DCToolResult(error=f"Bash tool execution error: {str(e)}")
    
    except ImportError as e:
        # Fall back to mock implementation if import fails
        logger.warning(f"Using mock implementation due to import error: {str(e)}")
        from .dc_adapters import dc_execute_bash_tool
        return await dc_execute_bash_tool(tool_input)

async def dc_execute_edit_tool_real(tool_input: Dict[str, Any]) -> DCToolResult:
    """
    Adapter for real str_replace_editor tool implementation with namespace isolation.
    
    Args:
        tool_input: Parameters for the editor tool
        
    Returns:
        DCToolResult containing output or error
    """
    logger.info(f"DC Real Edit Tool - Command: {tool_input.get('command')}, Path: {tool_input.get('path')}")
    start_time = time.time()
    
    try:
        # Try to import production tools if not already imported
        _safely_import_production_tools()
        
        if _edit_tool is None:
            return DCToolResult(error="Edit tool not available")
        
        # Call the real tool implementation with appropriate error handling
        try:
            result = await _edit_tool(**tool_input)
            
            # Transform result back to our format
            dc_result = DCToolResult(
                output=result.output,
                error=result.error
            )
            
            # Log success
            execution_time = time.time() - start_time
            logger.info(f"Edit tool executed in {execution_time:.2f}s")
            
            return dc_result
            
        except Exception as e:
            logger.error(f"Error executing edit tool: {str(e)}")
            logger.error(traceback.format_exc())
            return DCToolResult(error=f"Edit tool execution error: {str(e)}")
    
    except ImportError as e:
        # Fall back to mock implementation if import fails
        logger.warning(f"Using mock implementation due to import error: {str(e)}")
        # Note: We don't have a mock edit tool yet, so return an error
        return DCToolResult(error=f"Edit tool not available: {str(e)}")

def _transform_computer_parameters(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform computer tool parameters from our format to production format.
    
    Args:
        tool_input: Parameters in our format
        
    Returns:
        Parameters in production format
    """
    # Create a new dictionary for transformed parameters
    transformed = {}
    
    # Map action parameter (same in both)
    if "action" in tool_input:
        transformed["action"] = tool_input["action"]
    
    # Map coordinates parameter (different name in production)
    if "coordinates" in tool_input:
        transformed["coordinate"] = tool_input["coordinates"]
    
    # Map text parameter (same in both)
    if "text" in tool_input:
        transformed["text"] = tool_input["text"]
    
    # Map other parameters
    if "duration" in tool_input:
        transformed["duration"] = tool_input["duration"]
    
    if "scroll_direction" in tool_input:
        transformed["scroll_direction"] = tool_input["scroll_direction"]
    
    if "scroll_amount" in tool_input:
        transformed["scroll_amount"] = tool_input["scroll_amount"]
    
    if "start_coordinate" in tool_input:
        transformed["start_coordinate"] = tool_input["start_coordinate"]
    
    return transformed