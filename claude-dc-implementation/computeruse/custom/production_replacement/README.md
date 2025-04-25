# Claude DC Custom Production Environment

This is a complete, custom-built replacement for the Claude DC production environment, with streaming capabilities as a core feature.

## Key Features

- **Streaming Responses**: Token-by-token streaming output for a more responsive experience
- **Tool Integration**: Seamless integration of tools during streaming
- **Progress Reporting**: Real-time progress updates during tool execution
- **Thinking Capabilities**: Support for Claude's thinking beta feature
- **Extended Output**: Support for larger response sizes
- **Modern UI**: Clean Streamlit interface with real-time updates
- **Robust Error Handling**: Comprehensive error handling and recovery mechanisms
- **Clean Architecture**: Well-organized codebase with clear separation of concerns

## Directory Structure

```
/
├── deploy.sh              - Deployment script
├── loop.py                - Main agent loop with streaming
├── streamlit.py           - UI component
├── models/
│   ├── __init__.py
│   └── tool_models.py     - Data models for tools
├── tools/
│   ├── __init__.py
│   ├── registry.py        - Tool registry
│   ├── bash.py            - Streaming bash tool
│   ├── edit.py            - Streaming file editor
│   └── computer.py        - Computer control tool
├── utils/
│   ├── __init__.py
│   ├── streaming.py       - Streaming utilities
│   └── error_handling.py  - Error handling utilities
└── tests/                 - Test suite
```

## Deployment Instructions

### Prerequisites

1. Make sure Python 3.10+ is installed
2. Install required packages: `pip install anthropic streamlit pyautogui pillow`
3. Ensure you have a valid Anthropic API key

### Deployment Steps

1. **Validate**: Run `./deploy.sh --validate-only` to validate without deploying.
2. **Deploy**: Run `./deploy.sh` to back up the current environment and deploy.
3. **Verify**: After deployment, verify the installation:
   ```bash
   cd /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo
   python -c 'import loop, streamlit; print("Import check passed")'
   ```
4. **Run**: Start the application:
   ```bash
   cd /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo
   streamlit run streamlit.py
   ```

### Rollback

If needed, restore from the backup:
```bash
cp -r /path/to/backup/* /home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/
```

## Core Components

### Agent Loop (loop.py)

The main agent loop integrates with Claude's API and provides:
- Token-by-token streaming
- Tool use during streaming
- Thinking capabilities
- Session state management
- Error handling and recovery

### Streamlit UI (streamlit.py)

The UI component provides:
- Real-time display of streaming responses
- Progress visualization for tool execution
- Thinking visualization
- Settings management
- Conversation history

### Tool Registry (tools/registry.py)

The registry manages all available tools:
- Tool definitions, executors, and validators
- Dynamic tool registration
- Tool discovery

### Streaming-Compatible Tools

Tools that support streaming include:
- **Bash Tool**: Execute shell commands with real-time output
- **File Editor**: View, create, and edit files with progress reporting

## Development Guidelines

When enhancing this implementation:

1. **Maintain Architecture**: Keep the clean separation of concerns
2. **Add Tests**: Include tests for new functionality
3. **Error Handling**: Ensure robust error handling
4. **Documentation**: Update documentation as needed
5. **Token Management**: Be mindful of token usage
6. **Streaming First**: New tools should support streaming

## Next Steps

1. **Enhancement Optimization**: Fine-tune streaming for optimal performance
2. **Additional Tools**: Add more streaming-compatible tools as needed
3. **Extended Output**: Use extended output beta for very long responses
4. **Prompt Caching**: Implement prompt caching beta for token efficiency