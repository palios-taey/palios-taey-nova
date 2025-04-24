"""
Real tool adapters for DC Custom Implementation.
Provides safe adapters to the actual production tools.
"""

import sys
import logging
import importlib
import traceback
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
    # Add the dc_custom directory to the path
    DC_CUSTOM_DIR = Path("/home/computeruse/computer_use_demo/dc_custom")
    if str(DC_CUSTOM_DIR) not in sys.path:
        sys.path.insert(0, str(DC_CUSTOM_DIR))
        logger.info(f"Added {DC_CUSTOM_DIR} to sys.path")
    
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
    """Adapter for computer tool."""
    try:
        action = tool_input.get("action")
        
        if not action:
            return DCToolResult(error="Missing required 'action' parameter")
        
        # Transform input to format expected by production tool
        kwargs = {}
        
        if action == "screenshot":
            # Production tool doesn't need additional parameters for screenshot
            pass
        elif action == "move_mouse":
            if "coordinates" not in tool_input:
                return DCToolResult(error="Missing required 'coordinates' parameter")
            coords = tool_input["coordinates"]
            kwargs["x"] = coords[0]
            kwargs["y"] = coords[1]
        elif action == "left_button_press":
            if "coordinates" not in tool_input:
                return DCToolResult(error="Missing required 'coordinates' parameter")
            coords = tool_input["coordinates"]
            kwargs["x"] = coords[0]
            kwargs["y"] = coords[1]
        elif action == "type_text":
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
    """Adapter for bash tool."""
    try:
        if "command" not in tool_input:
            return DCToolResult(error="Missing required 'command' parameter")
        
        command = tool_input["command"]
        
        # Call the production tool
        result = await tool(command=command)
        
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