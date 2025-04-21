#!/usr/bin/env python3
"""
Integration script to apply the streaming changes to the production code.
This script will:
1. Back up the existing loop.py and streamlit.py files
2. Replace them with our updated versions that support streaming
"""

import os
import sys
import shutil
import datetime
from pathlib import Path

# Determine paths based on environment
if os.path.exists("/home/computeruse"):
    # We're in the container
    repo_root = Path("/home/computeruse/github/palios-taey-nova")
else:
    # We're on the host
    repo_root = Path("/home/jesse/projects/palios-taey-nova")

claude_dc_root = repo_root / "claude-dc-implementation"
computer_use_demo_dir = claude_dc_root / "computeruse/computer_use_demo"
current_experiment_dir = claude_dc_root / "computeruse/current_experiment"

# Source and destination files
source_loop = current_experiment_dir / "production_ready_loop.py"
dest_loop = computer_use_demo_dir / "loop.py"

# Create timestamp for backups
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_file(file_path):
    """Create a backup of a file with timestamp."""
    if file_path.exists():
        backup_path = file_path.parent / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    else:
        print(f"File not found: {file_path}")
        return False

def main():
    """Apply the streaming changes to the production code."""
    print("=" * 80)
    print("Integrating Streaming Functionality")
    print("=" * 80)
    
    # Check if source files exist
    if not source_loop.exists():
        print(f"ERROR: Source loop file not found: {source_loop}")
        return False
    
    # Backup existing files
    print("\nBacking up existing files...")
    loop_backed_up = backup_file(dest_loop)
    if not loop_backed_up:
        print("WARNING: Could not backup loop.py, it may not exist")
    
    # Replace loop.py with our streaming implementation
    print("\nReplacing loop.py with streaming implementation...")
    try:
        # Copy the file
        shutil.copy2(source_loop, dest_loop)
        print(f"✅ Successfully replaced {dest_loop}")
        
        # Make executable
        os.chmod(dest_loop, 0o755)
        print(f"✅ Made {dest_loop} executable")
    except Exception as e:
        print(f"❌ Error replacing loop.py: {e}")
        return False
    
    print("\nModifying __init__.py to enable streaming by default...")
    init_file = computer_use_demo_dir / "__init__.py"
    
    if init_file.exists():
        # Backup init file
        backup_file(init_file)
        
        try:
            # Read the file
            with open(init_file, 'r') as f:
                content = f.read()
            
            # Modify to enable streaming by default
            if "ENABLE_STREAMING" in content:
                # Replace or add ENABLE_STREAMING setting
                if "ENABLE_STREAMING = " in content:
                    content = content.replace(
                        "ENABLE_STREAMING = False", 
                        "ENABLE_STREAMING = True  # Always enable streaming for tool use"
                    )
                    content = content.replace(
                        "ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', False)",
                        "ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to True for streaming"
                    )
                else:
                    # Add it if not found
                    import_section = "import os\nimport logging\n"
                    replacement = import_section + "import sys\nfrom pathlib import Path\n\n"
                    content = content.replace(import_section, replacement)
                    
                    # Add after other ENABLE_ variables
                    if "ENABLE_" in content:
                        lines = content.split("\n")
                        new_lines = []
                        inserted = False
                        
                        for line in lines:
                            new_lines.append(line)
                            # Add after last ENABLE_ line
                            if not inserted and "ENABLE_" in line and not "ENABLE_STREAMING" in line and line.strip().endswith(")"):
                                new_lines.append("# Streaming is now a core feature, not a beta flag")
                                new_lines.append("ENABLE_STREAMING = get_bool_env('ENABLE_STREAMING', True)  # Default to True - this is a key feature")
                                inserted = True
                        
                        content = "\n".join(new_lines)
            
            # Write back
            with open(init_file, 'w') as f:
                f.write(content)
                
            print(f"✅ Successfully updated {init_file}")
        except Exception as e:
            print(f"❌ Error updating __init__.py: {e}")
    
    # Create a CHANGES.md file to document the update
    print("\nCreating CHANGES.md file to document updates...")
    changes_file = current_experiment_dir / "CHANGES.md"
    
    try:
        with open(changes_file, 'w') as f:
            f.write("""# Claude DC Streaming Implementation

## Overview
This update adds reliable streaming functionality to Claude DC. The implementation:

1. Makes streaming a core feature that's always enabled by default
2. Simplifies the handling of beta flags to avoid compatibility issues
3. Ensures tool use works properly with streaming responses

## Key Changes

### 1. Simplified API Integration
- Removed conditional streaming logic, now streaming is always enabled
- Added robust error handling for beta flags and thinking parameters
- Made the streaming code more resilient to SDK version differences

### 2. Tool Integration
- Ensured tools work properly during streaming
- Added support for streaming tool outputs in real-time

### 3. Configuration
- Set ENABLE_STREAMING to default to True in the configuration

## Testing
The implementation was thoroughly tested with a minimal approach to ensure reliability:
1. First verified streaming worked without beta flags
2. Then tested streaming with tool use
3. Finally integrated the full streaming implementation with beta features

## Usage
Streaming is now automatically enabled for all Claude DC interactions.
Tools will work correctly during streaming, with outputs shown in real-time.
""")
        print(f"✅ Created {changes_file}")
    except Exception as e:
        print(f"❌ Error creating CHANGES.md: {e}")
    
    print("\nIntegration complete!")
    print("Please restart Claude DC for the changes to take effect.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)