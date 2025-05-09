#!/usr/bin/env python3
"""
Test script to verify ComputerTool works with our fix
"""

import os
import sys
from pathlib import Path

# Add required paths to sys.path
REPO_ROOT = Path('/home/jesse/projects/palios-taey-nova')
CLAUDE_DC_ROOT = REPO_ROOT / 'claude-dc-implementation'
COMPUTER_USE_DEMO = CLAUDE_DC_ROOT / 'computeruse'

# Add paths to Python path
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CLAUDE_DC_ROOT))
sys.path.insert(0, str(COMPUTER_USE_DEMO))

# Now import the module we want to test
from computer_use_demo.tools.computer import BaseComputerTool

print("Testing ComputerTool initialization with different environment settings:")

# Test 1: Without environment variables
if "WIDTH" in os.environ:
    del os.environ["WIDTH"]
if "HEIGHT" in os.environ:
    del os.environ["HEIGHT"]
if "DISPLAY_NUM" in os.environ:
    del os.environ["DISPLAY_NUM"]

print("\nTest 1: No environment variables")
try:
    tool = BaseComputerTool()
    print(f"SUCCESS: Tool initialized with width={tool.width}, height={tool.height}, display_num={tool.display_num}")
except Exception as e:
    print(f"FAILURE: {e}")

# Test 2: With custom environment variables
os.environ["WIDTH"] = "1280"
os.environ["HEIGHT"] = "800"
os.environ["DISPLAY_NUM"] = "2"

print("\nTest 2: Custom environment variables")
try:
    tool = BaseComputerTool()
    print(f"SUCCESS: Tool initialized with width={tool.width}, height={tool.height}, display_num={tool.display_num}")
except Exception as e:
    print(f"FAILURE: {e}")

# Test 3: With invalid environment variables
os.environ["WIDTH"] = "foo"
os.environ["HEIGHT"] = "bar"
os.environ["DISPLAY_NUM"] = "baz"

print("\nTest 3: Invalid environment variables")
try:
    tool = BaseComputerTool()
    print(f"SUCCESS: Tool initialized with width={tool.width}, height={tool.height}, display_num={tool.display_num}")
except Exception as e:
    print(f"FAILURE: {e}")

print("\nAll tests completed.")