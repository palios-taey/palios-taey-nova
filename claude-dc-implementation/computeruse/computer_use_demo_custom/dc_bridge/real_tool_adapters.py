"""
Real tool adapters for DC Custom Implementation.
Provides safe adapters to the actual production tools.
"""

import sys
import logging
import importlib
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("real_adapters.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("real_adapters")

# Import from custom implementation
try:
    # Add the dc_impl directory to the path
    DC_IMPL_DIR = Path("/home/computeruse/computer_use_demo/dc_impl")
    if str(DC_IMPL_DIR) not in sys.path:
        sys.path.insert(0, str(DC_IMPL_DIR))
        logger.info(f"Added {DC_IMPL_DIR} to sys.path")
    
    # Import directly
    from models.dc_models import DCToolResult
except ImportError:
    # Define a simple version for testing
    from dataclasses import dataclass
    
    @dataclass
    class DCToolResult:
        """Represents the result of a tool execution."""
        output: str = None
        error: str = None
        base64_image: str = None

class ProductionToolManager:
    """Safely manages access to production tools."""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.adapters: Dict[str, Callable] = {}
        
        # Try to import production tools
        self._import_production_tools()
    
    def _import_production_tools(self) -> None:
        """Safely import production tools."""
        logger.info("Attempting to import production tools")
        
        # Original tools path
        prod_dir = Path("/home/computeruse/computer_use_demo")
        
        # Add production directory to path temporarily
        orig_path = sys.path.copy()
        if str(prod_dir) not in sys.path:
            sys.path.insert(0, str(prod_dir))
        
        try:
            # Import tools in a safe manner
            self._safe_import_tool("computer", "tools.computer", "ComputerTool20250124")
            self._safe_import_tool("bash", "tools.bash", "BashTool20250124")
            self._safe_import_tool("edit", "tools.edit", "StrReplaceEditorTool20250124")
            
            logger.info(f"Successfully imported {len(self.tools)} production tools")
        except Exception as e:
            logger.error(f"Error importing production tools: {str(e)}")
        finally:
            # Restore original path
            sys.path = orig_path
    
    def _safe_import_tool(self, name: str, module_path: str, class_name: str) -> None:
        """Safely import a specific tool."""
        try:
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
            self.tools[name] = tool_class()
            logger.info(f"Successfully imported {name} tool")
        except ImportError as e:
            logger.warning(f"Could not import {name} tool: {str(e)}")
        except AttributeError as e:
            logger.warning(f"Could not find {class_name} in {module_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error importing {name} tool: {str(e)}")
    
    def register_adapter(self, tool_name: str, adapter: Callable) -> None:
        """Register an adapter function for a specific tool."""
        self.adapters[tool_name] = adapter
        logger.info(f"Registered adapter for {tool_name}")
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self.tools
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool if it's available."""
        return self.tools.get(tool_name)
    
    def has_adapter(self, tool_name: str) -> bool:
        """Check if an adapter is available for a tool."""
        return tool_name in self.adapters
    
    async def execute_with_adapter(self, tool_name: str, tool_input: Dict[str, Any]) -> DCToolResult:
        """Execute a tool using its adapter."""
        if not self.has_tool(tool_name):
            return DCToolResult(error=f"Tool '{tool_name}' is not available")
        
        if not self.has_adapter(tool_name):
            return DCToolResult(error=f"No adapter registered for tool '{tool_name}'")
        
        try:
            tool = self.get_tool(tool_name)
            adapter = self.adapters[tool_name]
            return await adapter(tool, tool_input)
        except Exception as e:
            logger.error(f"Error executing {tool_name} with adapter: {str(e)}")
            logger.error(traceback.format_exc())
            return DCToolResult(error=f"Error executing tool: {str(e)}")

# Create tool manager
manager = ProductionToolManager()

# Adapter for computer tool
async def adapt_computer_tool(tool: Any, tool_input: Dict[str, Any]) -> DCToolResult:
    """Adapter for computer tool with enhanced screenshot functionality."""
    try:
        action = tool_input.get("action")
        
        if not action:
            return DCToolResult(error="Missing required 'action' parameter")
        
        # Import feature toggle system to check if the screenshot adapter is enabled
        try:
            from dc_bridge.enhanced_bridge import toggles
            use_screenshot_adapter = toggles.is_enabled("use_screenshot_adapter")
        except ImportError:
            logger.warning("Could not import feature toggles, defaulting to standard adapter")
            use_screenshot_adapter = False
        
        # Use the enhanced screenshot adapter if enabled and the action is screenshot
        if use_screenshot_adapter and action == "screenshot":
            logger.info("Using enhanced screenshot adapter")
            try:
                # Import the custom screenshot implementation
                sys.path.insert(0, str(Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo_custom/dc_impl")))
                from tools.dc_adapters import dc_execute_computer_tool
                
                # Call the enhanced implementation
                result = await dc_execute_computer_tool(tool_input)
                
                # Convert to the format expected by the bridge
                return result
            except ImportError as e:
                logger.error(f"Could not import screenshot adapter: {str(e)}")
                logger.error("Falling back to standard adapter")
            except Exception as e:
                logger.error(f"Error in screenshot adapter: {str(e)}")
                logger.error(traceback.format_exc())
                logger.error("Falling back to standard adapter")
        
        # Standard adapter for computer tool (used for non-screenshot actions or when adapter is disabled)
        # Transform input to format expected by production tool
        kwargs = {}
        
        if action == "screenshot":
            # Production tool doesn't need additional parameters for screenshot
            pass
        elif action == "move_mouse":
            if "coordinates" not in tool_input:
                return DCToolResult(error="Missing required 'coordinates' parameter")
            coords = tool_input["coordinates"]
            kwargs["coordinate"] = coords  # Fixed parameter name to match production tool
        elif action == "left_click":
            if "coordinates" not in tool_input:
                return DCToolResult(error="Missing required 'coordinates' parameter")
            coords = tool_input["coordinates"]
            kwargs["coordinate"] = coords  # Fixed parameter name to match production tool
        elif action == "type":
            if "text" not in tool_input:
                return DCToolResult(error="Missing required 'text' parameter")
            kwargs["text"] = tool_input["text"]
        # Add other actions as needed
        
        # Call the appropriate method on the production tool
        method = getattr(tool, action, None)
        if not method:
            return DCToolResult(error=f"Unknown action: {action}")
        
        # Execute the method
        result = await method(**kwargs)
        
        # Transform the result to our format
        return DCToolResult(
            output=result.get("output"),
            error=result.get("error"),
            base64_image=result.get("base64_image")
        )
    except AttributeError as e:
        logger.error(f"Attribute error in computer tool adapter: {str(e)}")
        return DCToolResult(error=f"Attribute error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in computer tool adapter: {str(e)}")
        logger.error(traceback.format_exc())
        return DCToolResult(error=f"Error: {str(e)}")

# Adapter for bash tool
async def adapt_bash_tool(tool: Any, tool_input: Dict[str, Any]) -> DCToolResult:
    """Adapter for bash tool with enhanced read-only command safety."""
    try:
        if "command" not in tool_input:
            return DCToolResult(error="Missing required 'command' parameter")
        
        command = tool_input["command"]
        
        # Import feature toggle system to check if the read-only bash adapter is enabled
        try:
            from dc_bridge.enhanced_bridge import toggles
            use_readonly_bash_adapter = toggles.is_enabled("use_readonly_bash_adapter")
        except ImportError:
            logger.warning("Could not import feature toggles, defaulting to standard adapter")
            use_readonly_bash_adapter = False
        
        # Use the enhanced read-only bash adapter if enabled
        if use_readonly_bash_adapter:
            logger.info("Using enhanced read-only bash adapter")
            try:
                # Import the custom bash implementation
                sys.path.insert(0, str(Path("/home/computeruse/computer_use_demo/dc_impl")))
                from tools.dc_adapters import dc_execute_bash_tool, dc_validate_read_only_command
                
                # First validate it's a read-only command
                is_valid, validation_message = dc_validate_read_only_command(command)
                if not is_valid:
                    logger.error(f"Command validation failed: {validation_message}")
                    return DCToolResult(error=f"Command validation failed: {validation_message}")
                
                # Call the enhanced implementation
                result = await dc_execute_bash_tool(tool_input)
                
                # Convert to the format expected by the bridge
                return result
            except ImportError as e:
                logger.error(f"Could not import read-only bash adapter: {str(e)}")
                logger.error("Falling back to standard adapter")
            except Exception as e:
                logger.error(f"Error in read-only bash adapter: {str(e)}")
                logger.error(traceback.format_exc())
                logger.error("Falling back to standard adapter")
        
        # Standard adapter for bash tool when adapter is disabled or on fallback
        # Call the production tool with resource limits for safety
        # Set timeout and resource limits
        timeout = 15.0  # seconds
        modified_command = f"timeout {timeout} bash -c 'ulimit -t 10 -v 500000; {command}'"
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                tool(command=modified_command),
                timeout=timeout + 2  # Add a small buffer for the timeout command itself
            )
        except asyncio.TimeoutError:
            # Handle timeout
            logger.error(f"Command timed out after {timeout} seconds")
            # Attempt to clean up by restarting bash
            try:
                await tool(restart=True)
            except Exception:
                pass
            return DCToolResult(error=f"Command timed out after {timeout} seconds")
        
        # Transform the result to our format
        return DCToolResult(
            output=result.get("output"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error in bash tool adapter: {str(e)}")
        logger.error(traceback.format_exc())
        return DCToolResult(error=f"Error: {str(e)}")

# Register adapters
manager.register_adapter("computer", adapt_computer_tool)
manager.register_adapter("bash", adapt_bash_tool)

# Exported functions
async def execute_real_tool(tool_name: str, tool_input: Dict[str, Any]) -> DCToolResult:
    """Execute a real tool using the appropriate adapter."""
    # Map our tool names to production tool names
    tool_map = {
        "dc_computer": "computer",
        "dc_bash": "bash"
    }
    
    # Get the production tool name
    prod_tool_name = tool_map.get(tool_name)
    if not prod_tool_name:
        return DCToolResult(error=f"Unknown tool: {tool_name}")
    
    # Execute with adapter
    return await manager.execute_with_adapter(prod_tool_name, tool_input)

def is_real_tool_available(tool_name: str) -> bool:
    """Check if a real tool is available."""
    tool_map = {
        "dc_computer": "computer",
        "dc_bash": "bash"
    }
    
    prod_tool_name = tool_map.get(tool_name)
    if not prod_tool_name:
        return False
    
    return manager.has_tool(prod_tool_name) and manager.has_adapter(prod_tool_name)