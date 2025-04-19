#!/usr/bin/env bash
# Launch Claude DC dev container with test code and unique ports
set -e

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    echo "Please install Docker first by running the setup.sh script."
    exit 1
fi

# Check Docker permissions
if ! docker ps &> /dev/null; then
    echo "PERMISSION ERROR: Cannot connect to Docker daemon."
    echo "Running with sudo permissions. You may be asked for your password."
    echo "To fix this permanently, run: sudo usermod -aG docker $USER"
    echo "Then log out and back in."
    USE_SUDO="sudo"
else
    USE_SUDO=""
fi

# Ensure API key is available
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo "Please set it first with: export ANTHROPIC_API_KEY=your_api_key"
    exit 1
fi

# Determine the correct path based on environment
if [ -d "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo" ]; then
    # Claude DC environment
    HOST_CODE_PATH="/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
else
    # Development environment 
    HOST_CODE_PATH="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
fi
CONTAINER_CODE_PATH="/home/computeruse/computer_use_demo"

# Check if Docker image exists
if ! $USE_SUDO docker images | grep -q "anthropic-computer-use"; then
    echo "Docker image 'anthropic-computer-use' not found. Building it now..."
    
    # Check for Dockerfile
    DOCKERFILE_DIR=$(dirname "$HOST_CODE_PATH")
    if [ ! -f "$DOCKERFILE_DIR/Dockerfile" ]; then
        echo "Creating a Dockerfile in $DOCKERFILE_DIR"
        cat > "$DOCKERFILE_DIR/Dockerfile" << 'EOF'
FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    firefox-esr \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    tigervnc-standalone-server \
    wget \
    sudo

# Set up working directory
WORKDIR /home/computeruse

# Copy code
COPY ./computer_use_demo /home/computeruse/computer_use_demo

# Install Python dependencies
RUN cd /home/computeruse/computer_use_demo && pip3 install -r requirements.txt

# Setup environment
ENV DISPLAY=:1
ENV PYTHONUNBUFFERED=1

# Start script
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 5900 6080 8501

CMD ["/start.sh"]
EOF
    fi
    
    # Check for start.sh
    if [ ! -f "$DOCKERFILE_DIR/start.sh" ]; then
        echo "Creating start.sh script in $DOCKERFILE_DIR"
        cat > "$DOCKERFILE_DIR/start.sh" << 'EOF'
#!/bin/bash
set -e

# Start Xvfb
Xvfb :1 -screen 0 1280x800x16 &

# Start VNC server
x11vnc -display :1 -nopw -listen localhost -xkb -forever &

# Start noVNC
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 &

# Start fluxbox window manager
fluxbox -display :1 &

# Start streamlit app in the background
cd /home/computeruse/computer_use_demo
python3 -m streamlit run streamlit.py --server.port=8501 --server.address=0.0.0.0

wait
EOF
        chmod +x "$DOCKERFILE_DIR/start.sh"
    fi
    
    # Build the Docker image
    echo "Building Docker image from $DOCKERFILE_DIR"
    cd "$DOCKERFILE_DIR"
    $USE_SUDO docker build -t anthropic-computer-use:latest .
    
    if [ $? -ne 0 ]; then
        echo "Failed to build Docker image. Please check the error messages above."
        exit 1
    fi
    echo "Docker image built successfully."
fi

# Stop existing dev container if running
echo "Stopping any existing claude_dc_dev container..."
$USE_SUDO docker stop claude_dc_dev 2>/dev/null || true
$USE_SUDO docker rm claude_dc_dev 2>/dev/null || true

# Run new dev container
echo "Starting claude_dc_dev container..."
$USE_SUDO docker run -d --name claude_dc_dev \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e CLAUDE_ENV=dev \
  -p 8502:8501 -p 6081:6080 -p 5901:5900 \
  -v "$HOST_CODE_PATH:$CONTAINER_CODE_PATH" \
  anthropic-computer-use:latest

# Check if container started successfully
if [ $? -ne 0 ]; then
    echo "Error: Failed to start development container."
    exit 1
fi

echo "Claude DC dev container started!"
echo "Streamlit UI available at: http://localhost:8502"
echo "VNC interface available at: http://localhost:6081/vnc.html"
echo "Container logs:"
$USE_SUDO docker logs claude_dc_dev

echo "Waiting for Streamlit to initialize (this may take a moment)..."
sleep 5
echo "Development environment ready."