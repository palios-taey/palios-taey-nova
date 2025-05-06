# Claude Code Setup for Claude DC

This document explains how Claude Code is automatically set up in the Claude DC environment.

## Overview

The setup process automates the configuration of Claude Code within Claude DC, eliminating the need for manual API key entry. This is critical since copy-paste functionality is not available in Claude DC's terminal.

## Implementation Details

### 1. Claude Code API Key Configuration

The API key for Claude Code is automatically extracted from the secrets file and configured in two ways:

1. **Configuration File**: Creates a `.claude/config.json` file with the API key
2. **Environment Variable**: Sets the `ANTHROPIC_API_KEY` environment variable when launching Claude Code

### 2. Setup Process

The process is implemented in the `claude_dc_quick_setup.sh` script:

```bash
# Create Claude Code config directory
mkdir -p /home/computeruse/.claude

# Extract Claude Code API key from secrets file
if [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
    CLAUDE_CODE_API_KEY=$(grep -o '"claude_code"[[:space:]]*:[[:space:]]*"[^"]*"' /home/computeruse/secrets/palios-taey-secrets.json | sed 's/.*"claude_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    
    if [ ! -z "$CLAUDE_CODE_API_KEY" ]; then
        echo "Claude Code API key found in secrets"
        
        # Create config file with API key
        cat > /home/computeruse/.claude/config.json << EOF
{
  "apiKey": "$CLAUDE_CODE_API_KEY"
}
EOF
        chmod 600 /home/computeruse/.claude/config.json
        
        # Export API key as environment variable
        export ANTHROPIC_API_KEY="$CLAUDE_CODE_API_KEY"
    else
        echo "Error: Claude Code API key not found in secrets file"
    fi
else
    echo "Error: Secrets file not found"
fi
```

### 3. Launch with API Key

When launching Claude Code, the API key is passed as an environment variable and the `--no-browser` flag is used to prevent browser-based authentication:

```bash
if [ ! -z "$CLAUDE_CODE_API_KEY" ]; then
    echo "Using API key from secrets for Claude Code"
    xterm -fa 'Monospace' -fs 6 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 ANTHROPIC_API_KEY=\"$CLAUDE_CODE_API_KEY\" /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude --no-browser"
else
    echo "WARNING: No API key found, Claude Code will prompt for key on first run"
    xterm -fa 'Monospace' -fs 6 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude --no-browser"
fi
```

The `--no-browser` flag is essential when running in Claude DC's environment, as it prevents Claude Code from trying to open a browser for authentication, which would fail in the headless environment.

## Security Considerations

1. The script handles the removal of the `testkey-` prefix from secret files
2. The configuration file permissions are set to 600 (read/write for owner only)
3. The API key is never logged or printed to the console

## Debugging

You can enable debug mode by setting the `DEBUG` environment variable:

```bash
DEBUG=1 ./claude_dc_quick_setup.sh
```

This will enable verbose output of all commands executed by the script, helping diagnose any issues.

## Required Secret Format

The secrets file should contain a JSON object with a `claude_code` key:

```json
{
  "claude_code": "sk-ant-api03-..." 
}
```

Note: The actual file should include the `testkey-` prefix that will be automatically removed during setup.