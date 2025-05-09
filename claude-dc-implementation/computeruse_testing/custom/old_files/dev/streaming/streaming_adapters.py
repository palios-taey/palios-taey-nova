"""
Streaming adapters for Claude DC tools.

This module provides adapters to connect various tool implementations to the
streaming agent loop, ensuring proper integration and state management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List, Tuple

from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dc_streaming_adapters")

# Add file handler for streaming adapter logs
log_dir = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dev/streaming/logs")
log_dir.mkdir(exist_ok=True, parents=True)
file_handler = logging.FileHandler(log_dir / "dc_streaming_adapters.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Import our streaming bash implementation
try:
    from bash_streaming import dc_execute_bash_tool_streaming, dc_process_streaming_output
except ImportError:
    logger.error("Could not import bash_streaming module. Make sure it's in the Python path.")
    # Create placeholder functions
    async def dc_execute_bash_tool_streaming(*args, **kwargs):
        yield "Error: bash_streaming module not available"
    
    async def dc_process_streaming_output(*args, **kwargs):
        return {"error": "bash_streaming module not available"}

class StreamingToolAdapter:
    """
    Adapter for connecting streaming-enabled tools to the streaming agent loop.
    
    This class provides a standard interface for all streaming tools, handling
    state management, progress tracking, and tool execution.
    """
    
    def __init__(self):
        self.logger = logger
        self.tool_state = {}
        self.active_tools = {}
    
    async def execute_tool_streaming(
        self, 
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_id: str,
        on_progress: Optional[Callable[[str, float], None]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute a tool with streaming output.
        
        Args:
            tool_name: The name of the tool to execute
            tool_input: The tool input parameters
            tool_id: The unique ID for this tool use
            on_progress: Optional callback for progress reporting
            
        Yields:
            Tool output chunks as they become available
        """
        self.logger.info(f"Executing streaming tool: {tool_name}")
        
        # Track the active tool
        self.active_tools[tool_id] = {
            "tool_name": tool_name,
            "start_time": asyncio.get_event_loop().time(),
            "status": "running",
            "progress": 0.0
        }
        
        # Define progress callback
        async def progress_callback(message: str, progress: float):
            self.active_tools[tool_id]["progress"] = progress
            self.active_tools[tool_id]["status"] = message
            if on_progress:
                await on_progress(message, progress)
        
        try:
            # Execute the appropriate tool based on name
            if tool_name == "dc_bash":
                # Use the bash streaming implementation
                self.logger.info(f"Executing bash command: {tool_input.get('command', 'unknown')}")
                async for chunk in dc_execute_bash_tool_streaming(tool_input, progress_callback):
                    yield chunk
            
            elif tool_name == "dc_str_replace_editor":
                # File operations tool (to be implemented)
                self.logger.warning("File operations streaming not yet implemented")
                yield "File operations streaming not yet implemented."
                await progress_callback("Not implemented", 1.0)
            
            elif tool_name == "dc_computer" and tool_input.get("action") == "screenshot":
                # Screenshot tool (to be implemented)
                self.logger.warning("Screenshot streaming not yet implemented")
                yield "Screenshot streaming not yet implemented."
                await progress_callback("Not implemented", 1.0)
            
            else:
                # Unknown tool
                error_message = f"Unknown tool or unsupported action: {tool_name}"
                self.logger.error(error_message)
                yield f"Error: {error_message}"
                await progress_callback("Error", 1.0)
        
        except Exception as e:
            # Handle execution errors
            error_message = f"Error executing {tool_name}: {str(e)}"
            self.logger.error(error_message)
            yield f"Error: {error_message}"
            if on_progress:
                await progress_callback("Error", 1.0)
        
        finally:
            # Update tool status to completed
            if tool_id in self.active_tools:
                self.active_tools[tool_id]["status"] = "completed"
                self.active_tools[tool_id]["progress"] = 1.0
                
                # Calculate execution time
                start_time = self.active_tools[tool_id]["start_time"]
                execution_time = asyncio.get_event_loop().time() - start_time
                self.logger.info(f"Tool {tool_name} executed in {execution_time:.2f} seconds")
    
    def get_active_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active tools."""
        return self.active_tools.copy()
    
    def get_tool_status(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a specific tool."""
        return self.active_tools.get(tool_id)

# Create a singleton instance for global use
streaming_adapter = StreamingToolAdapter()

# Utility functions to simplify tool execution
async def execute_streaming_bash(
    command: str,
    on_progress: Optional[Callable[[str, float], None]] = None
) -> AsyncGenerator[str, None]:
    """
    Execute a bash command with streaming output.
    
    Args:
        command: The bash command to execute
        on_progress: Optional progress callback
        
    Yields:
        Command output chunks as they become available
    """
    tool_input = {"command": command}
    tool_id = f"bash_{asyncio.get_event_loop().time()}"
    
    async for chunk in streaming_adapter.execute_tool_streaming(
        tool_name="dc_bash",
        tool_input=tool_input,
        tool_id=tool_id,
        on_progress=on_progress
    ):
        yield chunk

# Demo function for testing
async def demo_streaming_adapters():
    """Demo function to test the streaming adapters implementation."""
    print("\nTesting streaming adapters\n")
    
    # Define a progress callback
    async def progress_callback(message, progress):
        print(f"\r[Progress: {message} - {progress:.0%}]", end="", flush=True)
    
    # Test bash command
    print("Executing bash command...")
    async for chunk in execute_streaming_bash(
        "ls -la /home/computeruse",
        on_progress=progress_callback
    ):
        print(chunk, end="", flush=True)
    
    print("\n\nActive tools info:")
    print(streaming_adapter.get_active_tools())
    
    print("\nDone!")

# Entry point for direct script execution
if __name__ == "__main__":
    asyncio.run(demo_streaming_adapters())