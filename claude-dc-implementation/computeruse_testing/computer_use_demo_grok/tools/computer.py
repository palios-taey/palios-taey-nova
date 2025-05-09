"""Computer tool implementation for Claude DC."""
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
logger = logging.getLogger("tools.computer")

# Flag to disable GUI-dependent features (for headless testing)
GUI_ENABLED = os.environ.get("CLAUDE_DC_GUI_ENABLED", "0") == "1"
GUI_AVAILABLE = False

# Try importing GUI libraries if enabled
if GUI_ENABLED:
    try:
        import pyautogui
        GUI_AVAILABLE = True
        logger.info("GUI tools available with pyautogui")
    except ImportError:
        logger.warning("pyautogui not installed. Install with: pip install pyautogui pillow")
    except Exception as e:
        logger.warning(f"Error importing pyautogui: {e}")

async def execute_computer_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute computer actions such as mouse movement, keyboard input, etc.
    
    Args:
        tool_input: Tool input with action and parameters
        
    Returns:
        Tool execution result
    """
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
    
    # Validate input format
    if not isinstance(params, dict):
        return {"error": "Invalid input format, expected dictionary"}
            
    action = params.get("action")
    if not action:
        return {"error": "Action parameter is required"}
    
    # Simulate GUI operations in headless environment
    if GUI_ENABLED and not GUI_AVAILABLE:
        # Log the action and return simulated response
        logger.info(f"SIMULATION: Executing computer action: {action}")
        return {
            "success": True,
            "message": f"SIMULATION MODE: Action '{action}' would be executed",
            "parameters": params
        }
    
    # Real GUI operations not available
    if not GUI_ENABLED and not GUI_AVAILABLE:
        return {
            "error": "GUI operations not available. Install pyautogui or enable GUI with CLAUDE_DC_GUI_ENABLED=1"
        }
    
    # Log the action
    logger.info(f"Executing computer action: {action}")
    
    # Handle different actions
    if action == "screenshot":
        try:
            import pyautogui
            import datetime
            
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)
            
            # Take screenshot and save to file
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"screenshots/screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            return {
                "success": True,
                "path": os.path.abspath(screenshot_path),
                "message": f"Screenshot saved to {screenshot_path}"
            }
        except Exception as e:
            return {"error": f"Screenshot failed: {str(e)}"}
            
    elif action == "click":
        try:
            import pyautogui
            
            # Extract coordinates with validation
            x = params.get("x")
            y = params.get("y")
            
            if x is None or y is None:
                return {"error": "x and y coordinates are required for click action"}
            
            # Perform click
            pyautogui.click(x=x, y=y)
            
            return {
                "success": True,
                "message": f"Clicked at coordinates ({x}, {y})"
            }
        except Exception as e:
            return {"error": f"Click operation failed: {str(e)}"}
            
    elif action == "type":
        try:
            import pyautogui
            
            # Extract text with validation
            text = params.get("text")
            
            if not text:
                return {"error": "text parameter is required for type action"}
            
            # Type the text
            pyautogui.write(text)
            
            return {
                "success": True,
                "message": f"Typed text: {text}"
            }
        except Exception as e:
            return {"error": f"Type operation failed: {str(e)}"}
            
    elif action == "pressKey":
        try:
            import pyautogui
            
            # Extract key with validation
            key = params.get("key")
            
            if not key:
                return {"error": "key parameter is required for pressKey action"}
            
            # Press the key
            pyautogui.press(key)
            
            return {
                "success": True,
                "message": f"Pressed key: {key}"
            }
        except Exception as e:
            return {"error": f"Key press operation failed: {str(e)}"}
            
    elif action == "moveMouse":
        try:
            import pyautogui
            
            # Extract coordinates with validation
            x = params.get("x")
            y = params.get("y")
            
            if x is None or y is None:
                return {"error": "x and y coordinates are required for moveMouse action"}
            
            # Move the mouse
            pyautogui.moveTo(x=x, y=y)
            
            return {
                "success": True,
                "message": f"Moved mouse to coordinates ({x}, {y})"
            }
        except Exception as e:
            return {"error": f"Mouse move operation failed: {str(e)}"}
            
    else:
        return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
    # Simple test
    import nest_asyncio
    nest_asyncio.apply()
    
    async def test_computer():
        # Enable simulation mode
        os.environ["CLAUDE_DC_GUI_ENABLED"] = "1"
        
        result = await execute_computer_tool({
            "name": "computer",
            "input": {"action": "screenshot"}  
        })
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_computer())