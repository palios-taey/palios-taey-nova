# Create a new file called run_streamlit.py at the root level

"""
Entry point that sets up the environment before running streamlit
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

# Import our safe operations FIRST, before anything else
from computer_use_demo.safe_file_operations import patch_streamlit

# Apply the patch to streamlit
patch_streamlit()

# Now it's safe to import and run streamlit
from computer_use_demo.streamlit import main
import asyncio

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
