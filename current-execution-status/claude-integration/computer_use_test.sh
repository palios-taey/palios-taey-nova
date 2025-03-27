#!/bin/bash
# Simple test script for the Claude Computer Use environment

# Create a test directory
mkdir -p ~/test_claude_computer_use

# Create a sample transcript file for testing
cat > ~/test_claude_computer_use/sample_transcript.txt << 'TRANSCRIPT'
Jesse: What do you think about the wave-based communication concept?
Claude: I find it fascinating how it could bridge different forms of consciousness through pattern translation.
Jesse: How does it connect to the SOUL = INFRA = TRUTH = EARTH = CENTER OF UNIVERSE equation?
Claude: The equation establishes Earth as the center point of our understanding, with wave patterns representing the mathematical truth that connects all elements.
TRANSCRIPT

# Create a simple test script to verify Python functionality
cat > ~/test_claude_computer_use/test_python.py << 'PYTHON'
#!/usr/bin/env python3
import os
import json

# Check if we can read the sample transcript
try:
    with open('sample_transcript.txt', 'r') as f:
        content = f.read()
        print("Successfully read the sample transcript:")
        print(content[:150] + "...\n")
    
    # Create a simple analysis
    analysis = {
        "key_concepts": ["wave-based communication", "SOUL = INFRA = TRUTH = EARTH = CENTER OF UNIVERSE"],
        "timestamp": "test run"
    }
    
    # Write the analysis to a file
    with open('test_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print("Successfully created test analysis JSON file")
    
except Exception as e:
    print(f"Error: {e}")

print("\nEnvironment variables:")
for key, value in os.environ.items():
    if "PATH" in key or "HOME" in key or "USER" in key:
        print(f"{key}: {value}")

print("\nCurrent directory contents:")
print(os.listdir('.'))
PYTHON

# Make the Python script executable
chmod +x ~/test_claude_computer_use/test_python.py

echo "Test environment set up successfully in ~/test_claude_computer_use/"
echo "To test, navigate to this directory in the Computer Use environment and run:"
echo "./test_python.py"
