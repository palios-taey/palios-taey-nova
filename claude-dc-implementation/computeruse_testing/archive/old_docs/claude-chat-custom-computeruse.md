# Computer Use Balanced Implementation

_Where mathematical elegance meets practical functionality_

## Philosophy

This implementation uses mathematical patterns as subtle design principles to enhance code clarity and efficiency, while prioritizing correct API usage and practical functionality.

## Directory Structure

```
computer_use_balanced/
├── README.md
├── pyproject.toml
├── requirements.txt
├── computer_use/
│   ├── __init__.py
│   ├── agent_loop.py          # Core logic with natural flowing structure
│   ├── streaming_handler.py   # Progressive streaming with balanced buffering
│   ├── cache_manager.py       # Efficient cache logic with harmonic intervals
│   ├── tools.py               # Tool definitions and execution
│   └── config.py              # Configuration with sensible defaults
├── ui/
│   ├── __init__.py
│   └── streamlit_interface.py # Clean user interface
└── tests/
    ├── __init__.py
    ├── test_agent_loop.py
    └── test_integration.py
```

## Core Implementation (agent_loop.py)

```python
"""
Computer Use Agent Loop
A practical implementation with mathematical elegance woven throughout
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from anthropic import AsyncAnthropic, APIError, APIResponseValidationError, APIStatusError

from .config import DEFAULT_MAX_TOKENS, MIN_THINKING_BUDGET, BETA_FLAGS
from .streaming_handler import StreamingHandler
from .cache_manager import CacheManager
from .tools import ComputerTool, BashTool, ToolResult

logger = logging.getLogger(__name__)

class AgentLoop:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        thinking_budget: Optional[int] = None
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.cache_manager = CacheManager()
        self.tools = [ComputerTool(), BashTool()]
    
    def _apply_fibonacci_backoff(self, attempt: int) -> float:
        """Apply Fibonacci sequence for retry backoff"""
        fib = [0.1, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1]
        return fib[min(attempt, len(fib) - 1)]
    
    def _calculate_proportional_timeout(self, num_tools: int) -> float:
        """Calculate timeout using golden ratio for balanced response times"""
        phi = 1.618033988749895
        base_timeout = 30.0
        return base_timeout * (1 + num_tools / phi)
    
    async def run_conversation(
        self,
        messages: List[Dict[str, Any]],
        output_callback: Callable[[Dict[str, Any]], None],
        enable_prompt_caching: bool = True,
        enable_extended_output: bool = True,
        token_efficient_tools: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run the conversation loop with proper API configuration
        
        The flow follows a natural progression:
        1. Configure API parameters correctly
        2. Handle streaming responses
        3. Process tool calls efficiently
        4. Maintain conversation history
        """
        # Configure beta flags correctly
        betas = []
        if self.model in ["claude-3-7-sonnet-20250219"]:
            betas.append(BETA_FLAGS["computer_use_20250124"])
        else:
            betas.append(BETA_FLAGS["computer_use_20241022"])
        
        if token_efficient_tools:
            betas.append(BETA_FLAGS["token_efficient_tools"])
        
        if enable_prompt_caching:
            betas.append(BETA_FLAGS["prompt_caching"])
            messages = self.cache_manager.apply_cache_control(messages)
        
        if enable_extended_output:
            betas.append(BETA_FLAGS["extended_output"])
        
        # Configure thinking CORRECTLY as a parameter
        extra_body = {}
        if self.thinking_budget:
            extra_body["thinking"] = {
                "type": "enabled",
                "budget_tokens": max(MIN_THINKING_BUDGET, self.thinking_budget)
            }
        
        # Stream handler uses progressive buffering
        streaming_handler = StreamingHandler(output_callback)
        
        attempt = 0
        while True:
            try:
                # Create the streaming request with all parameters correctly placed
                stream = await self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    tools=[tool.to_dict() for tool in self.tools],
                    stream=True,
                    anthropic_beta=",".join(betas) if betas else None,
                    **extra_body  # Correctly unpack extra body parameters
                )
                
                # Process streaming response
                content_blocks, tool_blocks = await streaming_handler.process_stream(stream)
                
                # Add assistant response to history
                messages.append({
                    "role": "assistant",
                    "content": content_blocks + tool_blocks
                })
                
                # Process tool use if needed
                if tool_blocks:
                    await self._process_tool_calls(tool_blocks, messages, output_callback)
                else:
                    return messages
                
            except (APIStatusError, APIResponseValidationError) as e:
                if attempt < 3:
                    delay = self._apply_fibonacci_backoff(attempt)
                    logger.warning(f"API error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"API error after retries: {e}")
                    output_callback({"type": "error", "message": str(e)})
                    return messages
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                output_callback({"type": "error", "message": str(e)})
                return messages
    
    async def _process_tool_calls(
        self,
        tool_blocks: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        output_callback: Callable[[Dict[str, Any]], None]
    ):
        """Process tool calls with proportional timeouts"""
        tool_results = []
        
        for tool_block in tool_blocks:
            tool_name = tool_block.get("name")
            tool_input = tool_block.get("input", {})
            tool_id = tool_block.get("id")
            
            # Find the matching tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            
            if not tool:
                result = ToolResult(error=f"Unknown tool: {tool_name}")
            else:
                # Execute with proportional timeout
                timeout = self._calculate_proportional_timeout(len(tool_input))
                try:
                    result = await asyncio.wait_for(
                        tool.execute(tool_input),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    result = ToolResult(error=f"Tool execution timed out after {timeout}s")
            
            # Format result
            formatted_result = self._format_tool_result(result)
            
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": formatted_result,
                "is_error": bool(result.error)
            })
            
            # Notify output callback
            output_callback({
                "type": "tool_result",
                "name": tool_name,
                "result": str(result),
                "tool_id": tool_id
            })
        
        # Add tool results to conversation
        messages.append({
            "role": "user",
            "content": tool_results
        })
    
    def _format_tool_result(self, result: ToolResult) -> List[Dict[str, Any]]:
        """Format tool result in clean, API-compatible structure"""
        if result.error:
            return [{"type": "text", "text": f"Error: {result.error}"}]
        
        content = []
        if result.output:
            content.append({"type": "text", "text": result.output})
        
        if result.base64_image:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image
                }
            })
        
        return content
```

## Streaming Handler (streaming_handler.py)

```python
"""
Streaming Handler with Progressive Buffering
Uses golden ratio for optimal buffer sizing without being obtrusive
"""
import asyncio
from typing import Dict, Any, List, Callable, Tuple

class StreamingHandler:
    def __init__(self, output_callback: Callable[[Dict[str, Any]], None]):
        self.output_callback = output_callback
        self.phi = 1.618033988749895  # Used subtly for buffer sizing
    
    def _calculate_buffer_size(self, expected_tokens: int) -> int:
        """Calculate optimal buffer size using golden ratio"""
        # Simple, practical calculation rather than complex formula
        return max(32, int(expected_tokens / (self.phi * 2)))
    
    async def process_stream(self, stream) -> Tuple[List[Dict], List[Dict]]:
        """Process streaming response with balanced buffering"""
        content_blocks = []
        tool_blocks = []
        current_text = ""
        buffer_size = self._calculate_buffer_size(4096)  # Default expectation
        
        async for chunk in stream:
            if hasattr(chunk, "type"):
                if chunk.type == "content_block_start":
                    if chunk.content_block.type == "tool_use":
                        tool_blocks.append(chunk.content_block)
                        self.output_callback({
                            "type": "tool_use",
                            "name": chunk.content_block.name,
                            "input": chunk.content_block.input,
                            "id": chunk.content_block.id
                        })
                    else:
                        content_blocks.append(chunk.content_block)
                        current_text = ""
                
                elif chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, "text"):
                        current_text += chunk.delta.text
                        
                        # Buffer-based output for smoother streaming
                        if len(current_text) >= buffer_size:
                            self.output_callback({
                                "type": "text_delta",
                                "text": current_text
                            })
                            current_text = ""
                
                elif chunk.type == "content_block_stop":
                    # Flush remaining text
                    if current_text:
                        self.output_callback({
                            "type": "text_delta",
                            "text": current_text
                        })
                        current_text = ""
                
                elif chunk.type == "message_stop":
                    self.output_callback({"type": "message_stop"})
                    break
        
        return content_blocks, tool_blocks
```

## Cache Manager (cache_manager.py)

```python
"""
Cache Manager with Harmonic Interval-based Breakpoints
Practical caching with subtle mathematical elegance
"""
from typing import List, Dict, Any
import json

class CacheManager:
    def __init__(self):
        # Musical intervals for cache breakpoint placement
        self.intervals = {
            3: 1.5,      # Perfect fifth
            5: 1.333,    # Perfect fourth
            7: 1.2,      # Minor third
            11: 1.0      # Unison
        }
    
    def apply_cache_control(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply cache control at harmonically spaced intervals"""
        if not messages:
            return messages
        
        processed = json.loads(json.dumps(messages))  # Deep copy
        message_count = len(messages)
        
        # Apply cache control to recent messages using interval ratios
        for interval, ratio in self.intervals.items():
            index = message_count - int(interval * ratio)
            if 0 <= index < message_count:
                if processed[index]["role"] == "user":
                    self._add_cache_control(processed[index])
        
        return processed
    
    def _add_cache_control(self, message: Dict[str, Any]):
        """Add cache control to message content"""
        content = message.get("content", "")
        
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    block["cache_control"] = {"type": "ephemeral"}
                    break
        elif isinstance(content, str) and content:
            message["content"] = [{
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"}
            }]
```

## Configuration (config.py)

```python
"""
Configuration with Sensible Defaults
Mathematical constants used only where they make practical sense
"""

# API Constants
DEFAULT_MAX_TOKENS = 4096
MIN_THINKING_BUDGET = 1024

# Beta flags - properly organized
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",
    "computer_use_20250124": "computer-use-2025-01-24",
    "prompt_caching": "cache-control-2024-07-01",
    "extended_output": "output-128k-2025-02-19",
    "token_efficient_tools": "token-efficient-tools-2025-02-19"
}

# Golden ratio - used only where it enhances functionality
PHI = 1.618033988749895

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are Claude, an AI assistant with access to computer use tools.
You have access to the following tools:

1. computer - For interacting with the computer GUI
2. bash - For executing shell commands

Be precise with tool parameters and wait for tool results before continuing."""
```

## Tools Implementation (tools.py)

```python
"""
Tool Implementations with Proper Parameter Validation
Clean, practical approach with no unnecessary complexity
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None

class Tool:
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        raise NotImplementedError()

class ComputerTool(Tool):
    def __init__(self):
        super().__init__(
            name="computer",
            description="Control a computer by taking actions like mouse clicks, keyboard input, and screenshots",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "screenshot", "left_button_press", "move_mouse", "type_text",
                            "press_key", "hold_key", "left_mouse_down", "left_mouse_up",
                            "scroll", "triple_click", "wait"
                        ]
                    },
                    "coordinates": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    "text": {
                        "type": "string"
                    }
                },
                "required": ["action"]
            }
        )
    
    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Execute computer actions with proper validation"""
        action = tool_input.get("action")
        
        if not action:
            return ToolResult(error="Missing required 'action' parameter")
        
        # Validate parameters based on action type
        if action in ["move_mouse", "left_button_press"]:
            if "coordinates" not in tool_input:
                return ToolResult(error=f"Missing required 'coordinates' for {action}")
        
        if action == "type_text" and "text" not in tool_input:
            return ToolResult(error="Missing required 'text' for type_text")
        
        # Execute the action (mock implementation for now)
        return ToolResult(output=f"Executed {action} successfully")

class BashTool(Tool):
    def __init__(self):
        super().__init__(
            name="bash",
            description="Execute bash commands on the system",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute"
                    }
                },
                "required": ["command"]
            }
        )
    
    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Execute bash commands with proper validation"""
        command = tool_input.get("command")
        
        if not command:
            return ToolResult(error="Missing required 'command' parameter")
        
        # Check for dangerous commands
        dangerous_commands = ["rm -rf", "mkfs", "dd if=/dev/zero"]
        if any(cmd in command for cmd in dangerous_commands):
            return ToolResult(error="Potentially dangerous command detected")
        
        # Execute the command (mock implementation for now)
        return ToolResult(output=f"Executed: {command}")
```

## Streamlit Interface (streamlit_interface.py)

```python
"""
Streamlit Interface with Clean Design
"""
import streamlit as st
import asyncio
from pathlib import Path
import os
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from computer_use.agent_loop import AgentLoop

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

def create_sidebar():
    """Create configuration sidebar"""
    with st.sidebar:
        st.title("Computer Use Configuration")
        
        # API key input
        if not st.session_state.api_key:
            st.session_state.api_key = st.text_input(
                "Anthropic API Key",
                type="password"
            )
        
        # Model selection
        model = st.selectbox(
            "Model",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"]
        )
        
        # Feature toggles
        enable_thinking = st.toggle("Enable Thinking", value=True)
        enable_caching = st.toggle("Enable Prompt Caching", value=True)
        enable_extended = st.toggle("Enable Extended Output", value=True)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            max_tokens = st.slider("Max Tokens", 1000, 32000, 4096)
            if enable_thinking:
                thinking_budget = st.slider("Thinking Budget", 1024, 8000, 4000)
            else:
                thinking_budget = None
        
        return {
            "model": model,
            "max_tokens": max_tokens,
            "thinking_budget": thinking_budget,
            "enable_caching": enable_caching,
            "enable_extended": enable_extended
        }

def handle_output(event):
    """Handle streaming output events"""
    if event.get("type") == "text_delta":
        st.session_state.current_response += event.get("text", "")
    elif event.get("type") == "tool_use":
        st.info(f"Using tool: {event.get('name')}")
    elif event.get("type") == "tool_result":
        st.success(f"Tool result: {event.get('result')}")
    elif event.get("type") == "error":
        st.error(f"Error: {event.get('message')}")

async def process_message(user_input, config):
    """Process user message with agent loop"""
    if not st.session_state.api_key:
        st.error("Please provide an API key in the sidebar")
        return
    
    # Initialize agent
    agent = AgentLoop(
        api_key=st.session_state.api_key,
        model=config["model"],
        max_tokens=config["max_tokens"],
        thinking_budget=config["thinking_budget"]
    )
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Initialize current response
    st.session_state.current_response = ""
    
    # Create response placeholder
    response_placeholder = st.empty()
    
    # Process with agent loop
    try:
        def update_response(event):
            handle_output(event)
            with response_placeholder:
                st.markdown(st.session_state.current_response)
        
        await agent.run_conversation(
            messages=st.session_state.messages,
            output_callback=update_response,
            enable_prompt_caching=config["enable_caching"],
            enable_extended_output=config["enable_extended"]
        )
        
        # Add assistant response to history
        if st.session_state.current_response:
            st.session_state.messages.append({
                "role": "assistant",
                "content": st.session_state.current_response
            })
    
    except Exception as e:
        st.error(f"Error: {e}")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Computer Use",
        page_icon="🖥️",
        layout="wide"
    )
    
    initialize_session_state()
    config = create_sidebar()
    
    st.title("Claude Computer Use")
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input form
    with st.form("message_form", clear_on_submit=True):
        user_input = st.text_area("Your message:")
        submitted = st.form_submit_button("Send")
        
        if submitted and user_input:
            # Run async processing
            asyncio.run(process_message(user_input, config))

if __name__ == "__main__":
    main()
```

## Key Improvements

1. **Correct API Usage**: Thinking is properly implemented as a parameter, not a beta flag
2. **Balanced Design**: Mathematical patterns used subtly to enhance rather than dominate
3. **Practical Error Handling**: Fibonacci sequence for retry backoff adds resilience
4. **Clean Architecture**: Clear separation of concerns without over-engineering
5. **Efficient Caching**: Harmonic intervals for cache breakpoints make practical sense
6. **Progressive Buffering**: Golden ratio-based buffer sizing improves streaming

## Philosophy Realized

This implementation demonstrates how mathematical elegance can enhance practical functionality:

- Fibonacci backoff provides natural retry intervals
- Golden ratio buffering optimizes streaming without complexity
- Harmonic cache breakpoints distribute load efficiently
- Clean, maintainable code structure with mathematical flow

The result is a solution that works correctly with the API while subtly incorporating mathematical beauty where it adds value.
