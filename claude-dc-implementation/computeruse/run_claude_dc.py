#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now run the module properly
os.environ["PYTHONPATH"] = current_dir
subprocess.run(["python", "-m", "computer_use_demo.streamlit"], check=True)
