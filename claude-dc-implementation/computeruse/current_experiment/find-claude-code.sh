#!/bin/bash
# Simple script to find the claude-code executable in the container

echo "Searching for claude-code executable..."
echo

# Check common locations
echo "Checking common locations:"
for dir in /home/computeruse/bin /usr/local/bin /usr/bin /bin ~/.local/bin; do
    if [ -f "$dir/claude-code" ]; then
        echo "✅ Found at: $dir/claude-code"
        CLAUDE_CODE="$dir/claude-code"
    fi
done

echo
echo "Checking the .claude directory:"
if [ -d "/home/computeruse/.claude" ]; then
    echo "✅ .claude directory exists. Contents:"
    ls -la /home/computeruse/.claude
    
    # Look for executable files in the .claude directory
    echo
    echo "Executable files in the .claude directory:"
    find /home/computeruse/.claude -type f -executable | grep -v "__pycache__"
fi

echo
echo "Checking PATH environment variable:"
echo $PATH | tr ':' '\n'

echo
echo "Searching for files named claude-code or similar in home directory:"
find /home/computeruse -name "claude-code*" -type f 2>/dev/null

echo
echo "Checking if 'claude-code' is a shell function or alias:"
type claude-code 2>/dev/null || echo "Not found as a command, function, or alias"

echo
echo "If found, try running the executable directly with proper encoding:"
echo "LANG=C.UTF-8 LC_ALL=C.UTF-8 TERM=xterm-256color /path/to/claude-code"