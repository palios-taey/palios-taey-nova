#!/usr/bin/env python3
"""
Utility script to help locate the computer_use_demo module
and its tools in the container environment.
"""

import os
import sys
import importlib
from pathlib import Path

def find_module(module_name):
    """Attempt to find and import a module."""
    print(f"Trying to import {module_name}...")
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        print(f"   Module location: {module.__file__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False

def search_for_directory(directory_name, start_path="/home/computeruse"):
    """Search for a directory with the given name."""
    print(f"Searching for directory: {directory_name} starting from {start_path}")
    
    matches = []
    for root, dirs, files in os.walk(start_path):
        if directory_name in dirs:
            full_path = os.path.join(root, directory_name)
            matches.append(full_path)
            print(f"✅ Found matching directory: {full_path}")
    
    if not matches:
        print(f"❌ No directories named {directory_name} found")
    
    return matches

def main():
    """Run the module finder."""
    print("=" * 80)
    print("Module Finder Utility")
    print("=" * 80)
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Display PYTHONPATH
    python_path = os.environ.get("PYTHONPATH", "")
    print(f"PYTHONPATH: {python_path}")
    
    # Display sys.path
    print("\nPython Path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # Try to import key modules
    print("\nTrying to import key modules:")
    find_module("anthropic")
    find_module("computer_use_demo")
    find_module("computer_use_demo.tools")
    
    # Search for the tools directory
    print("\nSearching for tools directory:")
    
    # Define common paths to check
    paths_to_check = [
        "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo",
        "/home/computeruse/github/palios-taey-nova/claude-dc-implementation",
        "/home/computeruse/github/palios-taey-nova"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"\nChecking path: {path}")
            print(f"Contents: {os.listdir(path)}")
            
            # Look for tools directory
            tools_path = os.path.join(path, "tools")
            if os.path.exists(tools_path):
                print(f"✅ Found tools directory at: {tools_path}")
                print(f"Contents: {os.listdir(tools_path)}")
    
    # Search for computer_use_demo
    print("\nSearching for computer_use_demo directory:")
    search_for_directory("computer_use_demo")
    
    # Search for tools
    print("\nSearching for tools directory:")
    search_for_directory("tools")

if __name__ == "__main__":
    main()