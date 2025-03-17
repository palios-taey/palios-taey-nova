#!/bin/bash

echo "Checking local environment..."

# Check Python version
python --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python -m venv venv
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install requirements
  pip install -r requirements.txt
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
python -m flask run --host=0.0.0.0 --port=8080
