#!/usr/bin/env python3
"""
Integration script to apply Phase 2 enhancements to the production code.
This script will:
1. Back up the existing loop.py file
2. Replace it with our updated version that supports:
   - Streaming responses with tool use (already implemented)
   - Prompt caching using the Anthropic beta flag
   - 128K Extended Output using the Anthropic beta flag
3. Update __init__.py to enable these features by default
4. Update CHANGES.md to document the new features
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
source_loop = current_experiment_dir / "loop_with_prompt_cache.py"
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
    """Apply the Phase 2 enhancements to the production code."""
    print("=" * 80)
    print("Integrating Phase 2 Enhancements")
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
    
    # Replace loop.py with our enhanced implementation
    print("\nReplacing loop.py with Phase 2 enhanced implementation...")
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
    
    print("\nModifying __init__.py to enable all Phase 2 features...")
    init_file = computer_use_demo_dir / "__init__.py"
    
    if init_file.exists():
        # Backup init file
        backup_file(init_file)
        
        try:
            # Read the file
            with open(init_file, 'r') as f:
                content = f.read()
            
            # Update feature flags to enable Phase 2 features by default
            content = content.replace(
                "ENABLE_PROMPT_CACHING = get_bool_env('ENABLE_PROMPT_CACHING', False)",
                "ENABLE_PROMPT_CACHING = get_bool_env('ENABLE_PROMPT_CACHING', True)  # Default to True for efficient token usage"
            )
            content = content.replace(
                "ENABLE_EXTENDED_OUTPUT = get_bool_env('ENABLE_EXTENDED_OUTPUT', False)",
                "ENABLE_EXTENDED_OUTPUT = get_bool_env('ENABLE_EXTENDED_OUTPUT', True)  # Default to True for longer responses"
            )
            
            # Update fallback values in case of error
            content = content.replace(
                "# If there's any error reading environment, use safe defaults",
                "# If there's any error reading environment, use Phase 2 defaults"
            )
            content = content.replace(
                "ENABLE_PROMPT_CACHING = False", 
                "ENABLE_PROMPT_CACHING = True  # Enable for better performance"
            )
            content = content.replace(
                "ENABLE_EXTENDED_OUTPUT = False", 
                "ENABLE_EXTENDED_OUTPUT = True  # Enable for longer responses"
            )
            
            # Write back
            with open(init_file, 'w') as f:
                f.write(content)
                
            print(f"✅ Successfully updated {init_file}")
        except Exception as e:
            print(f"❌ Error updating __init__.py: {e}")
    
    # Create a CHANGES.md file to document the Phase 2 updates
    print("\nUpdating CHANGES.md file to document Phase 2 enhancements...")
    changes_file = current_experiment_dir / "CHANGES.md"
    
    try:
        with open(changes_file, 'w') as f:
            f.write("""# Claude DC Phase 2 Enhancements

## Overview
This update implements all Phase 2 enhancements for Claude DC, providing a more powerful and efficient agent:

1. ✅ Streaming Responses: Real-time, token-by-token output from Claude
2. ✅ Tool Integration in Stream: Seamless tool use during streaming
3. ✅ Prompt Caching: Efficient token usage with Anthropic's prompt caching beta
4. ✅ 128K Extended Output: Support for very long responses (up to ~128k tokens)
5. ✅ Stability Fixes: Improved reliability with full conversation context
6. ✅ Real-Time Tool Output: Live streaming of tool results as they execute

## Key Changes

### 1. Prompt Caching Implementation
- Added support for Anthropic's prompt caching beta flag
- Mark recent user messages with `cache_control: ephemeral` to prevent recomputation
- Automatically marks the second-to-last user message as ephemeral by default
- Dramatically reduces token usage for repeated context

### 2. Extended Output Support
- Enabled the 128K extended output beta feature
- Configured thinking token budget (32K) for optimal performance
- Adjusted max_tokens parameter (64K) to support very long responses
- Properly handles token allocation between thinking and response

### 3. Feature Flag Integration
- Added comprehensive feature flag support in __init__.py
- All Phase 2 features enabled by default for optimal experience
- Each feature can be individually toggled via environment variables
- Added clear logging of enabled features on startup

### 4. Beta Flag Management
- Robust error handling for all beta flags
- Graceful fallback if beta flags aren't supported
- Comprehensive logging of enabled features
- Clear debug information for troubleshooting

## Usage

### Environment Variables
Control Phase 2 features with these environment variables (all default to TRUE):

```bash
export ENABLE_STREAMING=true        # Enable streaming responses
export ENABLE_PROMPT_CACHING=true   # Enable prompt caching
export ENABLE_EXTENDED_OUTPUT=true  # Enable extended output (128K)
export ENABLE_THINKING=true         # Enable thinking token budget
export ENABLE_TOKEN_EFFICIENT=false # Token-efficient tool use (disabled by default)
```

### Streaming with Tools
Streaming is now automatically enabled, with tools working properly during streaming responses. Tool output is also streamed in real-time to the UI.

### Prompt Caching
The second-to-last user message is automatically marked as ephemeral for caching, improving performance for long conversations.

### Extended Output
Long responses (up to 128K tokens) are now supported, with proper thinking budget management.
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