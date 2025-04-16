# /home/computeruse/computer_use_demo/patch_streamlit.py

"""
Minimal patch for streamlit.py to avoid subprocess patching issues
"""

import logging
import asyncio
from datetime import datetime

logger = logging.getLogger('patch_streamlit')

async def run_streamlit():
    """
    Run streamlit with minimal modifications to avoid recursion errors
    """
    try:
        # Import streamlit's main function
        from computer_use_demo.streamlit import main
        
        # Run the main function
        await main()
    except Exception as e:
        logger.error(f"Error running streamlit: {e}")
        raise

# Function to be called from command line
def main():
    """Main entry point for patched streamlit"""
    asyncio.run(run_streamlit())
