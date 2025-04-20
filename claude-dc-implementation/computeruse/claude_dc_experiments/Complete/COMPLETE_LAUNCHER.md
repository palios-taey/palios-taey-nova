# Claude DC Complete Launcher

## Overview

This is a comprehensive launcher for Claude DC that includes:

1. **Enhanced container management** - properly starts and monitors the Docker container
2. **VNC and Desktop access** - provides access to both the Streamlit UI and VNC desktop
3. **Beta feature control** - granular control over which beta features are enabled
4. **Health monitoring** - continuous monitoring of container health and service availability
5. **Error recovery** - automatic recovery when services fail

## Usage

### Basic Usage

Run Claude DC with default settings:
```bash
./launch_claude_dc_complete.sh
```

### VNC-Only Mode (Most Stable)

Run Claude DC with only VNC access (no Streamlit, which may cause errors):
```bash
./launch_claude_dc_complete.sh --vnc-only
```

### Beta Feature Control

Run without any beta features:
```bash
./launch_claude_dc_complete.sh --disable-betas
```

Run with only prompt caching (most stable beta feature):
```bash
./launch_claude_dc_complete.sh --beta-flags prompt-cache
```

Run with only extended output capability:
```bash
./launch_claude_dc_complete.sh --beta-flags extended-output
```

Run with all beta features enabled:
```bash
./launch_claude_dc_complete.sh --beta-flags all
```

### Advanced Options

Create a fresh container (removing any existing ones):
```bash
./launch_claude_dc_complete.sh --fresh
```

Launch in development mode:
```bash
./launch_claude_dc_complete.sh --dev
```

Run without health monitoring:
```bash
./launch_claude_dc_complete.sh --no-monitor
```

View all options:
```bash
./launch_claude_dc_complete.sh --help
```

## Access URLs

- **VNC Desktop:** http://localhost:6080
- **Streamlit UI:** http://localhost:8501
- **Combined UI:** http://localhost:8080

## Troubleshooting

If you experience issues:

1. First try VNC-only mode: `./launch_claude_dc_complete.sh --vnc-only`
2. If problems persist, try: `./launch_claude_dc_complete.sh --fresh --disable-betas --vnc-only`
3. Check container logs: `docker logs claude-dc`
4. Restart container: `docker restart claude-dc`

## Health Monitoring

The launcher includes continuous health monitoring that:
- Checks if the Docker container is running
- Verifies VNC and Streamlit services are accessible
- Automatically attempts to recover if services fail
- Keeps you informed of the system status

Press Ctrl+C at any time to exit the monitoring mode (container will continue running).