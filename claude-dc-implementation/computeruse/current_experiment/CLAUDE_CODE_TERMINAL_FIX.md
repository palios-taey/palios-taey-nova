# Claude Code Terminal Fix

## Problem
Claude Code experiences severe encoding issues when run in the Claude DC container environment:
- Random â characters appearing in the output
- Numbers appearing in the prompt field
- Thinking/analysis comments appearing on separate lines
- Each keystroke adding more â characters

## Root Cause
After extensive debugging, we determined the issue is with terminal compatibility rather than just UTF-8 encoding. Claude Code uses advanced terminal features that aren't properly supported in the default terminal environment used in the Claude DC container.

## Solution: Run Claude Code in XTerm

The most effective solution is to run Claude Code in a dedicated XTerm instance, which provides better terminal emulation and encoding support:

```bash
xterm -fa "Monospace" -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
```

### Implementation

A wrapper script has been created at `/home/computeruse/claude-xterm.sh`:

```bash
#!/bin/bash
# Launch Claude Code in xterm with proper encoding
xterm -fa "Monospace" -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude $*"
```

A symbolic link is also created for easy access:

```bash
ln -sf /home/computeruse/claude-xterm.sh /home/computeruse/claude-code
```

## Usage

To use Claude Code:

```bash
./claude-code "Your query here"
```

or

```bash
/home/computeruse/claude-code "Your query here"
```

This will launch Claude Code in a separate XTerm window with proper encoding support.

## Benefits of This Approach

1. **Isolation**: Runs Claude Code in its own terminal environment, preventing conflicts with the host terminal
2. **Simplicity**: No need to modify Claude Code itself or install additional Node.js packages
3. **Reliability**: XTerm has excellent support for Unicode/UTF-8 and terminal control sequences
4. **Compatibility**: Works regardless of Node.js version or Claude Code version

## Integration

This solution has been integrated into the `claude_dc_quick_setup.sh` script, so it will be automatically set up when running the quick setup process.

## Troubleshooting

If you experience issues:

1. Ensure XTerm is installed:
   ```bash
   sudo apt-get update && sudo apt-get install -y xterm
   ```

2. Try adjusting the font settings in the xterm command if text is too small or large:
   ```bash
   xterm -fa "Monospace" -fs 14 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
   ```

3. If Claude Code is installed at a different path, update the script accordingly.