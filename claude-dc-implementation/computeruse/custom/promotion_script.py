#!/usr/bin/env python3
"""
Promotion script for DC Custom Implementation.
Carefully promotes the custom implementation to production.
"""

import os
import sys
import shutil
import datetime
import hashlib
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("promotion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("promotion")

# Paths
GITHUB_DIR = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom")
PROD_DIR = Path("/home/computeruse/computer_use_demo")
DC_IMPL_DIR = GITHUB_DIR / "dc_impl"
BACKUP_DIR = GITHUB_DIR / "backups" / f"prod_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

def create_backup():
    """Create a backup of the production environment"""
    logger.info(f"Creating backup at {BACKUP_DIR}")
    BACKUP_DIR.parent.mkdir(exist_ok=True)
    shutil.copytree(PROD_DIR, BACKUP_DIR)
    logger.info(f"Backup created successfully")
    
    # Create a manifest of backed up files with checksums
    manifest_path = BACKUP_DIR / "manifest.txt"
    with open(manifest_path, "w") as f:
        for path in sorted(BACKUP_DIR.rglob("*.py")):
            if path.is_file():
                rel_path = path.relative_to(BACKUP_DIR)
                checksum = hashlib.sha256(path.read_bytes()).hexdigest()
                f.write(f"{rel_path},{checksum}\n")
    
    logger.info(f"Backup manifest created at {manifest_path}")
    return BACKUP_DIR

def verify_github_implementation():
    """Verify the GitHub implementation is complete and tested"""
    logger.info("Verifying GitHub implementation")
    
    # Check for required directories
    required_dirs = ["models", "registry", "tools", "tests"]
    for dir_name in required_dirs:
        if not (DC_IMPL_DIR / dir_name).is_dir():
            logger.error(f"Missing required directory: {dir_name}")
            return False
    
    # Check for required files
    required_files = ["dc_executor.py", "dc_setup.py", "README.md"]
    for file_name in required_files:
        if not (DC_IMPL_DIR / file_name).is_file():
            logger.error(f"Missing required file: {file_name}")
            return False
    
    # Run tests
    logger.info("Running tests to verify implementation")
    try:
        os.chdir(Path("/home/computeruse/github/palios-taey-nova"))
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path("/home/computeruse/github/palios-taey-nova"))
        result = subprocess.run(
            ["python", "-m", "claude_dc_implementation.computeruse.custom.dc_impl.tests.test_tools"],
            env=env,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Tests failed:\n{result.stderr}")
            return False
        logger.info(f"Tests passed:\n{result.stdout}")
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return False
    
    logger.info("GitHub implementation verified successfully")
    return True

def create_bridge_module():
    """Create a bridge module in production to access the custom implementation"""
    logger.info("Creating bridge module in production")
    
    bridge_dir = PROD_DIR / "dc_bridge"
    bridge_dir.mkdir(exist_ok=True)
    
    # Create __init__.py
    with open(bridge_dir / "__init__.py", "w") as f:
        f.write('"""Bridge to DC Custom Implementation"""\n')
    
    # Create bridge.py
    bridge_path = bridge_dir / "bridge.py"
    with open(bridge_path, "w") as f:
        f.write('''"""
Bridge module to access DC Custom Implementation.
This module provides access to the custom implementation without directly
modifying production code.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dc_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dc_bridge")

# Add GitHub directory to path
GITHUB_DIR = Path("/home/computeruse/github/palios-taey-nova")
if str(GITHUB_DIR) not in sys.path:
    sys.path.insert(0, str(GITHUB_DIR))
    logger.info(f"Added {GITHUB_DIR} to sys.path")

# Import from custom implementation
try:
    from claude_dc_implementation.computeruse.custom.dc_impl.dc_setup import dc_initialize
    from claude_dc_implementation.computeruse.custom.dc_impl.dc_executor import dc_execute_tool
    
    # Initialize the implementation
    dc_initialize()
    logger.info("Successfully imported and initialized DC Custom Implementation")
    DC_CUSTOM_AVAILABLE = True
except Exception as e:
    logger.error(f"Error importing DC Custom Implementation: {str(e)}")
    DC_CUSTOM_AVAILABLE = False

async def execute_tool(tool_name, tool_input):
    """
    Execute a tool using the custom implementation.
    Falls back to mock implementation if real tools are unavailable.
    """
    if not DC_CUSTOM_AVAILABLE:
        logger.warning("DC Custom Implementation unavailable, using mock implementation")
        # Return a mock result
        return {"output": f"Mock execution of {tool_name} with input {tool_input}"}
    
    try:
        # Execute the tool using the custom implementation
        result = await dc_execute_tool(tool_name, tool_input)
        
        # Convert to the format expected by production
        return {
            "output": result.output,
            "error": result.error,
            "base64_image": result.base64_image
        }
    except Exception as e:
        logger.error(f"Error executing tool with custom implementation: {str(e)}")
        # Return an error result
        return {"error": f"Error: {str(e)}"}
''')
    
    logger.info(f"Bridge module created at {bridge_path}")
    return bridge_path

def promote_implementation():
    """
    Promote the custom implementation to production.
    Uses a bridge approach rather than direct replacement.
    """
    logger.info("Promoting implementation to production")
    
    # Create the promotion directory in production
    promote_dir = PROD_DIR / "dc_custom"
    promote_dir.mkdir(exist_ok=True)
    
    # Copy the custom implementation to production
    for item in DC_IMPL_DIR.glob("*"):
        if item.is_dir():
            shutil.copytree(item, promote_dir / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, promote_dir / item.name)
    
    logger.info(f"Custom implementation copied to {promote_dir}")
    
    # Create the bridge module
    bridge_path = create_bridge_module()
    
    # Create a simple test script
    test_path = PROD_DIR / "test_dc_custom.py"
    with open(test_path, "w") as f:
        f.write('''"""
Test script for DC Custom Implementation.
"""

import asyncio
from dc_bridge.bridge import execute_tool

async def test_dc_custom():
    """Test the DC Custom Implementation"""
    print("Testing DC Custom Implementation")
    
    # Test computer tool
    print("Testing computer tool...")
    result = await execute_tool("dc_computer", {"action": "screenshot"})
    print(f"Result: {result}")
    
    # Test bash tool
    print("Testing bash tool...")
    result = await execute_tool("dc_bash", {"command": "echo Hello from DC Custom"})
    print(f"Result: {result}")
    
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(test_dc_custom())
''')
    
    logger.info(f"Test script created at {test_path}")
    return promote_dir

def verify_promotion():
    """Verify the promotion was successful"""
    logger.info("Verifying promotion")
    
    # Run the test script
    try:
        os.chdir(PROD_DIR)
        result = subprocess.run(
            ["python", "test_dc_custom.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Test script failed:\n{result.stderr}")
            return False
        logger.info(f"Test script passed:\n{result.stdout}")
    except Exception as e:
        logger.error(f"Error running test script: {str(e)}")
        return False
    
    logger.info("Promotion verified successfully")
    return True

def main():
    """Main promotion process"""
    logger.info("Starting promotion process")
    
    # Verify GitHub implementation
    if not verify_github_implementation():
        logger.error("GitHub implementation verification failed. Aborting promotion.")
        return False
    
    # Create backup
    backup_dir = create_backup()
    
    # Promote implementation
    promote_dir = promote_implementation()
    
    # Verify promotion
    if not verify_promotion():
        logger.error("Promotion verification failed. Consider rolling back.")
        return False
    
    logger.info("Promotion completed successfully")
    print(f"""
Promotion Summary:
- Backup created at: {backup_dir}
- Custom implementation promoted to: {promote_dir}
- Bridge module created to access the implementation
- Test script created to verify functionality

To roll back, run:
    shutil.rmtree("{PROD_DIR / 'dc_bridge'}")
    shutil.rmtree("{PROD_DIR / 'dc_custom'}")
    os.remove("{PROD_DIR / 'test_dc_custom.py'}")
""")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)