import sys
print("Python path:", sys.path)
print("Modules loaded:", list(sys.modules.keys()))

# __init__.py
from .token_manager import token_manager
from computer_use_demo.adaptive_client import create_adaptive_client
from .safe_file_operations import safe_cat, safe_read_file, interceptor, patch_streamlit

# Apply patches immediately when the module is imported
patch_streamlit()
