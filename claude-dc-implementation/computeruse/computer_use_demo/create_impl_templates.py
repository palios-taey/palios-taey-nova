"""
Create implementation templates for loop.py and streamlit.py changes
"""
import os
import re

def create_template(source_path, template_path, tag):
    """Create a modified template from source"""
    with open(source_path, 'r') as f:
        content = f.read()
    
    # Add template markers for easy identification of required changes
    content = f"""# STREAMING IMPLEMENTATION TEMPLATE - {tag}
# Generated from current production file
# Look for STREAMING-CHANGE comments to see where changes are needed

{content}

# STREAMING-CHANGE: Add streaming client integration here if not present above
# STREAMING-CHANGE: Ensure proper token management integration
"""
    
    with open(template_path, 'w') as f:
        f.write(content)
    
    print(f"Created template at {template_path}")

# Create loop.py template
create_template(
    '/home/computeruse/computer_use_demo/loop_current.txt',
    '/home/computeruse/computer_use_demo/loop_streaming_template.py',
    'LOOP'
)

# Create streamlit.py template
create_template(
    '/home/computeruse/computer_use_demo/streamlit_current.txt',
    '/home/computeruse/computer_use_demo/streamlit_streaming_template.py',
    'STREAMLIT'
)

print("Created implementation templates")
print("Edit these files to add streaming support, following the STREAMING-CHANGE markers")