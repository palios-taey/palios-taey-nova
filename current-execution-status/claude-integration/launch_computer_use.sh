#!/bin/bash
# Script to launch the Claude Computer Use environment

echo "Stopping any existing computer-use containers..."
docker ps -a | grep computer-use-demo | awk '{print $1}' | xargs -r docker stop
echo "Removing stopped containers..."
docker ps -a | grep computer-use-demo | awk '{print $1}' | xargs -r docker rm

# Check if ANTHROPIC_API_KEY is already set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    # Try to read from file
    if [ -f "$HOME/.anthropic/api_key" ]; then
        export ANTHROPIC_API_KEY=$(cat $HOME/.anthropic/api_key)
    else
        echo "Please enter your Anthropic API key:"
        read API_KEY
        mkdir -p $HOME/.anthropic
        echo "$API_KEY" > $HOME/.anthropic/api_key
        export ANTHROPIC_API_KEY="$API_KEY"
    fi
fi

# Create transcripts directory if it doesn't exist
mkdir -p $HOME/transcripts


# Run the Computer Use container
docker run \
   -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
   -v $HOME/.anthropic:/home/computeruse/.anthropic \
   -v $HOME/transcripts:/home/computeruse/transcripts \
   -v $HOME/projects/palios-taey-nova:/home/computeruse/github/palios-taey-nova \
   -p 5900:5900 \
   -p 8501:8501 \
   -p 6080:6080 \
   -p 8080:8080 \
   -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

echo "Computer Use environment started!"
echo "Access the demo UI at http://localhost:8080"
echo "For VNC access: http://localhost:6080"
echo "For Streamlit access: http://localhost:8501"
