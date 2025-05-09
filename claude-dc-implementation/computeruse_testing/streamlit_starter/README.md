# Claude DC Streaming Implementation Guide

## Overview

This guide outlines the correct implementation of streaming responses with tool use for Claude DC, focusing on key areas where previous implementations have failed. This implementation follows the Fibonacci Development Pattern principles, starting with the smallest functional components first.

## Recent Updates - APIProvider Compatibility

This implementation has been updated to address the error:

```
ImportError: cannot import name 'APIProvider' from 'computer_use_demo.loop'
```

The key changes include:
1. Added the `APIProvider` enum to maintain backward compatibility
2. Added a `sampling_loop` function that wraps the agent_loop functionality
3. Ensured all imports and function signatures match the original implementation

## Critical Implementation Requirements

1. **Beta Flags Handling**
   - Fixed common misunderstandings about beta flags for computer use and thinking
   - Implemented proper dictionary-based approach for beta flags

2. **Thinking Parameter Correction**
   - **CRITICAL FIX**: Thinking is NOT a beta flag
   - Must be implemented as a parameter in the request body (`extra_body["thinking"]`)
   - Minimum budget of 1024 tokens required

3. **Streaming with Tool Use Integration**
   - Stream support for large outputs (up to 128K tokens with extended output beta)
   - Tools must be properly validated before execution
   - Complete event handling for all streaming chunk types

## Key Reference Points

From `/computeruse/cache/cache-separate/fibonacci-development-pattern.md`:
- Implementation principles (lines 8-63): Start with smallest functional components
- Follows Golden Ratio proportions and error handling with Fibonacci backoff
- Focus on natural, balanced growth with manageable complexity at each stage

From `/computeruse/references/chatgpt-custom-computeruse.md`:
- Beta flag implementation (lines 25-29): Critical for 128K token support
- API call structure (lines 96-106): Shows proper beta flags and thinking setup
- Tool execution architecture (lines 42-85): Details step-by-step process

## Implementation Architecture

### Core Components

1. **Agent Loop (`loop.py`)**
   - Core streaming API integration
   - Complete tool execution workflow
   - Proper beta flags and thinking configuration

2. **Tool Definitions (`tools/`)**
   - Bash tool (`bash.py`) - For executing shell commands
   - Computer tool (`computer.py`) - For GUI interactions

3. **Streamlit Interface (`streamlit_app.py`)**
   - Real-time streaming display
   - Tool visualization support
   - Configuration options

## Key Implementation Details

### Beta Flags and Thinking Configuration

```python
# Beta flags for different tool versions
BETA_FLAGS = {
    "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
    "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
}

# Prompt caching flag
PROMPT_CACHING_FLAG = "cache-control-2024-07-01"

# Extended output flag
EXTENDED_OUTPUT_FLAG = "output-128k-2025-02-19"

# Configure thinking (NOT a beta flag, but a parameter in extra_body)
if thinking_budget:
    extra_body["thinking"] = {
        "type": "enabled",
        "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
    }
```

### API Call Structure

```python
# Call the API with streaming
response = await client.messages.create(
    model=model,
    messages=messages,
    system=system_prompt,
    max_tokens=max_tokens,
    tools=tools,
    stream=True,
    anthropic_beta=",".join(betas) if betas else None,
    **extra_body  # Unpack extra_body to include thinking configuration
)
```

### Streaming Event Handling

```python
async for chunk in stream:
    if hasattr(chunk, "type"):
        if chunk.type == "content_block_start":
            # Handle content block start
        elif chunk.type == "content_block_delta":
            # Handle content deltas
        elif chunk.type == "message_stop":
            # Handle message completion
```

## Step-by-Step Development Approach

Following the Fibonacci Development Pattern:

1. **Step 1 (Base Component)**: Implement core API integration with correct beta flags and thinking
2. **Step 1 (Base Component)**: Implement basic streaming support with proper event handling
3. **Step 2 (Integration)**: Add tool execution with proper parameter validation
4. **Step 3 (Enhancement)**: Implement the Streamlit UI with real-time updates
5. **Step 5 (Extension)**: Add extended capabilities (prompt caching, error handling)
8. **Step 8 (Refinement)**: Complete implementation with advanced features and optimizations

## Testing Strategy

1. Test the API configuration with minimal calls to verify beta flags and thinking setup
2. Test streaming without tools to validate the basic streaming mechanism
3. Test with simple tools to verify the tool execution flow
4. Test with complex scenarios to ensure robustness

## Implementation Files

This starter package includes:
- Core implementation files for streaming with tool use
- Base Streamlit UI for testing and demonstration
- Test scripts to validate the implementation
- Deployment script for easy installation

Start by examining `loop.py` for the core implementation, then review the tool implementations and Streamlit UI.

## Deployment Instructions

To deploy this implementation and fix the `ImportError`:

1. Run the deployment script:
   ```
   ./deploy.sh
   ```

   This script:
   - Creates a backup of your current environment
   - Copies the new implementation to the computer_use_demo directory
   - Installs required dependencies

2. Launch the Streamlit application:
   ```
   cd /home/computeruse/computer_use_demo
   streamlit run streamlit_app.py
   ```

## Compatibility Features

The implementation maintains compatibility by:

1. **APIProvider Enum**: Added to match the original implementation
   ```python
   class APIProvider(StrEnum):
       ANTHROPIC = "anthropic"
       BEDROCK = "bedrock"
       VERTEX = "vertex"
   ```

2. **sampling_loop Function**: Acts as a wrapper around agent_loop
   ```python
   async def sampling_loop(
       *,
       system_prompt_suffix: str = "",
       model: str,
       provider: APIProvider = APIProvider.ANTHROPIC,
       messages: List[Dict[str, Any]],
       # ... other parameters ...
   ) -> List[Dict[str, Any]]:
       # Call agent_loop with appropriate parameters
   ```

These changes ensure that existing code that relies on imports from computer_use_demo.loop will continue to work.