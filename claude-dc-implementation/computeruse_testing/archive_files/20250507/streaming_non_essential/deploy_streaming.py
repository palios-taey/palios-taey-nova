#!/usr/bin/env python3
"""
Deployment script for streaming implementation.

This script should be executed by DCCC to deploy the streaming implementation
to production, including handling the critical loop.py and streamlit.py files.
"""

import os
import sys
import shutil
import logging
import json
import importlib.util
from pathlib import Path
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.dirname(__file__), "logs", "deployment.log"),
    filemode="a"
)
logger = logging.getLogger("deploy_streaming")

# Constants
STREAMING_DIR = Path(__file__).parent
PRODUCTION_DIR = Path("/home/computeruse/computer_use_demo")

def verify_backup_exists():
    """Verify that a backup exists before proceeding with deployment."""
    backup_dir = Path("/home/computeruse/computer_use_demo_backups")
    if not backup_dir.exists() or not any(backup_dir.iterdir()):
        logger.error("No backup directory found. Please run backup_production.py first.")
        print("❌ ERROR: No backup found! Run backup_production.py before deployment.")
        return False
    
    logger.info(f"Found backup directory: {backup_dir}")
    print(f"✅ Found backup directory: {backup_dir}")
    return True

def deploy_non_critical_files():
    """Deploy all non-critical files first."""
    files_to_deploy = [
        (STREAMING_DIR / "unified_streaming_loop.py", PRODUCTION_DIR / "streaming" / "unified_streaming_loop.py"),
        (STREAMING_DIR / "streaming_enhancements.py", PRODUCTION_DIR / "streaming" / "streaming_enhancements.py"),
        (STREAMING_DIR / "tool_adapter.py", PRODUCTION_DIR / "streaming" / "tool_adapter.py"),
        (STREAMING_DIR / "feature_toggles.json", PRODUCTION_DIR / "streaming" / "feature_toggles.json"),
        (STREAMING_DIR / "models" / "dc_models.py", PRODUCTION_DIR / "streaming" / "models" / "dc_models.py"),
        (STREAMING_DIR / "tools" / "dc_bash.py", PRODUCTION_DIR / "streaming" / "tools" / "dc_bash.py"),
        (STREAMING_DIR / "tools" / "dc_file.py", PRODUCTION_DIR / "streaming" / "tools" / "dc_file.py"),
    ]
    
    # Create necessary directories
    (PRODUCTION_DIR / "streaming").mkdir(exist_ok=True)
    (PRODUCTION_DIR / "streaming" / "models").mkdir(exist_ok=True)
    (PRODUCTION_DIR / "streaming" / "tools").mkdir(exist_ok=True)
    
    # Create __init__.py files
    for dir_path in [
        PRODUCTION_DIR / "streaming",
        PRODUCTION_DIR / "streaming" / "models",
        PRODUCTION_DIR / "streaming" / "tools",
    ]:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created {init_file}")
    
    # Deploy each file
    deployment_results = []
    for source, target in files_to_deploy:
        try:
            if source.exists():
                shutil.copy2(source, target)
                logger.info(f"Deployed {source} to {target}")
                deployment_results.append((str(source), True))
            else:
                logger.error(f"Source file {source} does not exist")
                deployment_results.append((str(source), False))
        except Exception as e:
            logger.error(f"Error deploying {source}: {str(e)}")
            deployment_results.append((str(source), False))
    
    # Print summary
    print("\nNon-critical file deployment summary:")
    for file_path, success in deployment_results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{status}: {file_path}")
    
    return all(success for _, success in deployment_results)

def deploy_critical_files():
    """Deploy the critical loop.py and streamlit.py files."""
    critical_files = [
        (STREAMING_DIR / "integration_loop.py", PRODUCTION_DIR / "loop.py"),
        (STREAMING_DIR / "integration_streamlit.py", PRODUCTION_DIR / "streamlit.py"),
    ]
    
    # Check if the critical files exist in the streaming directory
    missing_files = [source for source, _ in critical_files if not source.exists()]
    if missing_files:
        logger.error(f"Missing critical files for deployment: {missing_files}")
        print(f"❌ ERROR: Missing critical files: {[str(f) for f in missing_files]}")
        return False
    
    # Deploy each critical file
    deployment_results = []
    for source, target in critical_files:
        try:
            # Create a temporary backup of the target file
            temp_backup = target.with_suffix(target.suffix + ".bak")
            if target.exists():
                shutil.copy2(target, temp_backup)
                logger.info(f"Created temporary backup: {temp_backup}")
            
            # Deploy the new file
            shutil.copy2(source, target)
            logger.info(f"Deployed critical file {source} to {target}")
            deployment_results.append((str(source), True))
            
            # Only remove the backup if deployment was successful
            if temp_backup.exists():
                temp_backup.unlink()
                logger.info(f"Removed temporary backup: {temp_backup}")
                
        except Exception as e:
            logger.error(f"Error deploying critical file {source}: {str(e)}")
            
            # Try to restore from temporary backup if deployment failed
            if "temp_backup" in locals() and temp_backup.exists():
                try:
                    shutil.copy2(temp_backup, target)
                    logger.info(f"Restored {target} from temporary backup")
                    print(f"⚠️ Deployment failed, restored {target} from backup")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
                    print(f"❌ CRITICAL: Failed to restore {target} from backup!")
            
            deployment_results.append((str(source), False))
    
    # Print summary
    print("\nCritical file deployment summary:")
    for file_path, success in deployment_results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{status}: {file_path}")
    
    return all(success for _, success in deployment_results)

def verify_deployment():
    """Verify the deployment was successful."""
    # Check if all required files exist
    required_files = [
        PRODUCTION_DIR / "streaming" / "unified_streaming_loop.py",
        PRODUCTION_DIR / "streaming" / "streaming_enhancements.py",
        PRODUCTION_DIR / "streaming" / "tool_adapter.py",
        PRODUCTION_DIR / "streaming" / "feature_toggles.json",
        PRODUCTION_DIR / "streaming" / "models" / "dc_models.py",
        PRODUCTION_DIR / "streaming" / "tools" / "dc_bash.py",
        PRODUCTION_DIR / "streaming" / "tools" / "dc_file.py",
        PRODUCTION_DIR / "loop.py",
        PRODUCTION_DIR / "streamlit.py",
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        logger.error(f"Deployment verification failed. Missing files: {missing_files}")
        print(f"❌ Deployment verification failed. Missing files:")
        for f in missing_files:
            print(f"  - {f}")
        return False
    
    # Try importing the critical modules to ensure they're valid Python
    try:
        spec = importlib.util.spec_from_file_location("loop", PRODUCTION_DIR / "loop.py")
        loop_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loop_module)
        logger.info("Successfully imported loop.py")
        
        spec = importlib.util.spec_from_file_location("streamlit", PRODUCTION_DIR / "streamlit.py")
        streamlit_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(streamlit_module)
        logger.info("Successfully imported streamlit.py")
        
        print("✅ Module import verification successful.")
    except Exception as e:
        logger.error(f"Module import verification failed: {str(e)}")
        print(f"❌ Module import verification failed: {str(e)}")
        return False
    
    return True

def main():
    """Main deployment function."""
    print("=== Streaming Implementation Deployment ===\n")
    
    # Step 1: Verify backup exists
    if not verify_backup_exists():
        return 1
    
    # Step 2: Deploy non-critical files
    print("\nDeploying non-critical files...")
    if not deploy_non_critical_files():
        logger.error("Non-critical file deployment failed")
        print("❌ Non-critical file deployment failed. See logs for details.")
        return 1
    
    # Step 3: Deploy critical files
    print("\nDeploying critical files...")
    if not deploy_critical_files():
        logger.error("Critical file deployment failed")
        print("❌ Critical file deployment failed. See logs for details.")
        return 1
    
    # Step 4: Verify deployment
    print("\nVerifying deployment...")
    if not verify_deployment():
        logger.error("Deployment verification failed")
        print("❌ Deployment verification failed. See logs for details.")
        return 1
    
    print("\n✅ Streaming implementation deployed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())