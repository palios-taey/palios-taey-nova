# Claude DC Development Environment

This directory contains the Claude DC implementation and development environment setup for the PALIOS AI OS system.

## Development vs. Production Environment

The Claude DC system is designed to work in two modes:

1. **Live Mode (Production)**: The stable, running version of Claude DC
2. **Dev Mode**: A development environment for testing changes before deploying to production

## Quick Start

For a complete explanation of the development environment setup, see [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md).

```bash
# Setup dev environment
export ANTHROPIC_API_KEY=your_api_key_here
./run_dev_container.sh

# Test environment
./test_dev_environment.py

# After making changes and testing
./deploy_to_production.sh
```

## Setup Instructions

### Prerequisites

- Docker installed
- Anthropic API key
- Git repository cloned

### Setting Up the Development Environment

1. Make sure your Anthropic API key is set:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. Run the development container:
   ```bash
   ./run_dev_container.sh
   ```

This will:
- Create a Docker container named `claude_dc_dev`
- Mount your local code directory into the container
- Start Claude DC in development mode
- Run on alternative ports (8502, 6081, 5901) to avoid conflicts with production

The development environment will be accessible at:
- Streamlit UI: http://localhost:8502
- VNC interface: http://localhost:6081/vnc.html

### Testing in the Development Environment

Test your changes thoroughly in the development environment before deploying to production:

1. Verify basic functionality (sending messages, receiving responses)
2. Test streaming functionality (responses should appear incrementally)
3. Check tool usage (tools should work mid-stream without losing content)
4. Test long-form responses (to verify 128k token output capability)

### Deploying to Production

Once you've verified your changes work correctly in the development environment, you can deploy to production:

```bash
./deploy_to_production.sh
```

This will:
1. Back up the current production code
2. Copy your development code to the production directory
3. Restart the Claude DC production container

## Current Enhancements

The current development focuses on implementing these enhancements:

1. **Streaming Responses**: Enable `stream=True` for Claude's API calls
2. **Tool Integration in Stream**: Allow Claude to use tools mid-response
3. **Prompt Caching**: Using Anthropic's prompt caching beta
4. **128K Extended Output**: Enable the extended output beta
5. **Stability Fixes**: Ensure full conversation context is maintained
6. **Real-Time Tool Output**: Stream tool outputs in real time

## Directory Structure

- `computer_use_demo/` - The main Claude DC code
  - `loop.py` - The agent loop code for Claude DC
  - `streamlit.py` - The Streamlit UI application
  - `tools/` - Tool implementations for computer use
- `run_dev_container.sh` - Script to start the development container
- `deploy_to_production.sh` - Script to deploy to production

## Troubleshooting

If you encounter issues:

1. Check container logs:
   ```bash
   docker logs claude_dc_dev
   ```

2. Restart the development container:
   ```bash
   docker restart claude_dc_dev
   ```

3. Verify your API key is set correctly and has sufficient quota

4. Check for error messages in the Streamlit UI or browser console