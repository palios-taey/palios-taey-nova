"""
Test script to validate that APIProvider and sampling_loop can be properly imported.
"""
import sys
from pathlib import Path

# Add the current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

try:
    # Test importing APIProvider
    from loop import APIProvider
    print(f"Successfully imported APIProvider: {APIProvider}")
    print(f"Available providers: {[p.value for p in APIProvider]}")
    
    # Test importing sampling_loop
    from loop import sampling_loop
    print(f"Successfully imported sampling_loop")
    
    print("\nAPI import tests passed!")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)