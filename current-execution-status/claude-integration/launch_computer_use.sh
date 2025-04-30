#!/bin/bash
# Script to launch the Claude Computer Use Development environment

echo "Stopping any existing computer-use containers..."
docker ps -a | grep computer-use-demo | awk '{print $1}' | xargs -r docker stop
echo "Removing stopped containers..."
docker ps -a | grep computer-use-demo | awk '{print $1}' | xargs -r docker rm

# Change to the anthropic-quickstarts computer-use-demo directory
cd /home/jesse/projects/anthropic-quickstarts/computer-use-demo

./setup.sh  # configure venv, install development dependencies, and install pre-commit hooks
docker build . -t computer-use-demo:local  # manually build the docker image (optional)
export ANTHROPIC_API_KEY=%your_api_key%
docker run \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -v $(pwd)/computer_use_demo:/home/computeruse/computer_use_demo/ `# mount local python module for development` \
    -v $HOME/.anthropic:/home/computeruse/.anthropic \
    -p 5900:5900 \
    -p 8501:8501 \
    -p 6080:6080 \
    -p 8080:8080 \
    -it computer-use-demo:local  # can also use ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

echo "Computer Use development environment started!"
echo "Access the demo UI at http://localhost:8080"
echo "For VNC access: http://localhost:6080"
echo "For Streamlit access: http://localhost:8501"
