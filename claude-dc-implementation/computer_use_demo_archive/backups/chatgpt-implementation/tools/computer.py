"""Tool for controlling the computer (mouse, keyboard, screenshots)."""
import os
import asyncio
import base64
import io
from typing import Literal
from PIL import ImageGrab
from computer_use_demo.tools.base import BaseAnthropicTool
from computer_use_demo.types import ToolResult, CLIResult, ToolFailure, ToolError

# Define valid actions for the computer tool
Action = Literal[
    "mouse_move",
    "left_click",
    "left_click_drag",
    "key",
    "type",
    "screenshot",
    "cursor_position"
]

class ComputerTool20241022(BaseAnthropicTool):
    """Tool implementation for controlling the computer (2024-10-22 version)."""

    name = "computer"
    api_type = "computer_20241022"

    def __init__(self):
        # Prepare display environment and xdotool command prefix
        display_num = os.getenv("DISPLAY_NUM")
        if display_num is not None:
            self.display_num = int(display_num)
            self._display_prefix = f"DISPLAY=:{self.display_num} "
        else:
            self.display_num = None
            self._display_prefix = ""
        # Screen resolution must be provided via environment
        self.width = int(os.getenv("WIDTH") or 0)
        self.height = int(os.getenv("HEIGHT") or 0)
        assert self.width and self.height, "Environment variables WIDTH and HEIGHT must be set"
        # Base xdotool command (with display prefix if any)
        self.xdotool = f"{self._display_prefix}xdotool"

    def to_params(self) -> dict:
        return {
            "name": "computer",
            "type": "computer_20241022",
            "description": "Control the computer's GUI (mouse, keyboard, screenshots).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The computer control action to perform.",
                        "enum": [
                            "mouse_move", "left_click", "left_click_drag",
                            "key", "type", "screenshot", "cursor_position"
                        ]
                    },
                    "coordinate": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Coordinates [x,y] for mouse actions (required for 'mouse_move' and 'left_click_drag')."
                    },
                    "text": {
                        "type": "string",
                        "description": "Text input for keyboard actions (required for 'key' or 'type')."
                    }
                },
                "required": ["action"]
            }
        }

    async def __call__(
        self, *, action: Action, coordinate: tuple[int, int] = None, text: str = None, **kwargs
    ) -> ToolResult:
        # Execute the requested action
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None or not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
                raise ToolError(f"coordinate is required for action '{action}'")
            x, y = int(coordinate[0]), int(coordinate[1])
            if x < 0 or y < 0:
                raise ToolError("Coordinates must be non-negative")
            if action == "mouse_move":
                cmd = f"{self.xdotool} mousemove --sync {x} {y}"
            else:  # left_click_drag
                cmd = f"{self.xdotool} mousedown 1 mousemove --sync {x} {y} mouseup 1"
            return await self._run_shell_command(cmd)

        elif action == "left_click":
            cmd = f"{self.xdotool} click 1"
            return await self._run_shell_command(cmd)

        elif action == "key":
            if not text:
                raise ToolError("text is required for 'key' action")
            cmd = f"{self.xdotool} key -- {text}"
            return await self._run_shell_command(cmd)

        elif action == "type":
            if not text:
                raise ToolError("text is required for 'type' action")
            # Type the text in smaller chunks to avoid overflow
            result = ToolResult()
            chunk_size = 50
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                # Quote the chunk for shell safety (simple approach; may need refinement for special chars)
                cmd = f'{self.xdotool} type -- "{chunk}"'
                part = await self._run_shell_command(cmd, take_screenshot=False)
                result = result + part if result else part
            return result

        elif action == "screenshot":
            return await self._take_screenshot()

        elif action == "cursor_position":
            cmd = f"{self.xdotool} querymouse"
            return await self._run_shell_command(cmd, take_screenshot=False)

        else:
            return ToolFailure(error=f"Unknown action: {action}")

    async def _run_shell_command(self, command: str, take_screenshot: bool = True) -> ToolResult:
        """Run a shell command and return its output (and optionally a screenshot) as a ToolResult."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
        except Exception as e:
            return ToolFailure(error=f"Failed to run command: {e}")

        output_text = stdout.decode('utf-8', errors='ignore') if stdout else ""
        error_text = stderr.decode('utf-8', errors='ignore') if stderr else ""

        result = ToolResult()
        if output_text:
            result = result + CLIResult(output=output_text)
        if error_text:
            result = result + ToolFailure(error=error_text)
        if take_screenshot:
            screenshot_result = await self._take_screenshot()
            result = result + screenshot_result if screenshot_result else result
        return result

    async def _take_screenshot(self) -> ToolResult:
        """Capture the current screen and return a ToolResult containing the image."""
        try:
            image = await asyncio.to_thread(ImageGrab.grab)
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            img_bytes = buf.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return ToolResult(base64_image=img_base64)
        except Exception as e:
            return ToolFailure(error=f"Screenshot failed: {e}")

