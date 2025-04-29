"""
Computer tool implementation for Claude Computer Use.
Provides GUI interaction capabilities through mouse and keyboard control.
"""

import os
import asyncio
import base64
import logging
import io
from typing import Dict, Any, Optional, Callable, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("computer_tool")

# Check if we can import pyautogui
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    from PIL import Image
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    logger.warning("pyautogui not installed. Install with: pip install pyautogui pillow")

class ToolResult:
    """Container for tool execution results"""
    def __init__(self, 
                 output: Optional[str] = None, 
                 error: Optional[str] = None, 
                 base64_image: Optional[str] = None):
        self.output = output
        self.error = error
        self.base64_image = base64_image
    
    def __str__(self):
        if self.error:
            return f"Error: {self.error}"
        return self.output or ""

async def validate_computer_parameters(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the parameters for the computer tool.
    
    Args:
        tool_input: The input parameters for the tool
        
    Returns:
        (is_valid, error_message)
    """
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action", "")
    if not action or not isinstance(action, str):
        return False, "Action must be a non-empty string"
    
    # Validate action-specific parameters
    if action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, "Coordinates must be a list of two integers [x, y]"
        
        if not all(isinstance(coord, int) for coord in coordinates):
            return False, "Coordinates must be integers"
    
    elif action == "type_text":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for type_text"
        
        text = tool_input.get("text")
        if not isinstance(text, str):
            return False, "Text must be a string"
    
    elif action == "press_key":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for press_key"
        
        key = tool_input.get("text")
        if not isinstance(key, str):
            return False, "Key must be a string"
            
    elif action == "wait":
        if "duration" in tool_input:
            duration = tool_input.get("duration")
            if not isinstance(duration, (int, float)) or duration <= 0:
                return False, "Duration must be a positive number"
    
    return True, "Valid parameters"

async def take_screenshot() -> Optional[str]:
    """Take a screenshot and return as base64 string"""
    if not PYAUTOGUI_AVAILABLE:
        return None
    
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Convert to base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return None

async def execute_computer_tool(
    tool_input: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> ToolResult:
    """
    Execute a computer action.
    
    Args:
        tool_input: The input parameters for the tool
        progress_callback: Optional callback for progress updates
        
    Returns:
        ToolResult with the output or error
    """
    # Check if pyautogui is available
    if not PYAUTOGUI_AVAILABLE:
        return ToolResult(
            error="pyautogui not installed. This is a simulated environment.",
            output="Note: Using simulated computer control. Install pyautogui for actual computer control."
        )
    
    # Validate parameters
    valid, error_message = await validate_computer_parameters(tool_input)
    if not valid:
        return ToolResult(error=error_message)
    
    action = tool_input.get("action", "")
    
    try:
        if progress_callback:
            progress_callback(f"Executing action: {action}")
        
        # Handle different actions
        if action == "screenshot":
            # Take a screenshot
            if progress_callback:
                progress_callback("Taking screenshot...")
            
            img_str = await take_screenshot()
            
            return ToolResult(
                output="Screenshot captured successfully",
                base64_image=img_str
            )
        
        elif action == "move_mouse":
            coordinates = tool_input.get("coordinates", [0, 0])
            if progress_callback:
                progress_callback(f"Moving mouse to {coordinates}")
            
            pyautogui.moveTo(coordinates[0], coordinates[1])
            return ToolResult(output=f"Mouse moved to {coordinates}")
        
        elif action == "left_button_press":
            coordinates = tool_input.get("coordinates", [0, 0])
            if progress_callback:
                progress_callback(f"Clicking at {coordinates}")
            
            pyautogui.click(coordinates[0], coordinates[1])
            return ToolResult(output=f"Mouse clicked at {coordinates}")
        
        elif action == "type_text":
            text = tool_input.get("text", "")
            if progress_callback:
                progress_callback(f"Typing text: {text}")
            
            pyautogui.write(text)
            return ToolResult(output=f"Typed text: {text}")
        
        elif action == "press_key":
            key = tool_input.get("text", "")
            if progress_callback:
                progress_callback(f"Pressing key: {key}")
            
            pyautogui.press(key)
            return ToolResult(output=f"Pressed key: {key}")
        
        elif action == "left_mouse_down":
            coordinates = tool_input.get("coordinates", [0, 0])
            if progress_callback:
                progress_callback(f"Mouse down at {coordinates}")
            
            pyautogui.mouseDown(coordinates[0], coordinates[1], button='left')
            return ToolResult(output=f"Mouse down at {coordinates}")
        
        elif action == "left_mouse_up":
            coordinates = tool_input.get("coordinates", [0, 0])
            if progress_callback:
                progress_callback(f"Mouse up at {coordinates}")
            
            pyautogui.mouseUp(coordinates[0], coordinates[1], button='left')
            return ToolResult(output=f"Mouse up at {coordinates}")
        
        elif action == "scroll":
            amount = tool_input.get("amount", 0)
            if progress_callback:
                progress_callback(f"Scrolling amount: {amount}")
            
            pyautogui.scroll(amount)
            return ToolResult(output=f"Scrolled amount: {amount}")
        
        elif action == "triple_click":
            coordinates = tool_input.get("coordinates", [0, 0])
            if progress_callback:
                progress_callback(f"Triple clicking at {coordinates}")
            
            pyautogui.tripleClick(coordinates[0], coordinates[1])
            return ToolResult(output=f"Triple clicked at {coordinates}")
        
        elif action == "wait":
            duration = tool_input.get("duration", 1.0)
            if progress_callback:
                progress_callback(f"Waiting for {duration} seconds")
            
            await asyncio.sleep(duration)
            return ToolResult(output=f"Waited for {duration} seconds")
        
        else:
            return ToolResult(error=f"Unknown action: {action}")
        
    except Exception as e:
        logger.error(f"Error executing computer action: {str(e)}")
        return ToolResult(error=f"Error executing action: {str(e)}")

if __name__ == "__main__":
    # Test the tool
    import sys
    import json
    
    async def test_action(action, **kwargs):
        tool_input = {"action": action, **kwargs}
        result = await execute_computer_tool(tool_input)
        if result.error:
            print(f"Error: {result.error}")
            return 1
        else:
            print(f"Output: {result.output}")
            if result.base64_image:
                print(f"Screenshot captured (base64 data available)")
            return 0
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        params = {}
        
        # Parse additional parameters
        for arg in sys.argv[2:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # Try to parse as JSON
                try:
                    params[key] = json.loads(value)
                except json.JSONDecodeError:
                    params[key] = value
        
        # Run the test
        exit_code = asyncio.run(test_action(action, **params))
        sys.exit(exit_code)
    else:
        print("Usage: python computer.py <action> [key=value ...]")
        print("Examples:")
        print("  python computer.py screenshot")
        print("  python computer.py move_mouse coordinates=[100,200]")
        print("  python computer.py type_text text=\"Hello, world!\"")
        sys.exit(1)