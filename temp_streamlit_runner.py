
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('streamlit_runner')

# Add repository path to Python path to make all imports work
repo_root = Path("/home/jesse/projects/palios-taey-nova")
computer_use_demo = repo_root / "claude-dc-implementation/computeruse/computer_use_demo"

# Add all required paths to Python system path
for path in [repo_root, repo_root / "claude-dc-implementation", 
             repo_root / "claude-dc-implementation/computeruse"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Additionally set PYTHONPATH environment variable
current_pythonpath = os.environ.get("PYTHONPATH", "")
paths_to_add = [str(repo_root), 
                str(repo_root / "claude-dc-implementation"),
                str(repo_root / "claude-dc-implementation/computeruse")]
                
new_pythonpath = os.pathsep.join([current_pythonpath] + paths_to_add)
os.environ["PYTHONPATH"] = new_pythonpath

# Ensure ComputerTool environment variables are set
required_vars = {
    "WIDTH": os.environ.get("WIDTH", "1024"),
    "HEIGHT": os.environ.get("HEIGHT", "768"),
    "DISPLAY_NUM": os.environ.get("DISPLAY_NUM", "1")
}

# Set or update environment variables
for var, value in required_vars.items():
    os.environ[var] = value
    
# Log environment settings
logger.info(f"Screen dimensions: {os.environ['WIDTH']}x{os.environ['HEIGHT']} on display:{os.environ['DISPLAY_NUM']}")
logger.info(f"Python path includes: {sys.path[:5]}")

# Now import and run streamlit
import streamlit.web.cli as stcli
import streamlit as st

if __name__ == "__main__":
    streamlit_file = str(computer_use_demo / "streamlit.py")
    sys.argv = ["streamlit", "run", streamlit_file, 
                "--server.port=8501", "--server.headless=true"]
    sys.exit(stcli.main())
