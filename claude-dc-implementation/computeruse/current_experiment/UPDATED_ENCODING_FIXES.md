# Updated Claude Code Encoding Fixes

Based on the debug output analysis, we've created enhanced solutions to fix the UTF-8 encoding issues when running Claude Code in the Claude DC container environment.

## Root Cause Analysis

The debug logs revealed several issues:

1. **Binary data handling**: Node.js is writing raw binary data directly to the terminal, bypassing normal encoding conversion (visible in Buffer outputs)

2. **Stream handling problems**: There appear to be issues with stream reading/writing operations

3. **Terminal configuration mismatch**: Despite environment variables being set correctly, the terminal handling in Claude Code is causing problems

## Solution 1: Enhanced Wrapper Script

The most robust approach is to use an enhanced wrapper script that addresses multiple aspects of the encoding problems:

```bash
./improved-claude-encoding-fix.sh
```

This script:
- Sets comprehensive encoding environment variables
- Configures Node.js options to handle encoding correctly
- Forces stdout/stderr to use UTF-8
- Provides a debug mode for troubleshooting

## Solution 2: JavaScript Patching

An alternative approach is to patch the Claude Code executable directly:

```bash
./patch-claude-code-encoding.sh
```

This script:
- Creates a backup of the original Claude Code executable
- Modifies the JavaScript to force UTF-8 encoding
- Adds error handling for encoding issues
- Intercepts stdout/stderr write operations to ensure UTF-8 encoding

## Diagnostic Tool

To help identify exactly where the encoding issue is occurring:

```bash
./test-claude-encoding.sh
```

This script tests:
- Terminal UTF-8 support
- Node.js UTF-8 handling
- Claude Code version information
- System environment variables
- A simple Claude Code query

## Implementation Instructions

1. Copy these scripts to the Claude DC container
2. Make them executable: `chmod +x *.sh`
3. Try the diagnostic tool first: `./test-claude-encoding.sh`
4. Based on the results, use either the wrapper script or the patching approach
5. If using the wrapper, run: `./improved-claude-encoding-fix.sh [your query]`
6. If issues persist, try the debug mode: `./improved-claude-encoding-fix.sh --debug [your query]`

## Additional Troubleshooting

If issues persist:

1. Check if a specific Node.js version might work better:
   ```bash
   nvm install 16.20.0
   nvm use 16.20.0
   npm install -g @anthropic-ai/claude-code@latest
   ```

2. Try simplifying the terminal environment:
   ```bash
   export TERM=xterm
   ./improved-claude-encoding-fix.sh
   ```

3. Check for any terminal multiplexers (screen, tmux) that might be affecting encoding

4. Verify iconv is installed in the container:
   ```bash
   apt-get update && apt-get install -y libc-bin
   ```

5. Try running Claude Code with explicit stdin/stdout encoding:
   ```bash
   ./improved-claude-encoding-fix.sh < <(echo "Your query") | iconv -f utf-8 -t utf-8
   ```