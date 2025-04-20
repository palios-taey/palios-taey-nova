#!/bin/bash
# Claude DC Quick Setup Script
# This script sets up and runs Claude DC with Phase 2 enhancements

set -e  # Exit on error

REPO_ROOT="/home/jesse/projects/palios-taey-nova"
LAUNCH_HELPERS="$REPO_ROOT/launch_helpers"

# Display header
echo "====================================================="
echo "       Claude DC Quick Setup - Phase 2 Enhanced      "
echo "====================================================="
echo

# Step 1: Run the setup script to prepare Claude DC
echo "Step 1: Setting up Claude DC environment..."
$LAUNCH_HELPERS/setup_claude_dc.sh

# Step 2: Validate the Claude DC installation
echo
echo "Step 2: Validating Claude DC configuration..."
$LAUNCH_HELPERS/validate_claude_dc.py

# Check if validation succeeded
if [ $? -ne 0 ]; then
    echo
    echo "❌ Validation failed. Please check the errors above."
    echo "You can manually fix the issues and run the validation again with:"
    echo "  $LAUNCH_HELPERS/validate_claude_dc.py"
    exit 1
fi

# Step 3: Launch Claude DC
echo
echo "Step 3: Launching Claude DC..."
echo "Launch options:"
echo "  1) Streamlit UI (recommended)"
echo "  2) Console Mode"
echo "  3) Exit without launching"
echo
read -p "Choose an option (1-3): " launch_option

case $launch_option in
    1)
        echo "Launching Streamlit UI..."
        $REPO_ROOT/claude_dc_launch.sh
        ;;
    2)
        echo "Launching Console Mode..."
        $REPO_ROOT/claude_dc_launch.sh --mode console
        ;;
    3)
        echo "Claude DC is set up but not launched."
        echo "You can run it later with: $REPO_ROOT/claude_dc_launch.sh"
        ;;
    *)
        echo "Invalid option. Claude DC is set up but not launched."
        echo "You can run it later with: $REPO_ROOT/claude_dc_launch.sh"
        ;;
esac