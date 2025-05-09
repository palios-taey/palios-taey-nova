#!/usr/bin/env python3
"""
Backup script for production files.

This script creates timestamped backups of important production files
before modifying them for streaming implementation.
"""

import os
import sys
import shutil
import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.dirname(__file__), "logs", "backup.log"),
    filemode="a"
)
logger = logging.getLogger("backup_production")

def create_backup_directory():
    """Create a backup directory with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("/home/computeruse/computer_use_demo_backups") / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def backup_file(file_path, backup_dir):
    """Create a backup of a single file."""
    source_path = Path(file_path)
    if not source_path.exists():
        logger.warning(f"File {source_path} does not exist. Skipping backup.")
        return False
    
    try:
        # Preserve the relative path structure
        relative_path = source_path.relative_to("/home/computeruse/computer_use_demo")
        target_path = backup_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        logger.info(f"Backed up {source_path} to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Error backing up {source_path}: {str(e)}")
        return False

def backup_production_files():
    """Back up all important production files."""
    # Critical files to back up
    critical_files = [
        "/home/computeruse/computer_use_demo/loop.py",
        "/home/computeruse/computer_use_demo/streamlit.py",
        "/home/computeruse/computer_use_demo/tools/bash.py",
        "/home/computeruse/computer_use_demo/tools/edit.py",
        "/home/computeruse/computer_use_demo/tools/computer.py",
        "/home/computeruse/computer_use_demo/tools/base.py",
        "/home/computeruse/computer_use_demo/tools/collection.py",
        "/home/computeruse/computer_use_demo/tools/groups.py",
        "/home/computeruse/computer_use_demo/tools/__init__.py",
    ]
    
    # Create backup directory
    backup_dir = create_backup_directory()
    logger.info(f"Created backup directory: {backup_dir}")
    
    # Back up each file
    backup_results = []
    for file_path in critical_files:
        success = backup_file(file_path, backup_dir)
        backup_results.append((file_path, success))
    
    # Also back up the entire tools directory for completeness
    try:
        shutil.copytree(
            "/home/computeruse/computer_use_demo/tools",
            backup_dir / "tools",
            dirs_exist_ok=True
        )
        logger.info(f"Backed up entire tools directory to {backup_dir / 'tools'}")
    except Exception as e:
        logger.error(f"Error backing up tools directory: {str(e)}")
    
    # Print summary
    print(f"Backup Summary (logged to {os.path.join(os.path.dirname(__file__), 'logs', 'backup.log')}):")
    print(f"Backup directory: {backup_dir}")
    for file_path, success in backup_results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{status}: {file_path}")
    
    return backup_dir

if __name__ == "__main__":
    print("Creating backups of production files before streaming implementation...")
    backup_dir = backup_production_files()
    print(f"\nBackup completed. Files stored in: {backup_dir}")