#!/bin/bash
# setup.sh

echo "Starting Claude DC Environment Setup"
echo "==================================="

# Update system packages
sudo apt update -y

# Install required system-level dependencies explicitly
sudo apt install -y \
    brltty \
    command-not-found \
    chrome-gnome-shell \
    cups-bsd \
    python3-dbus \
    docker.io \
    python3-apt \
    system76-driver \
    python3-systemd \
    ubuntu-drivers-common \
    ufw \
    xkit

# Install and setup Docker properly
echo "Setting up Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    # Add Docker's official GPG key
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      
    # Install Docker packages
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group to run without sudo
sudo usermod -aG docker $USER
echo "Docker setup complete. Adding current shell to docker group..."

# Apply group changes to current shell session without requiring logout
newgrp docker << EONG

# Test Docker installation
echo "Testing Docker installation..."
docker run --rm hello-world || echo "Docker test failed. Please check Docker installation manually."

# Build the required Docker image for Claude DC
echo "Building the anthropic-computer-use Docker image..."
cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse
if [[ -f "Dockerfile" ]]; then
    docker build -t anthropic-computer-use:latest .
    echo "Docker image built successfully."
else
    # Create a basic Dockerfile if none exists
    echo "No Dockerfile found. Creating a basic Claude DC Dockerfile..."
    cat > Dockerfile << 'EOF'
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

    # Create a start.sh script if it doesn't exist
    cat > start.sh << 'EOF'
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
    chmod +x start.sh
    
    # Build the Docker image
    docker build -t anthropic-computer-use:latest .
    echo "Docker image built successfully."
fi

echo "Verifying image exists..."
docker images | grep anthropic-computer-use || echo "Warning: Image build may have failed"

# Return to original group and directory
EONG

sudo apt-get install -y rsync

# Python environment setup
echo "Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r claude-dc-implementation/requirements.txt

# Install spaCy language model
echo "Installing spaCy model..."
python -m spacy download en_core_web_md

# Create required directories
echo "Creating directory structure..."
mkdir -p claude-dc-implementation/data/transcripts
mkdir -p claude-dc-implementation/data/patterns
mkdir -p claude-dc-implementation/data/models
mkdir -p claude-dc-implementation/logs
mkdir -p claude-dc-implementation/cache

# Setup .env file from secrets (adjust as needed)
if [ ! -f "claude-dc-implementation/.env" ] && [ -f "/home/computeruse/secrets/palios-taey-secrets.json" ]; then
  echo "Creating .env file from secrets..."
  python3 -c "
import json
import os
with open('/home/computeruse/secrets/palios-taey-secrets.json', 'r') as f:
    secrets = json.load(f)
with open('claude-dc-implementation/.env', 'w') as f:
    f.write(f\"ANTHROPIC_API_KEY=\\\"{secrets['api_keys']['anthropic']}\\\"\n\")
    f.write(f\"GOOGLE_AI_STUDIO_KEY=\\\"{secrets['api_keys']['google_ai_studio']}\\\"\n\")
    f.write(f\"OPENAI_API_KEY=\\\"{secrets['api_keys']['openai']}\\\"\n\")
    f.write(f\"XAI_GROK_API_KEY=\\\"{secrets['api_keys']['xai_grok']}\\\"\n\")
    f.write(f\"GCP_PROJECT_ID=\\\"{secrets['gcp']['project_id']}\\\"\n\")
    f.write(f\"GCP_REGION=\\\"{secrets['gcp']['region']}\\\"\n\")
    f.write(f\"WEBHOOK_SECRET=\\\"{secrets['webhook']['secret']}\\\"\n\")
"
else
  echo "Skipping .env creation (already exists or secrets not found)"
fi

echo ""
echo "Setup complete!"

