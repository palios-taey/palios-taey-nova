# Testing Phase 2 Enhancements for Claude DC

This document explains how to test the Phase 2 enhancements for Claude DC, even if Docker is not available or is having issues in your environment.

## Overview

The Phase 2 enhancements include:
1. Streaming responses
2. Tool integration in streaming
3. Prompt caching
4. Extended 128k output
5. Real-time tool output streaming

## Testing Options

We provide two approaches for testing:

### Option 1: Docker Container Testing (Preferred)

If Docker is functioning correctly:

```bash
# Set your API key
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Run the development container
cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/
./run_dev_container.sh

# Test the environment
./test_dev_environment.py
```

### Option 2: Local Testing (Fallback)

If Docker is not available or not working:

```bash
# Set your API key
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Run the setup script (it will detect Docker issues and switch to local mode)
cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/
./run_dev_container.sh

# Test with local mode explicitly
./test_dev_environment.py --local

# Run specific Phase 2 feature tests
./test_phase2_features.py
```

## Testing Without Modifying Your Environment

If you want to test the code without affecting your current environment at all:

```bash
# Create a test directory
mkdir -p /home/computeruse/test_environment

# Copy the enhanced code
cp -r /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo/* /home/computeruse/test_environment/

# Run tests on the copied code
cd /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/
./test_phase2_features.py --test-dir=/home/computeruse/test_environment
```

## Understanding Test Results

The test scripts will output clear PASS/FAIL indicators for each feature being tested. A summary will be shown at the end with an overall assessment.

A JSON report file `phase2_test_report.json` will be created in the test directory with detailed results.

## Deploying After Successful Testing

Only once testing passes, you can deploy to your live environment:

```bash
# First, back up your current environment
/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/backup_current_env.sh

# Deploy the updates
/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/deploy_to_production.sh
```

## Troubleshooting

If you encounter issues:

1. Check logs for specific error messages
2. Try the local testing mode if Docker is problematic
3. Ensure your API key is properly set
4. Verify all Python dependencies are installed (streamlit, httpx, etc.)
5. Check file permissions (use `chmod +x` on scripts if needed)