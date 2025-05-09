#!/usr/bin/env python3
"""
Deployment script for updating loop.py to support streaming.

This script safely modifies loop.py to integrate with the streaming implementation
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

def deploy_streaming_loop():
    """Deploy streaming integration to loop.py."""
    
    # Define paths
    loop_path = Path("/home/computeruse/computer_use_demo/loop.py")
    streaming_integration_path = Path("/home/computeruse/computer_use_demo/streaming_integration.py")
    
    # Verify files exist
    if not loop_path.exists():
        print(f"Error: {loop_path} not found")
        return False
    
    if not streaming_integration_path.exists():
        print(f"Error: {streaming_integration_path} not found")
        return False
    
    # Create backup
    backup_path = backup_file(loop_path)
    
    # Read the original loop.py
    with open(loop_path, "r") as f:
        loop_content = f.read()
    
    # Read the streaming integration module
    with open(streaming_integration_path, "r") as f:
        integration_content = f.read()
    
    # Prepare the modified content
    # We'll add the streaming imports and wrap the sampling_loop function
    modified_content = loop_content
    
    # Add import for streaming integration
    import_line = "from .streaming_integration import is_feature_enabled, async_sampling_loop\n"
    # Find the right place to add imports - after the last import statement
    import_end_index = max(
        modified_content.rfind("import "),
        modified_content.rfind("from ")
    )
    
    # Find the end of the import block
    import_block_end = modified_content.find("\n\n", import_end_index)
    if import_block_end == -1:
        # If we can't find a double newline, use a single one
        import_block_end = modified_content.find("\n", import_end_index)
    
    # Insert our import after the last import
    modified_content = (
        modified_content[:import_block_end + 1] +
        import_line +
        modified_content[import_block_end + 1:]
    )
    
    # Replace the original sampling_loop function with one that delegates to the streaming implementation
    original_function_start = modified_content.find("async def sampling_loop(")
    if original_function_start == -1:
        print("Error: Could not find sampling_loop function in loop.py")
        return False
    
    function_body_start = modified_content.find(":", original_function_start) + 1
    # Find the indentation of the function body
    next_line_start = modified_content.find("\n", function_body_start) + 1
    indent = ""
    for char in modified_content[next_line_start:]:
        if char.isspace():
            indent += char
        else:
            break
    
    # Find the end of the docstring
    docstring_start = modified_content.find('"""', function_body_start)
    docstring_end = modified_content.find('"""', docstring_start + 3) + 3
    
    # Construct the new function implementation that delegates to the streaming implementation
    streaming_delegation = f'''
{indent}"""
{indent}Agentic sampling loop for the assistant/tool interaction of computer use.
{indent}
{indent}This implementation can delegate to the streaming implementation based on feature toggles.
{indent}"""
{indent}# Check if streaming is enabled
{indent}if is_feature_enabled("use_unified_streaming"):
{indent}    try:
{indent}        # Use the streaming implementation
{indent}        return await async_sampling_loop(
{indent}            model=model,
{indent}            provider=provider,
{indent}            system_prompt_suffix=system_prompt_suffix,
{indent}            messages=messages,
{indent}            output_callback=output_callback,
{indent}            tool_output_callback=tool_output_callback,
{indent}            api_response_callback=api_response_callback,
{indent}            api_key=api_key,
{indent}            only_n_most_recent_images=only_n_most_recent_images,
{indent}            max_tokens=max_tokens,
{indent}            tool_version=tool_version,
{indent}            thinking_budget=thinking_budget,
{indent}            token_efficient_tools_beta=token_efficient_tools_beta,
{indent}        )
{indent}    except Exception as e:
{indent}        print(f"Error in streaming implementation: {{str(e)}}")
{indent}        print("Falling back to original implementation")
{indent}        # Continue with original implementation on error
'''
    
    # Replace the original function body with our streaming delegation code + original code
    original_function_body_start = docstring_end
    modified_content = (
        modified_content[:original_function_body_start] +
        streaming_delegation +
        modified_content[original_function_body_start:]
    )
    
    # Write the modified content to loop.py
    with open(loop_path, "w") as f:
        f.write(modified_content)
    
    print(f"Successfully updated {loop_path} to integrate with streaming capabilities")
    print(f"Original file backed up at {backup_path}")
    return True

if __name__ == "__main__":
    if deploy_streaming_loop():
        print("Deployment successful!")
    else:
        print("Deployment failed.")