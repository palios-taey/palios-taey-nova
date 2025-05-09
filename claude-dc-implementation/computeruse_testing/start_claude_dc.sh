#!/bin/bash
# Ultra simple direct launcher for Claude DC

echo "Starting Claude DC..."
cd /home/computeruse
python direct_start.py

# If that fails, try the basic approach
if [ $? -ne 0 ]; then
  echo "Direct start failed, trying alternative approach..."
  cd /home/computeruse/computer_use_demo
  streamlit run claude_ui.py
fi