#!/bin/bash
# Script to run the Streamlit UI for Claude DC

# Usage information
show_help() {
  echo "Usage: ./run_streamlit.sh [OPTIONS]"
  echo "Run the Claude DC Streamlit UI"
  echo ""
  echo "Options:"
  echo "  --test      Run tests before starting"
  echo "  --help      Show this help message"
  echo ""
  echo "Environment variables:"
  echo "  ANTHROPIC_API_KEY  Your Anthropic API key (required)"
  echo ""
  echo "Example:"
  echo "  ANTHROPIC_API_KEY=sk_ant_... ./run_streamlit.sh"
}

# Check for API key
if [ -z "${ANTHROPIC_API_KEY}" ]; then
  echo "Error: ANTHROPIC_API_KEY environment variable is not set."
  echo "Please set your API key before running:"
  echo "  ANTHROPIC_API_KEY=sk_ant_... ./run_streamlit.sh"
  exit 1
fi

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --test)
      RUN_TESTS=true
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Check if required packages are installed
check_dependencies() {
  echo "Checking dependencies..."
  pip install -q -r requirements.txt
  if [ $? -ne 0 ]; then
    echo "Error installing dependencies. Please check requirements.txt."
    exit 1
  fi
  echo "Dependencies installed successfully."
}

# Run tests if requested
run_tests() {
  echo "Running implementation tests..."
  python3 test_implementation.py
  if [ $? -ne 0 ]; then
    echo "Some tests failed. Do you want to continue anyway? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
      echo "Exiting."
      exit 1
    fi
  else
    echo "All tests passed!"
  fi
}

# Start the Streamlit app
start_streamlit() {
  echo "Starting Streamlit app..."
  streamlit run streamlit_app.py
}

# Main script
echo "Claude DC Streamlit Launcher"
echo "--------------------------"

# Install dependencies
check_dependencies

# Run tests if requested
if [ "${RUN_TESTS}" = true ]; then
  run_tests
fi

# Start Streamlit
start_streamlit