#!/bin/bash
# Comprehensive Claude DC launcher with VNC and Streamlit UI
# This script launches Claude DC with proper environment setup and ensures
# both VNC (desktop) and Streamlit UI are accessible.

set -e  # Exit on error

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DC_ROOT="$SCRIPT_DIR/claude-dc-implementation"

# Color codes for output
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
LAUNCH_VNC=true
LAUNCH_STREAMLIT=true
DISABLE_BETAS=false
BETA_FLAGS="all"  # Options: all, prompt-cache, extended-output, none
DEV_MODE=false
VNC_ONLY_MODE=false

# Print banner
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}     Claude DC - Complete Launch System      ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --disable-vnc)
      LAUNCH_VNC=false
      shift
      ;;
    --disable-streamlit)
      LAUNCH_STREAMLIT=false
      shift
      ;;
    --vnc-only)
      VNC_ONLY_MODE=true
      LAUNCH_STREAMLIT=false
      shift
      ;;
    --disable-betas)
      DISABLE_BETAS=true
      shift
      ;;
    --beta-flags)
      BETA_FLAGS="$2"
      shift
      shift
      ;;
    --dev)
      DEV_MODE=true
      shift
      ;;
    --fresh)
      # This option is handled elsewhere, just consume it here
      shift
      ;;
    --no-monitor)
      # This option is handled elsewhere, just consume it here
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --disable-vnc        Don't launch VNC server"
      echo "  --disable-streamlit  Don't launch Streamlit UI"
      echo "  --vnc-only           Launch only VNC desktop, no Streamlit (most stable)"
      echo "  --disable-betas      Disable all beta features"
      echo "  --beta-flags VALUE   Specify which beta flags to enable (all, prompt-cache, extended-output, none)"
      echo "  --dev                Run in development mode"
      echo "  --fresh              Force creation of a new container"
      echo "  --no-monitor         Don't monitor container health (exit after launch)"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Configure environment variables based on options
export CLAUDE_ENV=${CLAUDE_ENV:-"live"}
if [ "$DEV_MODE" = true ]; then
  export CLAUDE_ENV="dev"
  echo -e "${YELLOW}Running in development mode${NC}"
fi

# Apply beta flags configuration
if [ "$DISABLE_BETAS" = true ]; then
  # Disable all beta features
  export ENABLE_PROMPT_CACHING=false
  export ENABLE_EXTENDED_OUTPUT=false
  export ENABLE_TOKEN_EFFICIENT=false
  echo -e "${YELLOW}All beta features disabled${NC}"
else
  case "$BETA_FLAGS" in
    "all")
      export ENABLE_PROMPT_CACHING=true
      export ENABLE_EXTENDED_OUTPUT=true
      export ENABLE_TOKEN_EFFICIENT=false  # Still keep this disabled for stability
      echo -e "${GREEN}Enabled beta features: prompt caching, 128K extended output${NC}"
      ;;
    "prompt-cache")
      export ENABLE_PROMPT_CACHING=true
      export ENABLE_EXTENDED_OUTPUT=false
      export ENABLE_TOKEN_EFFICIENT=false
      echo -e "${GREEN}Enabled beta features: prompt caching only${NC}"
      ;;
    "extended-output")
      export ENABLE_PROMPT_CACHING=false
      export ENABLE_EXTENDED_OUTPUT=true
      export ENABLE_TOKEN_EFFICIENT=false
      echo -e "${GREEN}Enabled beta features: 128K extended output only${NC}"
      ;;
    "none")
      export ENABLE_PROMPT_CACHING=false
      export ENABLE_EXTENDED_OUTPUT=false
      export ENABLE_TOKEN_EFFICIENT=false
      echo -e "${YELLOW}All beta features disabled${NC}"
      ;;
    *)
      echo -e "${RED}Invalid beta flag configuration: $BETA_FLAGS${NC}"
      exit 1
      ;;
  esac
fi

# Set screen dimensions for ComputerTool
export WIDTH=${WIDTH:-1024}
export HEIGHT=${HEIGHT:-768}
export DISPLAY_NUM=${DISPLAY_NUM:-1}

echo -e "${GREEN}Screen dimensions: ${WIDTH}x${HEIGHT} on display:${DISPLAY_NUM}${NC}"

# Check for Anthropic API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  # Check for API key file
  if [ -f "$HOME/.anthropic/api_key" ]; then
    export ANTHROPIC_API_KEY=$(cat "$HOME/.anthropic/api_key")
    echo -e "${GREEN}Using API key from $HOME/.anthropic/api_key${NC}"
  else
    echo -e "${YELLOW}No API key found. Please enter your Anthropic API key:${NC}"
    read -r ANTHROPIC_API_KEY
    # Save for future use
    mkdir -p "$HOME/.anthropic"
    echo "$ANTHROPIC_API_KEY" > "$HOME/.anthropic/api_key"
    chmod 600 "$HOME/.anthropic/api_key"
    export ANTHROPIC_API_KEY
  fi
fi

# Function to check service health
check_service() {
  local service_name=$1
  local port=$2
  local max_attempts=$3
  local attempt=1
  
  echo -e "${YELLOW}Checking ${service_name} availability on port ${port}...${NC}"
  
  while [ $attempt -le $max_attempts ]; do
    if nc -z localhost $port; then
      echo -e "${GREEN}✅ ${service_name} is available on port ${port}${NC}"
      return 0
    else
      echo -e "${YELLOW}Attempt ${attempt}/${max_attempts}: ${service_name} not yet available...${NC}"
      sleep 2
      ((attempt++))
    fi
  done
  
  echo -e "${RED}❌ ${service_name} is not available after ${max_attempts} attempts${NC}"
  return 1
}

# Launch and verify container
launch_container() {
  # First, stop any existing container
  if [ -n "$CONTAINER_ID" ]; then
    echo -e "${YELLOW}Found existing container (${CONTAINER_ID}), stopping it first...${NC}"
    docker stop "$CONTAINER_ID" >/dev/null 2>&1
    docker rm "$CONTAINER_ID" >/dev/null 2>&1
  fi
  
  # Create any required directories
  mkdir -p "$HOME/transcripts"
  
  # Run the container with proper mounts and port mappings
  echo -e "${GREEN}Launching Claude DC container...${NC}"
  CONTAINER_ID=$(docker run -d \
     -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
     -e ENABLE_PROMPT_CACHING="$ENABLE_PROMPT_CACHING" \
     -e ENABLE_EXTENDED_OUTPUT="$ENABLE_EXTENDED_OUTPUT" \
     -e ENABLE_TOKEN_EFFICIENT="$ENABLE_TOKEN_EFFICIENT" \
     -e WIDTH="$WIDTH" \
     -e HEIGHT="$HEIGHT" \
     -e DISPLAY_NUM="$DISPLAY_NUM" \
     -e CLAUDE_ENV="$CLAUDE_ENV" \
     -v "$HOME/.anthropic:/home/computeruse/.anthropic" \
     -v "$HOME/transcripts:/home/computeruse/transcripts" \
     -v "$SCRIPT_DIR:/home/computeruse/github/palios-taey-nova" \
     -e DISPLAY=:1 \
     --expose 5900 \
     --expose 8501 \
     --expose 6080 \
     --expose 8080 \
     -p 5900:5900 \
     -p 8501:8501 \
     -p 6080:6080 \
     -p 8080:8080 \
     --name claude-dc \
     ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest)
  
  echo -e "${GREEN}Container started with ID: ${CONTAINER_ID}${NC}"
  
  # Allow container to initialize
  echo -e "${YELLOW}Waiting for container services to start...${NC}"
  sleep 5
  
  # Check container logs for startup
  echo -e "${YELLOW}Checking container logs...${NC}"
  docker logs claude-dc | tail -n 10
  
  # Check container health
  echo -e "${YELLOW}Verifying container health...${NC}"
  CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' claude-dc)
  
  if [ "$CONTAINER_STATUS" != "running" ]; then
    echo -e "${RED}Container is not running! Status: ${CONTAINER_STATUS}${NC}"
    echo -e "${YELLOW}Showing container logs:${NC}"
    docker logs claude-dc
    return 1
  fi
  
  # Explicitly start services in the container
  echo -e "${YELLOW}Starting VNC and novnc services in container...${NC}"
  docker exec -d claude-dc bash -c "cd /home/computeruse && ./start_all.sh" || true
  sleep 3
  
  # Start Streamlit in the background if not in VNC-only mode
  if [ "$VNC_ONLY_MODE" = false ]; then
    echo -e "${YELLOW}Starting Streamlit service in container...${NC}"
    docker exec -d claude-dc bash -c "cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo && WIDTH=1024 HEIGHT=768 DISPLAY_NUM=1 DISPLAY=:1 python -m streamlit run streamlit.py &" || true
    sleep 2
    
    # Check Streamlit availability
    check_service "Streamlit" 8501 5
  else
    echo -e "${YELLOW}Running in VNC-only mode - Streamlit disabled${NC}"
  fi
  
  # Always check VNC service
  check_service "VNC" 6080 5
  
  return 0
}

# Remove container if requested
if [[ "$*" == *"--fresh"* ]]; then
  echo -e "${YELLOW}Removing any existing Claude DC containers...${NC}"
  docker ps -a | grep "claude-dc\|computer-use-demo" | awk '{print $1}' | xargs -r docker stop
  docker ps -a | grep "claude-dc\|computer-use-demo" | awk '{print $1}' | xargs -r docker rm
  CONTAINER_ID=""
else
  # Check Docker status for container
  CONTAINER_ID=$(docker ps -a | grep "claude-dc\|computer-use-demo" | awk '{print $1}' | head -n 1)
fi

# Launch or restart container
if [ -n "$CONTAINER_ID" ]; then
  echo -e "${YELLOW}Found existing container (${CONTAINER_ID})${NC}"
  
  CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_ID")
  if [ "$CONTAINER_STATUS" == "running" ]; then
    echo -e "${GREEN}Container is already running${NC}"
    
    # Check if services are accessible
    check_service "VNC" 6080 2 || {
      echo -e "${RED}VNC service is not accessible. Restarting container...${NC}"
      docker stop "$CONTAINER_ID" >/dev/null 2>&1
      launch_container
    }
    
    check_service "Streamlit" 8501 2 || {
      echo -e "${RED}Streamlit service is not accessible. Restarting container...${NC}"
      docker stop "$CONTAINER_ID" >/dev/null 2>&1
      launch_container
    }
  else
    echo -e "${YELLOW}Container exists but is not running (status: ${CONTAINER_STATUS})${NC}"
    echo -e "${YELLOW}Removing old container and launching fresh...${NC}"
    docker rm "$CONTAINER_ID" >/dev/null 2>&1
    launch_container
  fi
else
  # We need to run a new container
  echo -e "${YELLOW}No existing container found, launching new one...${NC}"
  
  # Check for required image
  if ! docker images | grep -q "ghcr.io/anthropics/anthropic-quickstarts.*computer-use-demo"; then
    echo -e "${YELLOW}Docker image not found, pulling latest...${NC}"
    docker pull ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
  fi
  
  # Launch container
  launch_container
fi

# Print access URLs
echo -e "${GREEN}=== Claude DC Services ===${NC}"
echo -e "${BLUE}Combined Demo UI:${NC} http://localhost:8080"
echo -e "${BLUE}VNC access:${NC} http://localhost:6080"
echo -e "${BLUE}Streamlit UI:${NC} http://localhost:8501"

# Launch browser tabs for requested interfaces
if [ "$LAUNCH_VNC" = true ]; then
  echo -e "${YELLOW}Launching VNC access in browser...${NC}"
  xdg-open http://localhost:6080 &
fi

if [ "$LAUNCH_STREAMLIT" = true ]; then
  echo -e "${YELLOW}Launching Streamlit UI in browser...${NC}"
  xdg-open http://localhost:8501 &
fi

echo -e "${GREEN}All services are now available!${NC}"
echo
echo -e "${YELLOW}Note: If you encounter any errors in Streamlit, try the following:${NC}"
echo -e "1. Use ${GREEN}--disable-betas${NC} flag to run without beta features"
echo -e "2. Use ${GREEN}--beta-flags prompt-cache${NC} to only enable prompt caching"
echo -e "3. Access the desktop directly via VNC at http://localhost:6080"
echo

# Monitor container health continuously
if [[ "$*" != *"--no-monitor"* ]]; then
  echo -e "${YELLOW}Starting container health monitoring (press Ctrl+C to exit)...${NC}"
  
  # Start monitoring loop to keep script alive and check health
  while true; do
    # Get container status
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' claude-dc 2>/dev/null)
    
    if [ "$CONTAINER_STATUS" != "running" ]; then
      echo -e "${RED}Container is no longer running! Status: ${CONTAINER_STATUS}${NC}"
      echo -e "${YELLOW}Attempting to restart...${NC}"
      
      # Try to restart the container
      docker start claude-dc 2>/dev/null
      sleep 5
      
      # Check if restart succeeded
      CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' claude-dc 2>/dev/null)
      if [ "$CONTAINER_STATUS" != "running" ]; then
        echo -e "${RED}Failed to restart container. Please run with --fresh flag to start a new container.${NC}"
        exit 1
      else
        echo -e "${GREEN}Container successfully restarted${NC}"
      fi
    else
      # Quick service check (minimal output)
      nc -z localhost 6080 >/dev/null 2>&1 || echo -e "${YELLOW}VNC service not responding${NC}"
      
      # Only check Streamlit if not in VNC-only mode
      if [ "$VNC_ONLY_MODE" = false ]; then
        nc -z localhost 8501 >/dev/null 2>&1 || echo -e "${YELLOW}Streamlit service not responding${NC}"
      fi
    fi
    
    # Show running status
    echo -ne "${GREEN}Claude DC running${NC} [press Ctrl+C to exit] $(date +"%H:%M:%S")\r"
    sleep 5
  done
else
  echo -e "${BLUE}To stop the container:${NC} docker stop claude-dc"
fi