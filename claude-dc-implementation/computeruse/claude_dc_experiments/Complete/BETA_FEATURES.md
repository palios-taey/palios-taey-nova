# Claude DC Beta Features Guide

## Understanding Claude DC Beta Features

Claude DC supports several beta features that enhance its capabilities. These features can be enabled or disabled independently to help isolate issues.

### Available Beta Features

1. **Prompt Caching**
   - Flag: `prompt-caching-2024-07-31`
   - Environment Variable: `ENABLE_PROMPT_CACHING`
   - Description: Caches previously processed prompt sections to reduce token usage and improve performance
   - Risk Level: Low

2. **128K Extended Output**
   - Flag: `output-128k-2025-02-19`
   - Environment Variable: `ENABLE_EXTENDED_OUTPUT`
   - Description: Enables support for very long outputs (up to ~128k tokens)
   - Risk Level: Medium

3. **Token-Efficient Tools** (Disabled by default)
   - Flag: `token-efficient-tools-2025-02-19`
   - Environment Variable: `ENABLE_TOKEN_EFFICIENT`
   - Description: Experimental feature for more token-efficient tool handling
   - Risk Level: High (may cause context loss issues)

## Troubleshooting Beta Features

If you encounter issues with Claude DC, you can selectively disable or enable beta features to isolate the problem.

### Common Problems and Solutions

1. **Issue**: Claude stops generating responses mid-stream
   - **Solution**: Disable 128K Extended Output: `ENABLE_EXTENDED_OUTPUT=false ./launch_claude_dc_complete.sh`

2. **Issue**: Claude loses context between turns
   - **Solution**: Make sure Token-Efficient Tools is disabled (default): `ENABLE_TOKEN_EFFICIENT=false ./launch_claude_dc_complete.sh`

3. **Issue**: High token usage
   - **Solution**: Ensure Prompt Caching is enabled: `ENABLE_PROMPT_CACHING=true ./launch_claude_dc_complete.sh`

4. **Issue**: All beta features causing problems
   - **Solution**: Disable all beta features: `./launch_claude_dc_complete.sh --disable-betas`

## Incremental Testing Approach

If you're experiencing issues with Claude DC, follow this incremental approach to enable features:

1. Start with no beta features:
   ```bash
   ./launch_claude_dc_complete.sh --disable-betas
   ```

2. Enable only prompt caching (usually very stable):
   ```bash
   ./launch_claude_dc_complete.sh --beta-flags prompt-cache
   ```

3. Add extended output if needed:
   ```bash
   ./launch_claude_dc_complete.sh --beta-flags extended-output
   ```

4. Enable all stable beta features:
   ```bash
   ./launch_claude_dc_complete.sh --beta-flags all
   ```

## Advanced Configuration

You can directly set environment variables before launching the script for fine-grained control:

```bash
ENABLE_PROMPT_CACHING=true ENABLE_EXTENDED_OUTPUT=false ENABLE_TOKEN_EFFICIENT=false ./launch_claude_dc_complete.sh
```

## VNC and Desktop Access

Claude DC provides both a Streamlit UI for interaction and VNC access to the desktop environment.

### Access Options

1. **Combined Demo UI**:
   - URL: http://localhost:8080
   - Description: Provides both the Streamlit interface and VNC access in a single view

2. **Streamlit UI Only**:
   - URL: http://localhost:8501
   - Description: Just the Claude DC chat interface without desktop access

3. **VNC Access Only**:
   - URL: http://localhost:6080
   - Description: Direct access to the desktop environment via VNC

### Command Line Options

You can control which interfaces are opened when launching Claude DC:

```bash
# Only launch VNC (no Streamlit)
./launch_claude_dc_complete.sh --disable-streamlit

# Only launch Streamlit (no VNC)
./launch_claude_dc_complete.sh --disable-vnc

# Launch both (default)
./launch_claude_dc_complete.sh
```