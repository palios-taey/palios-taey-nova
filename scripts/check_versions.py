#!/usr/bin/env python3
# check_versions.py

import sys
import importlib

def check_module_version(module_name):
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"{module_name}: {version}")
    except ImportError:
        print(f"{module_name}: Not installed")

print(f"Python version: {sys.version}")
check_module_version('anthropic')
check_module_version('httpx')
