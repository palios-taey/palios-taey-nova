#!/usr/bin/env python3
# fix_streaming_error.py

import os
import re

# Path to loop.py
LOOP_PY_PATH = "/home/computeruse/computer_use_demo/loop.py"

# Read the current file
with open(LOOP_PY_PATH, 'r') as f:
    content = f.read()

# Check if the problematic line exists
if '_calculate_nonstreaming_timeout' in content:
    print("Found problematic timeout calculation - modifying file")
    
    # Replace the specific parts causing issues
    fixed_content = re.sub(
        r'timeout = self\._client\._calculate_nonstreaming_timeout\(max_tokens\)', 
        'timeout = None  # Disable timeout calculation for long operations', 
        content
    )
    
    # Make another crucial modification to avoid calling _calculate_nonstreaming_timeout
    fixed_content = re.sub(
        r'client\.beta\.messages\.with_streaming_response\.create\(',
        'client.beta.messages.with_streaming_response.create(\n                timeout=None,',
        fixed_content
    )
    
    # Write the updated content
    with open(LOOP_PY_PATH, 'w') as f:
        f.write(fixed_content)
        
    print("Successfully patched timeout calculation in loop.py")
else:
    print("Could not find problematic timeout calculation - file may have been updated differently")

print("Run check complete - please restart Claude DC")
