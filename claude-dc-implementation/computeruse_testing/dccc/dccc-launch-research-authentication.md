# Troubleshooting Claude Code in restricted environments

Restricted computing environments pose unique challenges for tools like Claude Code that require authentication and external connections. This comprehensive guide addresses authentication issues, terminal functionality problems, and best practices specifically for Claude Code in environments with security limitations.

## Browser-free authentication with Claude Code

When standard browser authentication fails in restricted environments, Claude Code offers several alternatives. API keys provide the most reliable approach, bypassing browser requirements entirely.

**Direct API key authentication** is the simplest method. Set the API key as an environment variable before running Claude:

```bash
# Set the API key
export ANTHROPIC_API_KEY="your_api_key_here"

# Run Claude Code normally
claude
```

For persistent configuration, add to your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

Alternatively, configure Claude Code via the global configuration file at `~/.claude.json`:

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your_api_key_here"
  }
}
```

Permissions matter - secure this file with restricted access:

```bash
chmod 600 ~/.claude.json
```

## Enabling automatic browser opening

Claude Code attempts to open a browser automatically during OAuth authentication. If this fails, check these common issues:

1. **Default browser configuration**: Ensure your system has a properly configured default browser. On Linux:
   ```bash
   xdg-settings get default-web-browser
   # To set a default browser:
   xdg-settings set default-web-browser firefox.desktop
   ```

2. **X11 permissions**: For graphical applications in restricted environments, check X server permissions:
   ```bash
   xhost +local:
   ```

3. **Display environment variable**: Verify the DISPLAY variable is properly set:
   ```bash
   echo $DISPLAY
   # If not set:
   export DISPLAY=:0
   ```

If browser opening still fails, you can manually copy the authentication URL displayed in the terminal and paste it into any available browser.

## Fixing copy/paste in xterm and Linux terminals

Linux terminal environments use multiple clipboard mechanisms that can cause confusion in restricted setups. Understanding these is key to troubleshooting copy/paste issues.

### Configure xterm clipboard support

Add these lines to your `~/.Xresources` file to enable proper clipboard support:

```
! Enable copying to CLIPBOARD (not just PRIMARY)
xterm*selectToClipboard: true

! Configure key bindings for CLIPBOARD operations
xterm*VT100.translations: #override \
    Ctrl Shift <Key>C: copy-selection(CLIPBOARD) \n\
    Ctrl Shift <Key>V: insert-selection(CLIPBOARD)
```

Apply settings with:

```bash
xrdb -merge ~/.Xresources
```

### Terminal clipboard tools

When standard clipboard mechanisms fail, command-line tools can provide alternatives:

```bash
# Install clipboard utilities
sudo apt install xclip xsel    # Debian/Ubuntu
sudo dnf install xclip xsel    # Fedora
sudo pacman -S xclip xsel      # Arch Linux

# Copy text to clipboard
echo "text" | xclip -selection clipboard

# Paste from clipboard
xclip -selection clipboard -o
```

Create aliases for consistent usage:

```bash
echo 'alias clip="xclip -selection clipboard"' >> ~/.bashrc
echo 'alias paste="xclip -selection clipboard -o"' >> ~/.bashrc
source ~/.bashrc
```

### Clipboard synchronization

The PRIMARY (highlight) and CLIPBOARD (Ctrl+C/V) selections often don't sync automatically. Install a clipboard manager to fix this:

```bash
sudo apt install parcellite    # Debian/Ubuntu

# Configure to synchronize clipboards:
# 1. Right-click parcellite tray icon
# 2. Select Preferences
# 3. Enable "Use Primary" and "Synchronize clipboards"
```

## API key configuration for Claude Code

The most reliable way to use Claude Code in restricted environments is through pre-loaded API keys. Here are the best configuration methods:

### Environment variable approach

```bash
# Direct Anthropic API key
export ANTHROPIC_API_KEY="your_api_key_here"

# For AWS Bedrock authentication
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
export AWS_ACCESS_KEY_ID="your_aws_access_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
export AWS_REGION="your_aws_region"

# For Google Vertex authentication
export CLAUDE_CODE_USE_VERTEX=1
export ANTHROPIC_MODEL="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Configuration file method

Create or modify `~/.claude.json`:

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your_api_key_here",
    "ANTHROPIC_MODEL": "claude-3-7-sonnet-20250219"
  }
}
```

### Custom API key helper

For dynamic key generation or rotation, configure a script to provide the key:

```json
{
  "env": {
    "apiKeyHelper": "/path/to/your/key-generation-script.sh"
  }
}
```

The script will be invoked once at startup and the result cached for the session.

## Alternative authentication methods

When standard authentication fails, these alternatives work well in restricted environments:

### AWS Bedrock integration

Many enterprise environments already approve AWS connections, making this a convenient alternative:

```bash
# Configure for Bedrock with Claude 3.7 Sonnet
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL="us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# Set as default configuration
claude config set --global env '{"CLAUDE_CODE_USE_BEDROCK": "true", "ANTHROPIC_MODEL": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"}'
```

### Proxy server configuration

When direct connections to Anthropic are blocked, proxy servers can help:

```bash
# Standard proxy configuration
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Custom headers for proxy authentication
export ANTHROPIC_CUSTOM_HEADERS="Proxy-Authorization: Bearer your_auth_token"
```

### Headless mode for automation

For non-interactive usage, combine API key authentication with the `--print` flag:

```bash
export ANTHROPIC_API_KEY="your_api_key_here"
claude --print "Fix the bugs in the authentication module"
```

## Common environment issues blocking browsers

Several environment factors can prevent Claude Code from opening browsers:

### OS compatibility issues

Claude Code doesn't run directly in Windows and requires WSL. Common WSL-related issues include:

- OS/platform detection errors when WSL uses Windows npm
- "Node not found" errors when your WSL environment uses a Windows Node.js installation

To fix these, ensure you're using Linux-native versions of Node and npm within WSL.

### Network and proxy problems

- **Firewall restrictions**: Check if outbound connections to Anthropic's authentication endpoints are blocked
- **Corporate proxies**: Configure proxy settings with the HTTP_PROXY and HTTPS_PROXY environment variables
- **VPN issues**: Some VPNs restrict access to authentication domains

### Browser configuration issues

- Missing default browser configuration
- Browser security settings preventing programmatic opening
- Insufficient permissions for terminal applications to launch browsers

## Terminal settings blocking copy/paste

Several terminal settings can interfere with copy/paste functionality:

### Security mechanisms

- **Bracketed paste mode**: May interfere with certain paste operations
  ```bash
  # Disable with:
  printf "\e[?2004l"
  # Or in bash:
  bind 'set enable-bracketed-paste off'
  ```

### Application-specific issues

- **Terminal multiplexers**: Tools like tmux/screen might capture mouse events
  ```bash
  # Fix with (in .tmux.conf):
  set -g mouse on
  ```

- **Text editors**: Vim, Emacs, etc. may have custom clipboard handling
  ```bash
  # For vim, add to .vimrc:
  set clipboard=unnamedplus
  ```

### X11 configuration problems

- **Missing permissions**: X server may restrict clipboard access
  ```bash
  # Allow local applications to access X server:
  xhost +local:
  ```

- **Forwarding issues**: For remote sessions, ensure X11 forwarding is enabled
  ```bash
  # Connect with X11 forwarding:
  ssh -X user@host
  ```

## API key management best practices

Secure management of API keys is crucial in restricted environments:

### Storage security

- **Never hardcode** API keys in source code
- **Avoid storing** keys in files inside your application's source tree
- **Use dedicated secrets management** where available (Vault, AWS Secrets Manager)
- **Set proper file permissions** on any file containing API keys (chmod 600)

### Rotation and access control

- **Implement access controls** to limit who can access keys
- **Rotate keys periodically** (90 days standard, 30 days for high security)
- **Use different keys** for development, testing, and production
- **Delete unused keys** to minimize attack surface

### Secure deployment patterns

- Store keys in CI/CD secret stores, not configuration files
- Use different keys for CI/CD than for human users
- Restrict key permissions to only what's needed
- Scan for leaked secrets in repositories using tools like GitGuardian

## Solutions for Claude Computer Use environments

The Claude "Computer Use" feature runs in a sandboxed environment with specific requirements. When working in this context:

### Container-based approach

Claude Code provides a development container configuration that works well in restricted environments:

```bash
# Clone the Claude Code reference implementation
git clone https://github.com/anthropic/claude-code-reference
cd claude-code-reference

# Open in VS Code with Remote-Containers extension
# When prompted, click "Reopen in Container"
```

The container includes:
- Production-ready Node.js with dependencies
- Custom firewall restricting network access
- Security measures for running with restricted permissions

### Authentication in sandboxed environments

For Claude's Computer Use feature:

1. **Use API key authentication** rather than browser-based OAuth
2. **Configure environment variables** at the system level or in configuration files
3. **Implement proxy settings** if needed for network access
4. **Run in headless mode** with the `--print` flag for automation

The Claude Computer Use environment allows using the `--dangerously-skip-permissions` flag to bypass permission prompts in containerized environments.

### Workarounds for specific restrictions

If automation is required in Computer Use environments:
```bash
# Create a wrapper script to handle authentication
cat > run-claude.sh << 'EOF'
#!/bin/bash
export ANTHROPIC_API_KEY=$(cat /path/to/secure/key/file)
claude "$@"
EOF
chmod +x run-claude.sh

# Use the wrapper script
./run-claude.sh --print "Fix this code"
```

## Conclusion

By implementing these solutions, you can successfully run Claude Code even in highly restricted environments. The API key authentication method is generally the most reliable approach, avoiding browser dependencies entirely. For enterprise deployments, AWS Bedrock integration often provides the path of least resistance as these connections may already be approved in your organization.

Remember that security and compliance requirements vary across organizations - always consult with your security team before implementing workarounds in restricted environments.
