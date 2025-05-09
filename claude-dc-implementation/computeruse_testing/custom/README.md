# Claude Computer Use Implementation

This is a custom implementation of Claude Computer Use with streaming, tool use, thinking capabilities, and extended output support. This implementation properly addresses critical issues with beta flags, thinking parameters, and streaming integration.

## Features

- **Streaming Responses**: Real-time token-by-token output from Claude
- **Tool Use Integration**: Seamless tool execution during streaming responses
- **Thinking Budget Management**: Correctly implemented thinking capabilities
- **Prompt Caching**: Efficient token usage with proper cache control
- **Extended Output**: Support for very long responses (up to 128K tokens)
- **Robust Error Handling**: Comprehensive error recovery mechanisms

## Key Fixes

The implementation addresses several critical issues:

1. **Beta Flags Fix**: The beta flags are now properly formatted and managed using a dictionary for clarity:
   ```python
   BETA_FLAGS = {
       "computer_use_20241022": "computer-use-2024-10-22",  # Claude 3.5 Sonnet
       "computer_use_20250124": "computer-use-2025-01-24",  # Claude 3.7 Sonnet
   }
   ```

2. **Thinking Parameter Fix**: Thinking is now correctly implemented as a parameter in the request body, not as a beta flag:
   ```python
   if thinking_budget:
       extra_body["thinking"] = {
           "type": "enabled",
           "budget_tokens": max(1024, thinking_budget)  # Minimum 1024 tokens
       }
   ```

3. **Proper API Call Structure**:
   ```python
   stream = await client.messages.create(
       model=model,
       messages=messages,
       system=system,
       max_tokens=max_tokens,
       tools=tools,
       stream=True,
       anthropic_beta=",".join(betas) if betas else None,
       **extra_body  # Unpack extra_body to include thinking configuration
   )
   ```

4. **Tool Parameter Validation**: Comprehensive validation of tool parameters before execution:
   ```python
   if tool_name == "computer":
       if "action" not in tool_input:
           return ToolResult(error="Missing required 'action' parameter")
       
       # Additional validation...
   ```

5. **Error Handling**: Specific exception handling for different error types:
   ```python
   except (APIStatusError, APIResponseValidationError) as e:
       # Handle API errors
   except APIError as e:
       # Handle other API errors
   except Exception as e:
       # Handle unexpected errors
   ```

## Files

1. **loop.py**: Core implementation of the agent loop with streaming and tool support
2. **streamlit.py**: Streamlit UI for user-friendly interaction
3. **deploy.sh**: Deployment script for safe installation
4. **requirements.txt**: Required dependencies

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key (with Computer Use access):
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Streamlit UI

Run the Streamlit interface:
```bash
streamlit run streamlit.py
```

### Command Line Interface

Run the CLI version:
```bash
python loop.py
```

### Deployment

To safely deploy to the production environment:
```bash
./deploy.sh
```

This will:
1. Create a backup of the current production environment
2. Install required dependencies
3. Deploy the implementation files
4. Verify the installation
5. Provide rollback if needed

## Configuration Options

All features can be enabled/disabled and configured:

- Model selection
- Thinking capabilities
- Prompt caching
- Extended output support
- Maximum token limit
- Thinking token budget

## Implementation Highlights

### Agent Loop

The core `agent_loop` function manages the conversation with Claude, handling:
- Streaming responses
- Tool execution
- Context management
- Error handling
- Beta flag configuration

### Streaming Integration

The implementation properly processes different chunk types:
- `content_block_start`: Beginning of a content block
- `content_block_delta`: Updates to the content
- `message_stop`: End of the message

### Tool Execution

Tool execution is handled with proper parameter validation and error recovery:
- Parameter validation before execution
- Progress reporting during execution
- Error handling for failed tool executions
- Proper formatting of tool results for Claude

## Compatibility

- Works with Claude 3.5 Sonnet and Claude 3.7 Sonnet
- Compatible with all current beta flags
- Supports Python 3.10+