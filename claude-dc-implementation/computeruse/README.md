# DCCC Integration Project

This project contains the integration framework and documentation for implementing streaming capabilities in Claude DC using the official Anthropic computer-use-demo as a foundation.

## Quick Start

1. Launch the official Anthropic container:
   ```bash
   cd /home/jesse/projects/palios-taey-nova
   ./current-execution-status/claude-integration/launch_computer_use.sh
   ```

2. Get the container ID:
   ```bash
   docker ps
   ```

3. Run the integration script:
   ```bash
   ./claude-dc-implementation/computeruse/run_integrated_dccc.sh [container_id]
   ```

4. Access the UI:
   - Integrated UI: http://localhost:8501
   - Base UI: http://localhost:8080
   - VNC: http://localhost:6080

## Project Structure

```
/computeruse/
  ├── docs/                    # Documentation
  │   ├── DCCC_CLAUDE_DC_GUIDE.md      # Guide for Claude DC
  │   ├── DCCC_CLAUDE_CODE_GUIDE.md    # Guide for Claude Code
  │   ├── DCCC_INTEGRATION_PLAN.md     # Integration plan
  │   └── DCCC_TECHNICAL_REFERENCE.md  # Technical reference
  │
  ├── integration_framework.py # Core integration bridge
  ├── integrated_streamlit.py  # Enhanced UI with streaming
  ├── rosetta_stone.py         # AI-to-AI communication protocol
  ├── continuity.py            # Streamlit state persistence
  │
  ├── custom_implementation/   # Our custom streaming implementation
  │   ├── tools/               # Custom tool implementations
  │   ├── unified_streaming_loop.py    # Streaming agent loop
  │   └── streaming_enhancements.py    # Streaming utilities
  │
  ├── references/              # Reference documentation
  │   └── claude-dc-setup-prompt.md    # Setup prompt for Claude DC
  │
  ├── run_integrated_dccc.sh   # Script to run the integration
  └── clean_directories.sh     # Script to organize directories
```

## Documentation

### For Claude DC

- `DCCC_CLAUDE_DC_GUIDE.md`: Guide for Claude DC's role in the integration
- `DCCC_INTEGRATION_PLAN.md`: Overview of the integration approach
- `DCCC_TECHNICAL_REFERENCE.md`: Quick reference for common operations

### For Claude Code

- `DCCC_CLAUDE_CODE_GUIDE.md`: Guide for Claude Code's role
- `DCCC_TECHNICAL_REFERENCE.md`: Technical reference for implementation
- `DCCC_INTEGRATION_PLAN.md`: Detailed integration plan

## Key Components

### Integration Framework

The `integration_framework.py` file implements a bridge pattern that:
- Connects the official and custom implementations
- Controls features via toggles
- Provides fallbacks if features fail
- Routes API calls to the appropriate implementation

### Streaming Implementation

The custom streaming implementation:
- Uses `client.messages.stream()` instead of `client.beta.messages.with_raw_response.create()`
- Properly handles streaming events
- Supports thinking tokens
- Integrates tool use during streaming

### Streamlit Continuity

The continuity module:
- Saves conversation state before file changes
- Restores state after Streamlit restarts
- Uses serializable state format
- Handles edge cases

### ROSETTA STONE Protocol

The ROSETTA STONE protocol:
- Enables efficient AI-to-AI communication
- Uses a structured format: `[SENDER][TOPIC][MESSAGE]`
- Tracks token usage
- Optimizes for efficient communication

## Running the Integration

1. Launch the Anthropic container
2. Run the integration script with the container ID
3. Access the integrated UI at http://localhost:8501
4. Toggle features using the sidebar controls

## Cleaning Up

To organize the directories and archive old files:

```bash
./clean_directories.sh
```

This will:
- Move old documentation to an archive folder
- Organize the custom implementation
- Update reference documentation