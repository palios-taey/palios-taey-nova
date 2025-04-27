"""
Data models for tools and conversation elements.

This module provides all the data structures needed for tool execution,
conversation history, and session management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, TypedDict, Callable, Awaitable


@dataclass
class ToolResult:
    """
    Represents the result of a tool execution.
    
    Attributes:
        output: The tool's text output (if successful)
        error: Error message (if failed)
        base64_image: Base64-encoded image data (for screenshot tool)
        system: System messages for debugging
    """
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    system: Optional[str] = None
    
    def __bool__(self):
        """Returns True if any result field is populated."""
        return any([self.output, self.error, self.base64_image])


@dataclass
class ToolInfo:
    """
    Information about a tool in the registry.
    
    Attributes:
        definition: The tool definition for Claude API
        executor: Function that executes the tool
        validator: Function that validates tool parameters
        streaming: Whether the tool supports streaming
    """
    definition: Dict[str, Any]
    executor: Callable[[Dict[str, Any], Optional[Callable]], Awaitable[ToolResult]]
    validator: Callable[[Dict[str, Any]], tuple[bool, str]]
    streaming: bool = False


class Message(TypedDict):
    """
    A message in the conversation history.
    
    Attributes:
        role: The role of the message sender ("user", "assistant", "system")
        content: The content of the message
    """
    role: str
    content: Union[str, List[Dict[str, Any]]]


@dataclass
class StreamItem:
    """
    An item in the streaming buffer.
    
    Attributes:
        type: The type of item ("text", "tool_use", etc.)
        content: The content of the item
    """
    type: str
    content: Any


@dataclass
class SessionState:
    """
    Represents the state of a streaming session.
    
    Attributes:
        session_id: Unique identifier for the session
        is_streaming: Whether streaming is active
        is_interrupted: Whether streaming was interrupted
        active_tools: Currently active tools
        stream_buffer: Buffer for streaming content
    """
    session_id: str
    is_streaming: bool = False
    is_interrupted: bool = False
    active_tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    conversation_history: List[Message] = field(default_factory=list)


@dataclass
class StreamingConfig:
    """
    Configuration for streaming behavior.
    
    Attributes:
        enable_streaming: Whether streaming is enabled
        enable_thinking: Whether thinking is enabled
        thinking_budget: Token budget for thinking
        max_tokens: Maximum tokens in response
        model: Claude model to use
    """
    enable_streaming: bool = True
    enable_thinking: bool = True
    thinking_budget: int = 4000
    max_tokens: int = 16000
    model: str = "claude-3-7-sonnet-20240425"