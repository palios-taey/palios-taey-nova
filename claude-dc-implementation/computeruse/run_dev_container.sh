#!/usr/bin/env bash
# Launch Claude DC dev container with test code and unique ports

# Ensure API key is available
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo "Please set it first with: export ANTHROPIC_API_KEY=your_api_key"
    exit 1
fi

# Define paths
HOST_CODE_PATH="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
CONTAINER_CODE_PATH="/home/computeruse/computer_use_demo"

# Stop existing dev container if running
echo "Stopping any existing claude_dc_dev container..."
docker stop claude_dc_dev 2>/dev/null || true
docker rm claude_dc_dev 2>/dev/null || true

# Run new dev container
echo "Starting claude_dc_dev container..."
docker run -d --name claude_dc_dev \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e CLAUDE_ENV=dev \
  -p 8502:8501 -p 6081:6080 -p 5901:5900 \
  -v "$HOST_CODE_PATH:$CONTAINER_CODE_PATH" \
  anthropic-computer-use:latest

# Check if container started successfully
if [ $? -ne 0 ]; then
    echo "Error: Failed to start development container."
    echo "Make sure the anthropic-computer-use image exists."
    echo "You may need to build it first using:"
    echo "docker build -t anthropic-computer-use:latest ."
    exit 1
fi

echo "Claude DC dev container started!"
echo "Streamlit UI available at: http://localhost:8502"
echo "VNC interface available at: http://localhost:6081/vnc.html"
echo "Container logs:"
docker logs claude_dc_dev

echo "Waiting for Streamlit to initialize (this may take a moment)..."
sleep 5
echo "Development environment ready."