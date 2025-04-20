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
    python3-apt \
    system76-driver \
    python3-systemd \
    ubuntu-drivers-common \
    ufw \
    xkit


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

sudo apt-get install -y rsync

# Python environment setup
echo "Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r claude-dc-implementation/requirements.txt

# Install spaCy language model
echo "Installing spaCy model..."
python -m spacy download en_core_web_md

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

