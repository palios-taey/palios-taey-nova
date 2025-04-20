#!/bin/bash
# Simple wrapper script to launch Claude DC
# This script launches the container and then runs the setup script

set -e  # Exit on error

echo "==================================================="
echo "       Claude DC Launcher - Simplified Version"
echo "==================================================="

# First, launch the container using the standard script
echo "Step 1: Launching Computer Use container..."
./current-execution-status/claude-integration/launch_computer_use.sh

# Container started! The script should automatically attach
# to the container's terminal. From there, run:
#
# cd github/palios-taey-nova && ./claude_dc_setup.sh
#
# This will configure Claude DC inside the container
# with the desired features enabled.