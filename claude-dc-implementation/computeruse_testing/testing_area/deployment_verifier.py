#!/usr/bin/env python3
"""
Deployment Verification Utility for Claude DC Streaming Implementation

This script performs pre-deployment and post-deployment verification
to ensure the Claude DC streaming implementation is functioning correctly.
"""

import os
import sys
import asyncio
import logging
import shutil
import subprocess
import importlib.util
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"deployment_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger('claude_dc.deployment_verifier')

# Determine paths
REPO_ROOT = Path("/home/computeruse/github/palios-taey-nova")
CLAUDE_DC_ROOT = REPO_ROOT / "claude-dc-implementation"
COMPUTER_USE_DEMO_DIR = CLAUDE_DC_ROOT / "computeruse/computer_use_demo"
TESTING_AREA = CLAUDE_DC_ROOT / "computeruse/testing_area"
BACKUP_DIR = REPO_ROOT / "backups"

# Create backup directory if it doesn't exist
BACKUP_DIR.mkdir(exist_ok=True, parents=True)

async def create_backup():
    """Create a backup of the current production files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir(exist_ok=True, parents=True)
    
    # Files to backup
    files_to_backup = [
        COMPUTER_USE_DEMO_DIR / "loop.py",
        COMPUTER_USE_DEMO_DIR / "streamlit.py",
    ]
    
    # Create backups
    for file_path in files_to_backup:
        if file_path.exists():
            dest_path = backup_path / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.info(f"Backed up {file_path} to {dest_path}")
        else:
            logger.warning(f"File not found for backup: {file_path}")
    
    return backup_path

async def verify_syntax(file_path):
    """Verify Python syntax of a file."""
    try:
        # Check syntax using Python's compile function
        with open(file_path, 'r') as f:
            source = f.read()
        
        compile(source, file_path, 'exec')
        logger.info(f"Syntax check passed for {file_path}")
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False

async def verify_imports(file_path):
    """Verify imports in a Python file."""
    try:
        # Use importlib to check if module can be imported
        spec = importlib.util.spec_from_file_location("module.name", file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["module.name"] = module
        spec.loader.exec_module(module)
        logger.info(f"Import check passed for {file_path}")
        return True
    except ImportError as e:
        logger.error(f"Import error in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error importing {file_path}: {e}")
        return False

async def deploy_fixed_files():
    """Deploy the fixed files to production."""
    # Source files
    fixed_loop = TESTING_AREA / "fixed_loop.py"
    fixed_streamlit_api_callback = TESTING_AREA / "fixed_streamlit_api_callback.py"
    
    # Destination files
    dest_loop = COMPUTER_USE_DEMO_DIR / "loop.py"
    dest_streamlit = COMPUTER_USE_DEMO_DIR / "streamlit.py"
    
    # Verify source files exist
    if not fixed_loop.exists():
        logger.error(f"Fixed loop file not found: {fixed_loop}")
        return False
    
    if not fixed_streamlit_api_callback.exists():
        logger.error(f"Fixed streamlit callback file not found: {fixed_streamlit_api_callback}")
        return False
    
    # Verify syntax of source files
    if not await verify_syntax(fixed_loop):
        logger.error("Syntax verification failed for fixed_loop.py")
        return False
    
    if not await verify_syntax(fixed_streamlit_api_callback):
        logger.error("Syntax verification failed for fixed_streamlit_api_callback.py")
        return False
    
    # Create backup before deployment
    backup_path = await create_backup()
    logger.info(f"Created backup at {backup_path}")
    
    # Deploy fixed loop.py
    shutil.copy2(fixed_loop, dest_loop)
    logger.info(f"Deployed {fixed_loop} to {dest_loop}")
    
    # For streamlit.py, we need to patch only the affected functions
    try:
        # Read the fixed functions
        with open(fixed_streamlit_api_callback, 'r') as f:
            fixed_callbacks = f.read()
        
        # Read the current streamlit.py
        with open(dest_streamlit, 'r') as f:
            current_streamlit = f.read()
        
        # Extract the fixed functions
        import re
        api_callback_func = re.search(
            r'def _api_response_callback\([^)]*\):[^def]*',
            fixed_callbacks,
            re.DOTALL
        ).group(0)
        
        render_api_func = re.search(
            r'def _render_api_response\([^)]*\):[^def]*',
            fixed_callbacks,
            re.DOTALL
        ).group(0)
        
        # Replace the functions in the current streamlit.py
        updated_streamlit = re.sub(
            r'def _api_response_callback\([^)]*\):[^def]*',
            api_callback_func,
            current_streamlit,
            flags=re.DOTALL
        )
        
        updated_streamlit = re.sub(
            r'def _render_api_response\([^)]*\):[^def]*',
            render_api_func,
            updated_streamlit,
            flags=re.DOTALL
        )
        
        # Write the updated streamlit.py
        with open(dest_streamlit, 'w') as f:
            f.write(updated_streamlit)
        
        logger.info(f"Patched _api_response_callback and _render_api_response functions in {dest_streamlit}")
    except Exception as e:
        logger.error(f"Error patching streamlit.py: {e}")
        return False
    
    # Verify the deployed files
    if not await verify_syntax(dest_loop):
        logger.error("Syntax verification failed for deployed loop.py")
        # Rollback
        await rollback(backup_path)
        return False
    
    if not await verify_syntax(dest_streamlit):
        logger.error("Syntax verification failed for deployed streamlit.py")
        # Rollback
        await rollback(backup_path)
        return False
    
    # Verify imports
    if not await verify_imports(dest_loop):
        logger.error("Import verification failed for deployed loop.py")
        # Rollback
        await rollback(backup_path)
        return False
    
    if not await verify_imports(dest_streamlit):
        logger.error("Import verification failed for deployed streamlit.py")
        # Rollback
        await rollback(backup_path)
        return False
    
    logger.info("Deployment completed successfully")
    return True

async def rollback(backup_path):
    """Rollback to the backup files."""
    logger.warning(f"Rolling back to backup at {backup_path}")
    
    # Files to restore
    files_to_restore = [
        ("loop.py", COMPUTER_USE_DEMO_DIR / "loop.py"),
        ("streamlit.py", COMPUTER_USE_DEMO_DIR / "streamlit.py"),
    ]
    
    # Restore from backup
    for file_name, dest_path in files_to_restore:
        backup_file = backup_path / file_name
        if backup_file.exists():
            shutil.copy2(backup_file, dest_path)
            logger.info(f"Restored {backup_file} to {dest_path}")
        else:
            logger.warning(f"Backup file not found: {backup_file}")
    
    logger.info("Rollback completed")
    return True

async def verify_post_deployment():
    """Verify the system after deployment."""
    # Run minimal test script to check functionality
    minimal_test_path = CLAUDE_DC_ROOT / "computeruse/current_experiment/minimal_test.py"
    
    if not minimal_test_path.exists():
        logger.error(f"Minimal test script not found: {minimal_test_path}")
        return False
    
    try:
        # Set PYTHONPATH to include the required directories
        env = os.environ.copy()
        env["PYTHONPATH"] = ":".join(sys.path)
        
        # Run the minimal test
        logger.info(f"Running minimal test: {minimal_test_path}")
        process = subprocess.run(
            [sys.executable, str(minimal_test_path)],
            env=env,
            capture_output=True,
            text=True
        )
        
        # Check results
        if process.returncode == 0:
            logger.info("Minimal test completed successfully")
            logger.debug(f"Test output: {process.stdout}")
            return True
        else:
            logger.error(f"Minimal test failed with code {process.returncode}")
            logger.error(f"Error output: {process.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running minimal test: {e}")
        return False

async def main():
    """Main deployment verification process."""
    print("\n" + "=" * 80)
    print("CLAUDE DC STREAMING - DEPLOYMENT VERIFICATION")
    print("=" * 80)
    print(f"Verification started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Pre-deployment verification
    print("\nPre-deployment Verification:")
    print("--------------------------")
    
    # Check if source files exist
    fixed_loop = TESTING_AREA / "fixed_loop.py"
    fixed_streamlit_api_callback = TESTING_AREA / "fixed_streamlit_api_callback.py"
    
    if not fixed_loop.exists():
        print(f"❌ Fixed loop file not found: {fixed_loop}")
        return
    
    if not fixed_streamlit_api_callback.exists():
        print(f"❌ Fixed streamlit callback file not found: {fixed_streamlit_api_callback}")
        return
    
    # Check syntax of source files
    if await verify_syntax(fixed_loop):
        print(f"✅ Syntax verification passed for {fixed_loop}")
    else:
        print(f"❌ Syntax verification failed for {fixed_loop}")
        return
    
    if await verify_syntax(fixed_streamlit_api_callback):
        print(f"✅ Syntax verification passed for {fixed_streamlit_api_callback}")
    else:
        print(f"❌ Syntax verification failed for {fixed_streamlit_api_callback}")
        return
    
    # Deploy the fixed files
    print("\nDeploying Fixed Files:")
    print("-------------------")
    
    deployment_success = await deploy_fixed_files()
    if deployment_success:
        print("✅ Deployment completed successfully")
    else:
        print("❌ Deployment failed")
        return
    
    # Post-deployment verification
    print("\nPost-deployment Verification:")
    print("---------------------------")
    
    if await verify_post_deployment():
        print("✅ Post-deployment verification passed")
    else:
        print("❌ Post-deployment verification failed")
        print("⚠️ Consider rolling back to the latest backup")
        return
    
    # Final status
    print("\n" + "=" * 80)
    print("DEPLOYMENT STATUS: SUCCESS")
    print("=" * 80)
    print("The fixed implementation has been deployed and verified successfully.")
    print(f"Backup created at: {BACKUP_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())