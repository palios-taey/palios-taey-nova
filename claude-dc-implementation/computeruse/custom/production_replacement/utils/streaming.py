"""
Utilities for streaming output and state management.

This module provides helpers for managing streaming state, buffers, and async operations.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger("streaming_utils")

class StreamBuffer:
    """
    Buffer for managing streaming content, with support for text and tool use.
    
    This class handles appending text and tool use events to create a coherent
    stream of content blocks for the conversation history.
    """
    
    def __init__(self):
        """Initialize an empty stream buffer."""
        self.content_blocks: List[Dict[str, Any]] = []
        self.current_block_index = -1
    
    def add_text(self, text: str):
        """
        Add a new text block to the buffer.
        
        Args:
            text: The initial text for the block
        """
        self.content_blocks.append({
            "type": "text",
            "text": text
        })
        self.current_block_index = len(self.content_blocks) - 1
    
    def append_text(self, text: str):
        """
        Append text to the most recent text block, or create a new one.
        
        Args:
            text: The text to append
        """
        # If there are no blocks or the last block is not a text block,
        # create a new text block
        if not self.content_blocks or self.content_blocks[-1]["type"] != "text":
            self.add_text(text)
        else:
            # Append to the existing text block
            self.content_blocks[-1]["text"] += text
    
    def add_tool_use(self, tool_name: str, tool_input: Dict[str, Any], tool_id: str = None):
        """
        Add a tool use block to the buffer.
        
        Args:
            tool_name: The name of the tool
            tool_input: The input parameters for the tool
            tool_id: Optional tool ID (generated if not provided)
        """
        # Generate a tool ID if not provided
        if tool_id is None:
            tool_id = f"tool_{uuid.uuid4()}"
        
        # Add the tool use block
        self.content_blocks.append({
            "type": "tool_use",
            "name": tool_name,
            "input": tool_input,
            "id": tool_id
        })
        self.current_block_index = len(self.content_blocks) - 1
    
    def add_tool_result(self, tool_id: str, content: List[Dict[str, Any]]):
        """
        Add a tool result block to the buffer.
        
        Args:
            tool_id: The ID of the tool use
            content: The result content
        """
        self.content_blocks.append({
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": content
        })
        self.current_block_index = len(self.content_blocks) - 1
    
    def get_content_blocks(self) -> List[Dict[str, Any]]:
        """
        Get all content blocks in the buffer.
        
        Returns:
            List of content blocks
        """
        return self.content_blocks
    
    def clear(self):
        """Clear the buffer."""
        self.content_blocks = []
        self.current_block_index = -1
    
    def __len__(self):
        """Get the number of content blocks in the buffer."""
        return len(self.content_blocks)

class ProgressTracker:
    """
    Tracks progress of long-running operations.
    
    This class provides utilities for tracking progress of tool execution
    and other long-running operations.
    """
    
    def __init__(self, total_steps: int = 100):
        """
        Initialize a progress tracker.
        
        Args:
            total_steps: The total number of steps in the operation
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.status = "initializing"
    
    def update(self, step: Optional[int] = None, status: Optional[str] = None):
        """
        Update the progress tracker.
        
        Args:
            step: The current step (if None, increments by 1)
            status: The current status
        """
        if step is not None:
            self.current_step = min(step, self.total_steps)
        else:
            self.current_step = min(self.current_step + 1, self.total_steps)
        
        if status is not None:
            self.status = status
    
    def get_progress(self) -> float:
        """
        Get the current progress as a percentage.
        
        Returns:
            Progress percentage (0.0 to 1.0)
        """
        return self.current_step / self.total_steps
    
    def get_status(self) -> str:
        """
        Get the current status.
        
        Returns:
            Status message
        """
        return self.status
    
    def is_complete(self) -> bool:
        """
        Check if the operation is complete.
        
        Returns:
            True if complete, False otherwise
        """
        return self.current_step >= self.total_steps