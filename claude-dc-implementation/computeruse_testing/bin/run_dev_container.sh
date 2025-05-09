#!/usr/bin/env bash
# Launch Claude DC dev container with test code and unique ports

# Parse command line arguments
USE_LOCAL_MODE=false
for arg in "$@"
do
    case $arg in
        --local)
        USE_LOCAL_MODE=true
        shift # Remove --local from processing
        ;;
        *)
        # Unknown option
        ;;
    esac
done

# Check if we should use local mode automatically
if [ "$USE_LOCAL_MODE" = false ]; then
    echo "Checking Docker availability..."
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Switching to local mode."
        USE_LOCAL_MODE=true
    else
        # Try to start Docker if it's not running
        if ! sudo systemctl is-active --quiet docker; then
            echo "Docker is not running. Attempting to start..."
            sudo systemctl start docker
            sleep 3
            
            # Check if it started successfully
            if ! sudo systemctl is-active --quiet docker; then
                echo "Failed to start Docker. Switching to local mode."
                USE_LOCAL_MODE=true
            fi
        fi
        
        # Even if Docker is running, check if we can access it
        if ! sudo docker ps &> /dev/null; then
            echo "Cannot connect to Docker daemon. Switching to local mode."
            USE_LOCAL_MODE=true
        fi
    fi
fi

# Ensure API key is available
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo "Please set it first with: export ANTHROPIC_API_KEY=your_api_key"
    exit 1
fi

# Define paths for both Docker and local modes
if [ -d "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo" ]; then
    # Claude DC environment
    SOURCE_PATH="/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
else
    # Development environment 
    SOURCE_PATH="/home/jesse/projects/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo"
fi

TEST_ENV_PATH="/home/computeruse/test_environment"

# Run in local mode (non-Docker) if Docker isn't available
if [ "$USE_LOCAL_MODE" = true ]; then
    echo "*** Running in local test mode (without Docker) ***"
    
    # Create test environment directory
    mkdir -p "$TEST_ENV_PATH"
    
    # Copy files to test environment
    echo "Copying files to test environment..."
    cp -r "$SOURCE_PATH"/* "$TEST_ENV_PATH/"
    
    # Update permissions
    chmod -R 755 "$TEST_ENV_PATH"
    
    # Set environment variables
    export CLAUDE_ENV=dev
    
    # Install dependencies if needed
    if [ -f "$TEST_ENV_PATH/requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r "$TEST_ENV_PATH/requirements.txt"
    fi
    
    # Set the port for Streamlit
    export STREAMLIT_PORT=8502
    
    echo "Starting Streamlit in test environment..."
    cd "$TEST_ENV_PATH"
    echo "Test environment ready at $TEST_ENV_PATH"
    echo "To run the Streamlit app:"
    echo "cd $TEST_ENV_PATH && python -m streamlit run streamlit.py --server.port=8502"
    echo "The app will be available at: http://localhost:8502"
    
    # Exit with success - user will need to manually run Streamlit
    # because we can't background it in this script effectively
    exit 0
else
    # Docker mode
    echo "*** Running in Docker mode ***"
    
    # Check if Docker image exists and build if needed
    if ! sudo docker images | grep -q "anthropic-computer-use"; then
        echo "Docker image not found. Building it..."
        
        # Get Dockerfile directory
        DOCKERFILE_DIR=$(dirname "$SOURCE_PATH")
        
        # Create Dockerfile if not exists
        if [ ! -f "$DOCKERFILE_DIR/Dockerfile" ]; then
            echo "Creating Dockerfile in $DOCKERFILE_DIR"
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
        
        # Create start.sh script if not exists
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
        
        # Build Docker image
        echo "Building Docker image from $DOCKERFILE_DIR"
        cd "$DOCKERFILE_DIR"
        sudo docker build -t anthropic-computer-use:latest .
        
        if [ $? -ne 0 ]; then
            echo "Failed to build Docker image. Switching to local mode."
            USE_LOCAL_MODE=true
            
            # Recursively call this script with local mode forced
            USE_LOCAL_MODE=true $0
            exit $?
        fi
    fi
    
    # Stop existing dev container if running
    echo "Stopping any existing claude_dc_dev container..."
    sudo docker stop claude_dc_dev 2>/dev/null || true
    sudo docker rm claude_dc_dev 2>/dev/null || true
    
    # Run new dev container
    echo "Starting claude_dc_dev container..."
    CONTAINER_CODE_PATH="/home/computeruse/computer_use_demo"
    sudo docker run -d --name claude_dc_dev \
      -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
      -e CLAUDE_ENV=dev \
      -p 8502:8501 -p 6081:6080 -p 5901:5900 \
      -v "$SOURCE_PATH:$CONTAINER_CODE_PATH" \
      anthropic-computer-use:latest
    
    # Check if container started successfully
    if [ $? -ne 0 ]; then
        echo "Error: Failed to start container. Switching to local mode."
        USE_LOCAL_MODE=true
        
        # Recursively call this script with local mode forced
        USE_LOCAL_MODE=true $0
        exit $?
    fi
    
    echo "Claude DC dev container started!"
    echo "Streamlit UI available at: http://localhost:8502"
    echo "VNC interface available at: http://localhost:6081/vnc.html"
    echo "Container logs:"
    sudo docker logs claude_dc_dev
    
    echo "Waiting for Streamlit to initialize (this may take a moment)..."
    sleep 5
    echo "Development environment ready."
    exit 0
fi