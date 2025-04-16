"""
Extract current loop.py and streamlit.py content for analysis
"""
import os

def extract_file(file_path, output_path):
    """Extract file content to a .txt file for analysis"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Extracted {file_path} to {output_path}")
    return len(content)

# Extract loop.py
loop_size = extract_file(
    '/home/computeruse/computer_use_demo/loop.py',
    '/home/computeruse/computer_use_demo/loop_current.txt'
)

# Extract streamlit.py
streamlit_size = extract_file(
    '/home/computeruse/computer_use_demo/streamlit.py',
    '/home/computeruse/computer_use_demo/streamlit_current.txt'
)

print(f"Extracted loop.py ({loop_size} bytes) and streamlit.py ({streamlit_size} bytes)")
print("You can now safely analyze these files without risking production environment")