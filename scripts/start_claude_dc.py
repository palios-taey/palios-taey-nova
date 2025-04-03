#!/usr/bin/env python3
# start_claude_dc.py

import os
import sys
import subprocess

# Set environment variables to force streaming
os.environ["ANTHROPIC_FORCE_STREAMING"] = "true"

# Define a minimal initial prompt
minimal_prompt = """
Claude DC,

I'll provide a more detailed directive soon, but first I need to confirm you can process messages without hitting the streaming timeout error. Please respond with a simple confirmation that you're operational and ready to receive the full implementation directive.

Jesse
"""

# Launch Claude DC with the minimal prompt
subprocess.run(["python3", "/home/computeruse/computer_use_demo/streamlit.py"], 
               env=os.environ)

print("Started Claude DC with minimal prompt")
