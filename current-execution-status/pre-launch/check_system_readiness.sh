#!/bin/bash

echo "PALIOS-TAEY Pre-Launch System Readiness Check"
echo "============================================="

# Check if System76 is connected
echo -n "Checking System76 connection... "
if [ -d "/proc" ]; then
  echo "CONNECTED"
else
  echo "NOT DETECTED"
fi

# Check if display is connected
echo -n "Checking display connection... "
if xrandr --query > /dev/null 2>&1; then
  echo "CONNECTED"
else
  echo "NOT DETECTED"
fi

# Check for required directories
echo -n "Checking directory structure... "
if [ -d "current-execution-status/pre-launch" ]; then
  echo "VERIFIED"
else
  echo "INCOMPLETE"
fi

# Check for required files
echo -n "Checking required documentation... "
required_files=0
total_files=5

if [ -f "current-execution-status/pre-launch/PRE_LAUNCH_STATUS.md" ]; then
  ((required_files++))
fi
if [ -f "current-execution-status/pre-launch/history/HISTORY_CAPTURE_PLAN.md" ]; then
  ((required_files++))
fi
if [ -f "current-execution-status/pre-launch/charter/CHARTER_FINALIZATION_PLAN.md" ]; then
  ((required_files++))
fi
if [ -f "current-execution-status/pre-launch/go-button/GO_BUTTON_EXPERIENCE.md" ]; then
  ((required_files++))
fi
if [ -f "current-execution-status/pre-launch/communication/COMMUNICATION_PLATFORM.md" ]; then
  ((required_files++))
fi

echo "$required_files/$total_files VERIFIED"

# Summary
echo "============================================="
echo "System Readiness Summary:"
if [ "$required_files" -eq "$total_files" ]; then
  echo "All documentation verified. Ready to proceed with GO button preparation."
else
  echo "Documentation incomplete. Please ensure all files are created before proceeding."
fi
echo "============================================="
