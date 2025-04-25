
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import loop
    print("Loop module imported successfully")
    from tools import registry, bash, computer, edit
    print("Tool modules imported successfully")
    from utils import streaming, error_handling
    print("Utils modules imported successfully")
    from models import tool_models
    print("Model modules imported successfully")
    print("All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

sys.exit(0)
