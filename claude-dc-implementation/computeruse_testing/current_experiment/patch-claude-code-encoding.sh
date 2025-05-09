#!/bin/bash
# Script to patch Claude Code executable to fix encoding issues in the Claude DC environment

# Path to Claude Code executable
CLAUDE_PATH="/home/computeruse/.nvm/versions/node/v18.20.8/bin/claude"
BACKUP_PATH="${CLAUDE_PATH}.bak"

# Backup the original file if not already done
if [[ ! -f "$BACKUP_PATH" ]]; then
    echo "Creating backup of original Claude Code executable..."
    cp "$CLAUDE_PATH" "$BACKUP_PATH"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to create backup. Aborting."
        exit 1
    fi
    echo "Backup created at $BACKUP_PATH"
fi

# Temp file for patching
TEMP_FILE=$(mktemp)

# Check if file exists and is a JavaScript file (should contain Node.js shebang)
if grep -q "node" "$CLAUDE_PATH"; then
    # Extract shebang line
    SHEBANG=$(head -n 1 "$CLAUDE_PATH")
    
    # Create new file with modified shebang and encoding fixes
    echo '#!/usr/bin/env -S node --no-warnings --enable-source-maps' > "$TEMP_FILE"
    echo '' >> "$TEMP_FILE"
    echo '// === ENCODING FIX PATCH APPLIED ===' >> "$TEMP_FILE"
    echo '// Force UTF-8 encoding globally' >> "$TEMP_FILE"
    echo 'process.env.LANG = "C.UTF-8";' >> "$TEMP_FILE"
    echo 'process.env.LC_ALL = "C.UTF-8";' >> "$TEMP_FILE"
    echo 'process.env.TERM = "xterm-256color";' >> "$TEMP_FILE"
    echo 'process.env.LESSCHARSET = "utf-8";' >> "$TEMP_FILE"
    echo 'process.env.NCURSES_NO_UTF8_ACS = "1";' >> "$TEMP_FILE"
    echo '' >> "$TEMP_FILE"
    echo '// Force stdout/stderr to use UTF-8 encoding' >> "$TEMP_FILE"
    echo 'process.stdout.setDefaultEncoding("utf8");' >> "$TEMP_FILE"
    echo 'process.stderr.setDefaultEncoding("utf8");' >> "$TEMP_FILE"
    echo '' >> "$TEMP_FILE"
    echo '// Handle encoding errors in console output' >> "$TEMP_FILE"
    echo 'const originalStdoutWrite = process.stdout.write;' >> "$TEMP_FILE"
    echo 'process.stdout.write = function(chunk, encoding, callback) {' >> "$TEMP_FILE"
    echo '  try {' >> "$TEMP_FILE"
    echo '    if (Buffer.isBuffer(chunk)) {' >> "$TEMP_FILE"
    echo '      chunk = chunk.toString("utf8");' >> "$TEMP_FILE"
    echo '    }' >> "$TEMP_FILE"
    echo '    return originalStdoutWrite.call(this, chunk, "utf8", callback);' >> "$TEMP_FILE"
    echo '  } catch (e) {' >> "$TEMP_FILE"
    echo '    console.error("Encoding error:", e);' >> "$TEMP_FILE"
    echo '    return originalStdoutWrite.call(this, "[Encoding Error]", "utf8", callback);' >> "$TEMP_FILE"
    echo '  }' >> "$TEMP_FILE"
    echo '};' >> "$TEMP_FILE"
    echo '' >> "$TEMP_FILE"
    
    # Append the rest of the file (skipping the original shebang)
    tail -n +2 "$CLAUDE_PATH" >> "$TEMP_FILE"
    
    # Replace the original file with our patched version
    chmod +x "$TEMP_FILE"
    mv "$TEMP_FILE" "$CLAUDE_PATH"
    
    echo "Successfully patched Claude Code with encoding fixes!"
    echo "To test, run:"
    echo "  ${CLAUDE_PATH} --version"
    echo ""
    echo "If you need to revert to the original version, run:"
    echo "  cp \"${BACKUP_PATH}\" \"${CLAUDE_PATH}\""
else
    echo "Error: $CLAUDE_PATH does not appear to be a valid Claude Code executable"
    rm "$TEMP_FILE"
    exit 1
fi