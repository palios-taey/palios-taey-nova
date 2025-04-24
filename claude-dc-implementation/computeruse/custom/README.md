# Claude Custom Agent - MVP Implementation

This is a custom implementation of Claude Computer Use, focused on the core MVP features:
- Streaming responses
- Tool use integration
- Thinking token budget

## Features

- **Streaming API Integration**: Display Claude's responses token-by-token in real-time
- **Tool Use During Streaming**: Allow Claude to use tools mid-response without interruption
- **Thinking Token Budget**: Configure extended thinking for complex reasoning tasks
- **Prompt Caching**: Optimize token usage with cache control for multi-turn conversations
- **Extended Output**: Support for long responses (up to 128k tokens)
- **UI Integration**: Simple Streamlit interface for interacting with Claude
- **CLI Mode**: Command-line interface for running in terminal

## Getting Started

### Prerequisites

- Python 3.10+
- Anthropic API key with Computer Use access

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Running the Application

#### CLI Mode

Run the CLI version:

```bash
python main.py --cli
```

#### UI Mode

Run the Streamlit UI:

```bash
python main.py --ui
```

Or directly:

```bash
streamlit run ui.py
```

## Architecture

- **agent_loop.py**: Core implementation with streaming, tool use, and thinking integration
- **ui.py**: Streamlit UI for interactive use
- **main.py**: Entry point with CLI and UI options

## Configuration

The implementation supports configuring:

- Model selection
- Streaming mode
- Thinking token budget
- Prompt caching
- Extended output
- Maximum token limit

## Tools

Currently implemented:

- **Computer Use**: Basic computer control with screenshot, mouse, and keyboard actions
- **Bash**: Execute shell commands

## Development

To add new tools or features, extend the agent_loop.py file with additional tool definitions and implementations.

For UI customization, modify the ui.py file to add new components or change the layout.