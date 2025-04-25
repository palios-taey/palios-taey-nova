"""
Computer tool for GUI interactions.

This module provides a tool for interacting with the computer GUI, including
taking screenshots, mouse actions, and keyboard input.
"""

import logging
import time
import base64
import asyncio
from typing import Dict, Any, Optional, Tuple
import os
import sys
from pathlib import Path

from models.tool_models import ToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("computer_tool")

# Check for pyautogui dependency
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Enable failsafe for safety
    HAS_PYAUTOGUI = True
except ImportError:
    logger.warning("pyautogui not installed. Computer tool will operate in mock mode.")
    HAS_PYAUTOGUI = False

# Check for PIL dependency for screenshot handling
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    logger.warning("PIL not installed. Screenshot functionality will be limited.")
    HAS_PIL = False

def validate_computer_parameters(tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate computer tool parameters.
    
    Args:
        tool_input: The input parameters
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check for required action parameter
    if "action" not in tool_input:
        return False, "Missing required 'action' parameter"
    
    action = tool_input.get("action")
    
    # Validate action parameter
    valid_actions = [
        "screenshot", "left_button_press", "move_mouse", "type_text",
        "press_key", "hold_key", "left_mouse_down", "left_mouse_up",
        "scroll", "triple_click", "wait"
    ]
    
    if action not in valid_actions:
        return False, f"Invalid action: {action}. Valid actions: {', '.join(valid_actions)}"
    
    # Validate parameters based on action
    if action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up", "triple_click"]:
        if "coordinates" not in tool_input:
            return False, f"Missing required 'coordinates' parameter for {action}"
        
        coordinates = tool_input.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            return False, "Invalid coordinates format. Expected [x, y]"
        
        try:
            # Ensure coordinates are integers
            x, y = int(coordinates[0]), int(coordinates[1])
        except (ValueError, TypeError):
            return False, "Coordinates must be integers"
    
    elif action == "type_text":
        if "text" not in tool_input:
            return False, "Missing required 'text' parameter for type_text"
        
        text = tool_input.get("text")
        if not isinstance(text, str):
            return False, "Text must be a string"
    
    elif action == "press_key" or action == "hold_key":
        if "text" not in tool_input:
            return False, f"Missing required 'text' parameter for {action}"
        
        key = tool_input.get("text")
        if not isinstance(key, str):
            return False, "Key must be a string"
    
    elif action == "wait":
        duration = tool_input.get("duration", 1.0)
        try:
            duration = float(duration)
            if duration < 0 or duration > 10:
                return False, "Duration must be between 0 and 10 seconds"
        except (ValueError, TypeError):
            return False, "Duration must be a number"
    
    elif action == "scroll":
        if "scroll_direction" not in tool_input:
            return False, "Missing required 'scroll_direction' parameter for scroll"
        
        direction = tool_input.get("scroll_direction")
        if direction not in ["up", "down"]:
            return False, "Scroll direction must be 'up' or 'down'"
        
        amount = tool_input.get("scroll_amount", 3)
        try:
            amount = int(amount)
            if amount < 1 or amount > 10:
                return False, "Scroll amount must be between 1 and 10"
        except (ValueError, TypeError):
            return False, "Scroll amount must be an integer"
    
    return True, "Parameters valid"

async def execute_computer(tool_input: Dict[str, Any]) -> ToolResult:
    """
    Execute a computer action.
    
    Args:
        tool_input: The input parameters
        
    Returns:
        ToolResult with the operation result
    """
    # Extract action from input
    action = tool_input.get("action")
    
    logger.info(f"Executing computer action: {action}")
    
    # Check if pyautogui is available
    if not HAS_PYAUTOGUI and action != "screenshot":
        logger.warning(f"PyAutoGUI not available. Using mock implementation for {action}")
        return ToolResult(output=f"Mock execution of {action} (PyAutoGUI not available)")
    
    try:
        # Execute the appropriate action
        if action == "screenshot":
            return await take_screenshot()
        
        elif action in ["move_mouse", "left_button_press", "left_mouse_down", "left_mouse_up", "triple_click"]:
            coordinates = tool_input.get("coordinates", [0, 0])
            return await mouse_action(action, coordinates)
        
        elif action == "type_text":
            text = tool_input.get("text", "")
            return await type_text(text)
        
        elif action in ["press_key", "hold_key"]:
            key = tool_input.get("text", "")
            return await keyboard_action(action, key)
        
        elif action == "wait":
            duration = float(tool_input.get("duration", 1.0))
            return await wait_action(duration)
        
        elif action == "scroll":
            direction = tool_input.get("scroll_direction", "down")
            amount = int(tool_input.get("scroll_amount", 3))
            return await scroll_action(direction, amount)
        
        else:
            return ToolResult(error=f"Unsupported action: {action}")
    
    except Exception as e:
        logger.error(f"Error executing computer action: {str(e)}")
        return ToolResult(error=f"Error executing {action}: {str(e)}")

async def take_screenshot() -> ToolResult:
    """
    Take a screenshot of the current screen.
    
    Returns:
        ToolResult with base64-encoded image
    """
    if HAS_PYAUTOGUI and HAS_PIL:
        try:
            # Take screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return ToolResult(output="Screenshot taken successfully", base64_image=base64_image)
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ToolResult(error=f"Error taking screenshot: {str(e)}")
    else:
        logger.warning("Screenshot functionality not available (missing PyAutoGUI or PIL)")
        return ToolResult(output="Mock screenshot taken (PyAutoGUI or PIL not available)")

async def mouse_action(action: str, coordinates: List[int]) -> ToolResult:
    """
    Perform a mouse action.
    
    Args:
        action: The mouse action to perform
        coordinates: The x,y coordinates for the action
        
    Returns:
        ToolResult with status
    """
    try:
        x, y = int(coordinates[0]), int(coordinates[1])
        
        if action == "move_mouse":
            pyautogui.moveTo(x, y)
            return ToolResult(output=f"Moved mouse to coordinates [{x}, {y}]")
        
        elif action == "left_button_press":
            pyautogui.click(x, y)
            return ToolResult(output=f"Clicked at coordinates [{x}, {y}]")
        
        elif action == "left_mouse_down":
            pyautogui.mouseDown(x, y, button='left')
            return ToolResult(output=f"Mouse down at coordinates [{x}, {y}]")
        
        elif action == "left_mouse_up":
            pyautogui.mouseUp(x, y, button='left')
            return ToolResult(output=f"Mouse up at coordinates [{x}, {y}]")
        
        elif action == "triple_click":
            pyautogui.tripleClick(x, y)
            return ToolResult(output=f"Triple-clicked at coordinates [{x}, {y}]")
        
        else:
            return ToolResult(error=f"Unsupported mouse action: {action}")
    
    except Exception as e:
        logger.error(f"Error performing mouse action: {str(e)}")
        return ToolResult(error=f"Error performing {action}: {str(e)}")

async def type_text(text: str) -> ToolResult:
    """
    Type text using the keyboard.
    
    Args:
        text: The text to type
        
    Returns:
        ToolResult with status
    """
    try:
        pyautogui.typewrite(text)
        return ToolResult(output=f"Typed text: {text}")
    except Exception as e:
        logger.error(f"Error typing text: {str(e)}")
        return ToolResult(error=f"Error typing text: {str(e)}")

async def keyboard_action(action: str, key: str) -> ToolResult:
    """
    Perform a keyboard action.
    
    Args:
        action: The keyboard action to perform
        key: The key to press or hold
        
    Returns:
        ToolResult with status
    """
    try:
        if action == "press_key":
            pyautogui.press(key)
            return ToolResult(output=f"Pressed key: {key}")
        
        elif action == "hold_key":
            pyautogui.keyDown(key)
            await asyncio.sleep(0.5)  # Hold for half a second
            pyautogui.keyUp(key)
            return ToolResult(output=f"Held key: {key}")
        
        else:
            return ToolResult(error=f"Unsupported keyboard action: {action}")
    
    except Exception as e:
        logger.error(f"Error performing keyboard action: {str(e)}")
        return ToolResult(error=f"Error performing {action}: {str(e)}")

async def wait_action(duration: float) -> ToolResult:
    """
    Wait for a specified duration.
    
    Args:
        duration: The duration to wait in seconds
        
    Returns:
        ToolResult with status
    """
    try:
        # Clamp duration between 0 and 10 seconds for safety
        duration = max(0, min(10, duration))
        await asyncio.sleep(duration)
        return ToolResult(output=f"Waited for {duration} seconds")
    except Exception as e:
        logger.error(f"Error during wait: {str(e)}")
        return ToolResult(error=f"Error during wait: {str(e)}")

async def scroll_action(direction: str, amount: int) -> ToolResult:
    """
    Scroll the mouse wheel.
    
    Args:
        direction: The scroll direction ("up" or "down")
        amount: The amount to scroll
        
    Returns:
        ToolResult with status
    """
    try:
        # Clamp amount between 1 and 10 for safety
        amount = max(1, min(10, amount))
        
        # Convert direction to clicks (negative for up, positive for down)
        clicks = amount if direction == "down" else -amount
        
        pyautogui.scroll(clicks)
        return ToolResult(output=f"Scrolled {direction} by {amount} units")
    except Exception as e:
        logger.error(f"Error scrolling: {str(e)}")
        return ToolResult(error=f"Error scrolling: {str(e)}")

# Test function for direct execution
async def test_computer_tool():
    """Test the computer tool."""
    print("\nTesting computer tool...\n")
    
    # Test screenshot
    print("Taking screenshot...")
    result = await execute_computer({"action": "screenshot"})
    
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Output: {result.output}")
        if result.base64_image:
            print(f"Screenshot captured: {len(result.base64_image)} bytes")
    
    # Test mouse movement
    print("\nMoving mouse...")
    result = await execute_computer({"action": "move_mouse", "coordinates": [100, 100]})
    
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Output: {result.output}")
    
    # Test wait action
    print("\nWaiting...")
    result = await execute_computer({"action": "wait", "duration": 1.0})
    
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Output: {result.output}")

if __name__ == "__main__":
    asyncio.run(test_computer_tool())