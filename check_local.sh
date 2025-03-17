#!/bin/bash

echo "Checking local environment..."

# Check Python version - using explicit python3 command
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install requirements
  pip3 install -r requirements.txt
else
  # Activate existing virtual environment
  source venv/bin/activate
fi

# Run the fix environment script
./fix_environment_config.sh

# Run application locally
export USE_MOCK_RESPONSES=true
export ENVIRONMENT=development
export PORT=8080

echo "Starting application locally..."
cd src
python3 -m flask run --host=0.0.0.0 --port=8080
