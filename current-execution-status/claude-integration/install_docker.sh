#!/bin/bash
# Script to install Docker on Pop!_OS

echo "Installing Docker on Pop!_OS..."

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

echo "Docker installed successfully!"
echo "You may need to log out and back in for group changes to take effect."
echo "After logging back in, run the launch_computer_use.sh script again."
