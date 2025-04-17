from typing import Any, Literal
import os, base64, subprocess
from .base import BaseAnthropicTool
from .types import ToolResult, CLIResult, ToolError

class ComputerTool20250124(BaseAnthropicTool):
    """A tool to simulate computer screen, mouse, and keyboard actions."""
    api_type: Literal["computer_20250124"] = "computer_20250124"
    name:    Literal["computer"] = "computer"

    def __init__(self):
        # Load screen dimensions from environment for coordinate scaling
        self.width = int(os.getenv("WIDTH") or 0)
        self.height = int(os.getenv("HEIGHT") or 0)
        self.display = os.getenv("DISPLAY") or ":0"
        super().__init__()

    def to_params(self) -> Any:
        return {"type": self.api_type, "name": self.name}

    async def __call__(self, action: str, **kwargs) -> Any:
        # Dispatch to the appropriate helper method based on the action.
        # Supported actions might include: "mouse_move", "left_click", "right_click", "type", "key", "screenshot", etc.
        try:
            if action == "mouse_move":
                x = kwargs.get("x"); y = kwargs.get("y")
                if x is None or y is None:
                    raise ToolError("x and y coordinates are required for mouse_move")
                # Use a system tool like xdotool or cliclick to move mouse
                return await self.shell(f"xdotool mousemove --sync {x} {y}")
            elif action == "left_click":
                return await self.shell("xdotool click 1")
            elif action == "right_click":
                return await self.shell("xdotool click 3")
            elif action == "key":
                key_name = kwargs.get("key")
                if not key_name:
                    raise ToolError("key name is required for key action")
                return await self.shell(f"xdotool key {key_name}")
            elif action == "type":
                text = kwargs.get("text")
                if text is None:
                    raise ToolError("text is required for type action")
                # Simulate typing by chunking the text into keystrokes to avoid flooding
                typed = []
                for chunk in self._chunk_text(str(text), chunk_size=10):
                    await self.shell(f"xdotool type --delay 1 '{chunk}'", take_screenshot=False)
                    typed.append(chunk)
                # After typing, optionally take a screenshot of the result
                # (We won't combine partial outputs here, as typing typically has no direct output)
                return ToolResult(system=f'typed: {"".join(typed)}')
            elif action == "screenshot":
                # Take a screenshot and return as base64 image
                image_data = self._capture_screenshot()
                return ToolResult(base64_image=image_data)
            else:
                raise ToolError(f"Unknown action: {action}")
        except ToolError as e:
            # Propagate ToolError to be handled by the framework (it will be turned into a ToolResult with error)
            raise

    async def shell(self, command: str, take_screenshot: bool = True) -> ToolResult:
        """Execute a shell command for computer control (non-interactive, one-off command)."""
        # Run command and capture output
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"DISPLAY": self.display, **os.environ}  # ensure DISPLAY is set for GUI commands
        )
        out, err = await proc.communicate()
        output_text = out.decode(errors="ignore").strip()
        error_text = err.decode(errors="ignore").strip()
        # Optionally capture a screenshot after the command (to give visual feedback to Claude)
        img_data = None
        if take_screenshot:
            img_data = self._capture_screenshot()
        # Return a ToolResult with any text output, error, and image if captured
        return ToolResult(output=output_text if output_text else None,
                          error=error_text if error_text else None,
                          base64_image=img_data)

    def _capture_screenshot(self) -> str:
        """Capture a screenshot of the current screen and return as base64 string."""
        # Use `import -window root` (ImageMagick) or `xwd` and convert to capture the screen
        # Here we'll use a simple xwd + convert pipeline for demonstration:
        try:
            subprocess.run(["xwd", "-root", "-out", "/tmp/screenshot.xwd"], check=True)
            subprocess.run(["convert", "/tmp/screenshot.xwd", "-resize", f"{self.width}x{self.height}", "/tmp/screenshot.png"], check=True)
            with open("/tmp/screenshot.png", "rb") as f:
                image_bytes = f.read()
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            # If screenshot fails, return an error message in the output
            raise ToolError(f"Screenshot failed: {e}")

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """Utility to split text into smaller chunks for typing simulation."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# (If there was an older version of ComputerTool, it would similarly subclass this new class, 
# e.g., ComputerTool20241022 inheriting ComputerTool20250124 and just overriding api_type.)

