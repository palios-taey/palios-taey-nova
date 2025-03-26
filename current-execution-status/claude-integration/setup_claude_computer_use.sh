# Claude Computer Use Setup Script for System76 (Pop!_OS)
# This script will set up the Docker environment for Claude's Computer Use feature

# Step 1: Install Docker if not already installed
echo "Checking for Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    
    # Update package lists
    sudo apt update
    
    # Install prerequisites
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update packages again
    sudo apt update
    
    # Install Docker Engine
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group to avoid using sudo
    sudo usermod -aG docker $USER
    
    echo "Docker installed successfully. You may need to log out and back in for group changes to take effect."
else
    echo "Docker is already installed."
fi

# Step 2: Configure Environment for Claude Computer Use
echo "Setting up environment for Claude Computer Use..."

# Create directory for Claude API key
mkdir -p $HOME/.anthropic

# Prompt for API key if not already set
if [ ! -f $HOME/.anthropic/api_key ]; then
    echo "Please enter your Anthropic API key:"
    read API_KEY
    echo "$API_KEY" > $HOME/.anthropic/api_key
    echo "API key saved to $HOME/.anthropic/api_key"
else
    echo "API key file already exists."
fi

# Set up environment variable
export ANTHROPIC_API_KEY=$(cat $HOME/.anthropic/api_key)

# Step 3: Pull and run the Computer Use demo container
echo "Pulling the Claude Computer Use demo container..."
docker pull ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

echo "Running the Claude Computer Use demo container..."
docker run \
   -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
   -v $HOME/.anthropic:/home/computeruse/.anthropic \
   -p 5900:5900 \
   -p 8501:8501 \
   -p 6080:6080 \
   -p 8080:8080 \
   -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

# Note: The script will pause here as the container runs in the foreground
# Press Ctrl+C to stop the container when done

echo "Setup complete! Access the demo UI at http://localhost:8080"
echo "For VNC access: http://localhost:6080"
echo "For Streamlit access: http://localhost:8501"
