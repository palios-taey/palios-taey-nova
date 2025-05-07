#!/usr/bin/env python3
"""
Deployment script for updating streamlit.py to support streaming.

This script safely modifies streamlit.py to integrate with the streaming implementation
while maintaining backward compatibility.
"""

import os
import sys
import shutil
from pathlib import Path
import datetime

def backup_file(file_path):
    """Create a backup of the specified file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def deploy_streaming_streamlit():
    """Deploy streaming integration to streamlit.py."""
    
    # Define paths
    streamlit_path = Path("/home/computeruse/computer_use_demo/streamlit.py")
    
    # Verify files exist
    if not streamlit_path.exists():
        print(f"Error: {streamlit_path} not found")
        return False
    
    # Create backup
    backup_path = backup_file(streamlit_path)
    
    # Read the original streamlit.py
    with open(streamlit_path, "r") as f:
        streamlit_content = f.read()
    
    # Prepare the modified content
    modified_content = streamlit_content
    
    # Update import for streaming integration
    original_import = "from computer_use_demo.loop import (\n    APIProvider,\n    sampling_loop,\n)"
    streaming_import = "from computer_use_demo.loop import (\n    APIProvider,\n    sampling_loop,\n)\nfrom computer_use_demo.streaming_integration import is_feature_enabled"
    
    if original_import in modified_content:
        modified_content = modified_content.replace(original_import, streaming_import)
    else:
        print("Warning: Could not find expected import pattern. Manual verification needed.")
    
    # Add streaming status display to the sidebar
    # Find the settings section in the sidebar
    sidebar_pattern = "st.sidebar.title(\"Settings\")"
    streaming_status = '''st.sidebar.title("Settings")

# Add streaming status display
streaming_enabled = is_feature_enabled("use_unified_streaming")
streaming_bash = is_feature_enabled("use_streaming_bash")
streaming_file = is_feature_enabled("use_streaming_file")
streaming_thinking = is_feature_enabled("use_streaming_thinking")

with st.sidebar.expander("Streaming Status", expanded=False):
    st.write(f"Unified Streaming: {'Enabled' if streaming_enabled else 'Disabled'}")
    st.write(f"Streaming Bash: {'Enabled' if streaming_bash else 'Disabled'}")
    st.write(f"Streaming File: {'Enabled' if streaming_file else 'Disabled'}")
    st.write(f"Streaming Thinking: {'Enabled' if streaming_thinking else 'Disabled'}")'''
    
    if sidebar_pattern in modified_content:
        modified_content = modified_content.replace(sidebar_pattern, streaming_status)
    else:
        print("Warning: Could not find sidebar title. Manual verification needed.")
    
    # Enhance the output display to support token-by-token streaming
    # We'll look for the container that displays Claude's responses
    display_pattern = "with container.container():"
    streaming_display = '''with container.container():
        # Set up a placeholder for streaming output if streaming is enabled
        if is_feature_enabled("use_unified_streaming"):
            claude_output = st.empty()'''
    
    if display_pattern in modified_content:
        modified_content = modified_content.replace(display_pattern, streaming_display)
    else:
        print("Warning: Could not find container pattern. Manual verification needed.")
    
    # Write the modified content to streamlit.py
    with open(streamlit_path, "w") as f:
        f.write(modified_content)
    
    print(f"Successfully updated {streamlit_path} to integrate with streaming capabilities")
    print(f"Original file backed up at {backup_path}")
    return True

if __name__ == "__main__":
    if deploy_streaming_streamlit():
        print("Deployment successful!")
    else:
        print("Deployment failed.")