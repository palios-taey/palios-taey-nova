# Claude Code Encoding Fix

This document provides solutions for fixing UTF-8 encoding issues when running Claude Code in the Claude DC container environment.

## Problem

Claude Code is unable to run properly in the Claude DC container environment due to UTF-8 encoding issues, resulting in error messages about invalid characters.

## Solutions

We've created several different approaches to fix this issue, from simplest to most complex:

### 1. Wrapper Script (Recommended)

The simplest solution is a wrapper script that sets environment variables before executing Claude:

```bash
#!/bin/bash
# Set encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Run Claude directly with full path
/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude "$@"
```

To implement:
1. Copy `claude-encoded` to the container as `/home/computeruse/claude-encoded`
2. Make it executable: `chmod +x /home/computeruse/claude-encoded`
3. Run it instead of the regular claude executable: `./claude-encoded`

### 2. Direct Node.js Execution

Bypass the Claude executable and run it directly with Node:

```bash
#!/bin/bash
# Set encoding environment variables
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TERM=xterm-256color

# Run via Node directly
NODE_PATH=/home/computeruse/.nvm/versions/node/v18.20.0/bin/node
CLAUDE_PATH=/home/computeruse/.nvm/versions/node/v18.20.0/bin/claude

"$NODE_PATH" "$CLAUDE_PATH" "$@"
```

### 3. Patch the Shebang Line

This approach modifies the Claude executable's shebang line to include encoding variables:

```bash
#!/usr/bin/env -S LANG=C.UTF-8 LC_ALL=C.UTF-8 TERM=xterm-256color node --no-warnings --enable-source-maps
```

Use the `patch-claude.sh` script to implement this change.

### 4. Modify the JavaScript Source

This approach adds environment variable settings to the JavaScript code itself:

```javascript
// Set UTF-8 encoding environment variables
process.env.LANG = 'C.UTF-8';
process.env.LC_ALL = 'C.UTF-8';
process.env.TERM = 'xterm-256color';
```

Use the `patch-claude-node.sh` script to implement this change.

## Implementation Steps

1. Copy the desired script(s) into the Claude DC container
2. Make the script executable: `chmod +x script-name.sh`
3. Run the script to apply the fix
4. Test Claude Code to verify the encoding issue is resolved

## Verification

After applying any fix, test Claude Code with the following:

```bash
# Test with simple command
./claude-encoded --version

# Test with code processing
./claude-encoded "print('Hello, world')"
```

If Claude Code runs without encoding errors, the fix was successful.