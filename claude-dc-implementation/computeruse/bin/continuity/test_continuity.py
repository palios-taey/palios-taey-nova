#!/usr/bin/env python3
"""
Test script for the Streamlit continuity solution.
This script simulates a file change and tests the save/restore mechanism.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent.absolute()
TEST_STATE_FILE = "/tmp/test_continuity_state.json"
TEST_FILE = SCRIPT_DIR / "test_file_for_continuity.py"
ORIGINAL_CONTENT = """#!/usr/bin/env python3
\"\"\"
Test file for continuity mechanism.
Original version.
\"\"\"

def main():
    print("This is the original version")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
MODIFIED_CONTENT = """#!/usr/bin/env python3
\"\"\"
Test file for continuity mechanism.
Modified version.
\"\"\"

def main():
    print("This is the modified version")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

def setup_test_environment():
    """Set up the test environment with the original test file"""
    print("Setting up test environment...")
    
    # Create the test file with original content
    with open(TEST_FILE, 'w') as f:
        f.write(ORIGINAL_CONTENT)
    
    print(f"Created test file: {TEST_FILE}")
    return True

def cleanup_test_environment():
    """Clean up the test environment"""
    print("Cleaning up test environment...")
    
    # Remove the test file
    if TEST_FILE.exists():
        TEST_FILE.unlink()
        print(f"Removed test file: {TEST_FILE}")
    
    # Remove the test state file
    if os.path.exists(TEST_STATE_FILE):
        os.unlink(TEST_STATE_FILE)
        print(f"Removed test state file: {TEST_STATE_FILE}")
    
    return True

def save_state():
    """Save the conversation state"""
    print("Saving conversation state...")
    
    # Run the save_conversation_state.py script
    save_script = SCRIPT_DIR / "save_conversation_state.py"
    if not save_script.exists():
        print(f"Error: Save script not found: {save_script}")
        return False
    
    try:
        subprocess.run(
            [sys.executable, str(save_script), "--output", TEST_STATE_FILE],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Conversation state saved to {TEST_STATE_FILE}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error saving state: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def modify_file():
    """Modify the test file to simulate a code change"""
    print("Modifying test file...")
    
    # Save a backup of the original file
    backup_file = str(TEST_FILE) + ".bak"
    shutil.copy2(TEST_FILE, backup_file)
    print(f"Created backup: {backup_file}")
    
    # Modify the file
    with open(TEST_FILE, 'w') as f:
        f.write(MODIFIED_CONTENT)
    
    print(f"Modified test file: {TEST_FILE}")
    return True

def restore_state():
    """Restore the conversation state"""
    print("Restoring conversation state...")
    
    # Run the restore_conversation_state.py script
    restore_script = SCRIPT_DIR / "restore_conversation_state.py"
    if not restore_script.exists():
        print(f"Error: Restore script not found: {restore_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(restore_script), "--input", TEST_STATE_FILE, "--preview"],
            check=True,
            capture_output=True,
            text=True
        )
        print("State restoration preview:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restoring state: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def test_continuity():
    """Run the full continuity test"""
    print("=" * 80)
    print("Streamlit Continuity Test")
    print("=" * 80)
    
    # Setup test environment
    if not setup_test_environment():
        print("Failed to set up test environment")
        return False
    
    try:
        # Step 1: Save the state
        if not save_state():
            print("Failed to save state")
            return False
        
        # Step 2: Modify the file (simulating a code change)
        if not modify_file():
            print("Failed to modify test file")
            return False
        
        # Step 3: Restore the state
        if not restore_state():
            print("Failed to restore state")
            return False
        
        print("\nContinuity test completed successfully!")
        print("The mechanism would allow preserving context across file changes.")
        return True
        
    finally:
        # Always clean up
        cleanup_test_environment()

if __name__ == "__main__":
    success = test_continuity()
    sys.exit(0 if success else 1)