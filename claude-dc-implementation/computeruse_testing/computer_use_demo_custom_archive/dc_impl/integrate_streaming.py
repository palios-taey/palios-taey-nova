#!/usr/bin/env python3
"""
Integration script for deploying streaming functionality to production.

This script provides a safe way to integrate the custom streaming implementation
into the production environment (/home/computeruse/computer_use_demo/) while
maintaining system stability through backups and feature toggles.
"""

import os
import sys
import shutil
import argparse
import datetime
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integrate_streaming")

# Define paths
CUSTOM_DIR = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/computer_use_demo_custom")
PRODUCTION_DIR = Path("/home/computeruse/computer_use_demo")
BACKUP_DIR = Path("/home/computeruse/computer_use_demo_backups")

# Feature toggle configuration
TOGGLE_CONFIG_PATH = CUSTOM_DIR / "dc_impl" / "feature_toggles.json"

class StreamingIntegrator:
    """Handles integration of streaming functionality into production."""
    
    def __init__(self, args):
        """Initialize with command line arguments."""
        self.args = args
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = BACKUP_DIR / f"backup_{self.timestamp}"
        self.feature_toggles = self._load_feature_toggles()
    
    def _load_feature_toggles(self):
        """Load feature toggle configuration or create default."""
        if TOGGLE_CONFIG_PATH.exists():
            try:
                with open(TOGGLE_CONFIG_PATH, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Invalid toggle configuration in {TOGGLE_CONFIG_PATH}")
        
        # Default configuration
        return {
            "use_streaming_bash": True,
            "use_streaming_file": True,
            "use_streaming_screenshot": False,
            "use_unified_streaming": False,
            "use_streaming_thinking": True,
            "feature_version": "0.1"
        }
    
    def _save_feature_toggles(self):
        """Save current feature toggle configuration."""
        os.makedirs(TOGGLE_CONFIG_PATH.parent, exist_ok=True)
        with open(TOGGLE_CONFIG_PATH, "w") as f:
            json.dump(self.feature_toggles, f, indent=2)
        logger.info(f"Feature toggles saved to {TOGGLE_CONFIG_PATH}")
    
    def create_backup(self):
        """Create a backup of the production environment."""
        if not PRODUCTION_DIR.exists():
            logger.error(f"Production directory {PRODUCTION_DIR} does not exist!")
            return False
        
        try:
            # Create backup directory
            os.makedirs(self.backup_path, exist_ok=True)
            logger.info(f"Creating backup at {self.backup_path}")
            
            # Copy production to backup
            for item in PRODUCTION_DIR.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.backup_path)
                elif item.is_dir():
                    shutil.copytree(item, self.backup_path / item.name)
            
            logger.info(f"Backup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_path=None):
        """Restore production from a backup."""
        restore_path = Path(backup_path) if backup_path else self.backup_path
        
        if not restore_path.exists():
            logger.error(f"Backup directory {restore_path} does not exist!")
            return False
        
        try:
            logger.info(f"Restoring from backup {restore_path}")
            
            # Clear production directory (except for irreplaceable files)
            for item in PRODUCTION_DIR.iterdir():
                if item.is_file() and item.name not in [".gitignore", "README.md"]:
                    os.remove(item)
                elif item.is_dir() and item.name not in [".git"]:
                    shutil.rmtree(item)
            
            # Copy from backup to production
            for item in restore_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, PRODUCTION_DIR)
                elif item.is_dir() and item.name not in [".git"]:
                    dest_path = PRODUCTION_DIR / item.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
            
            logger.info(f"Restore completed successfully")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False
    
    def _update_feature_toggles(self):
        """Update feature toggles based on command line args."""
        if self.args.enable_streaming_bash is not None:
            self.feature_toggles["use_streaming_bash"] = self.args.enable_streaming_bash
        
        if self.args.enable_streaming_file is not None:
            self.feature_toggles["use_streaming_file"] = self.args.enable_streaming_file
        
        if self.args.enable_streaming_screenshot is not None:
            self.feature_toggles["use_streaming_screenshot"] = self.args.enable_streaming_screenshot
        
        if self.args.enable_unified_streaming is not None:
            self.feature_toggles["use_unified_streaming"] = self.args.enable_unified_streaming
        
        if self.args.enable_streaming_thinking is not None:
            self.feature_toggles["use_streaming_thinking"] = self.args.enable_streaming_thinking
        
        # Update version
        self.feature_toggles["feature_version"] = "0.2"
        
        # Save updated configuration
        self._save_feature_toggles()
    
    def integrate_streaming_bash(self):
        """Integrate streaming bash tool into production."""
        source_file = CUSTOM_DIR / "dc_impl" / "tools" / "dc_bash.py"
        target_file = PRODUCTION_DIR / "tools" / "dc_bash.py"
        
        if not source_file.exists():
            logger.error(f"Source file {source_file} does not exist!")
            return False
        
        try:
            # Create target directory if needed
            os.makedirs(target_file.parent, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_file, target_file)
            logger.info(f"Integrated streaming bash tool: {source_file} -> {target_file}")
            
            # Update feature toggles
            self.feature_toggles["use_streaming_bash"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to integrate streaming bash: {str(e)}")
            return False
    
    def integrate_streaming_file(self):
        """Integrate streaming file operations tool into production."""
        source_file = CUSTOM_DIR / "dc_impl" / "tools" / "dc_file.py"
        target_file = PRODUCTION_DIR / "tools" / "dc_file.py"
        
        if not source_file.exists():
            logger.error(f"Source file {source_file} does not exist!")
            return False
        
        try:
            # Create target directory if needed
            os.makedirs(target_file.parent, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_file, target_file)
            logger.info(f"Integrated streaming file operations: {source_file} -> {target_file}")
            
            # Update feature toggles
            self.feature_toggles["use_streaming_file"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to integrate streaming file operations: {str(e)}")
            return False
    
    def integrate_unified_streaming(self):
        """Integrate unified streaming agent loop into production."""
        source_files = [
            (CUSTOM_DIR / "dc_impl" / "unified_streaming_loop.py", PRODUCTION_DIR / "unified_streaming_loop.py"),
            (CUSTOM_DIR / "dc_impl" / "streaming_enhancements.py", PRODUCTION_DIR / "streaming_enhancements.py"),
        ]
        
        success = True
        for source_file, target_file in source_files:
            if not source_file.exists():
                logger.error(f"Source file {source_file} does not exist!")
                success = False
                continue
            
            try:
                # Create target directory if needed
                os.makedirs(target_file.parent, exist_ok=True)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                logger.info(f"Integrated streaming file: {source_file} -> {target_file}")
            except Exception as e:
                logger.error(f"Failed to integrate {source_file}: {str(e)}")
                success = False
        
        if success:
            # Update feature toggles
            self.feature_toggles["use_unified_streaming"] = True
        
        return success
    
    def update_main_loop(self):
        """Update the main loop file to reference the new streaming functionality."""
        main_loop_file = PRODUCTION_DIR / "loop.py"
        
        if not main_loop_file.exists():
            logger.error(f"Main loop file {main_loop_file} does not exist!")
            return False
        
        try:
            # Read the original file
            with open(main_loop_file, "r") as f:
                content = f.read()
            
            # Check if streaming import already exists
            if "from unified_streaming_loop import" in content:
                logger.info("Main loop already updated for streaming")
                return True
            
            # Add streaming imports
            import_lines = """
# Streaming functionality
try:
    from unified_streaming_loop import unified_streaming_agent_loop
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

# Feature toggles
STREAMING_ENABLED = STREAMING_AVAILABLE and {
    "use_streaming_bash": True,
    "use_streaming_file": True,
    "use_unified_streaming": True,
    "use_streaming_thinking": True
}
"""
            # Find the right position to insert (after imports)
            import_end = content.rfind("import") 
            import_end = content.find("\n", import_end) + 1
            
            # Insert at the right position
            new_content = content[:import_end] + import_lines + content[import_end:]
            
            # Inject a check to use streaming if available
            inject_point = "async def sampling_loop("
            streaming_check = """
    # Use streaming implementation if available and enabled
    if STREAMING_AVAILABLE and STREAMING_ENABLED:
        logger.info("Using unified streaming implementation")
        # Convert sampling_loop arguments to unified_streaming_agent_loop arguments
        return await unified_streaming_agent_loop(
            user_input=messages[-1].get("content", ""),
            conversation_history=messages[:-1],
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            # Pass through any other relevant parameters
        )
"""
            inject_pos = new_content.find(inject_point)
            if inject_pos > 0:
                # Find the first line after the function definition
                function_start = new_content.find("{", inject_pos)
                if function_start > 0:
                    new_content = new_content[:function_start+1] + streaming_check + new_content[function_start+1:]
            
            # Write the modified file
            with open(main_loop_file, "w") as f:
                f.write(new_content)
            
            logger.info("Updated main loop with streaming functionality")
            return True
        except Exception as e:
            logger.error(f"Failed to update main loop: {str(e)}")
            return False
    
    def run_integration(self):
        """Run the integration process."""
        
        # First update feature toggles based on command line args
        self._update_feature_toggles()
        
        # Create backup unless explicitly skipped
        if not self.args.skip_backup:
            if not self.create_backup():
                logger.error("Backup failed, aborting integration")
                return False
        
        # Track if we need to update the main loop
        need_loop_update = False
        
        # Integrate the requested components
        if self.args.bash_tool:
            if self.integrate_streaming_bash():
                need_loop_update = True
        
        if self.args.file_tool:
            if self.integrate_streaming_file():
                need_loop_update = True
        
        if self.args.unified_streaming:
            if self.integrate_unified_streaming():
                need_loop_update = True
        
        # Update the main loop if needed
        if need_loop_update and self.args.update_loop:
            self.update_main_loop()
        
        # Save the updated feature toggles
        self._save_feature_toggles()
        
        logger.info("Integration completed successfully")
        return True
    
    def list_backups(self):
        """List all available backups."""
        if not BACKUP_DIR.exists():
            logger.error(f"Backup directory {BACKUP_DIR} does not exist!")
            return False
        
        backups = [d for d in BACKUP_DIR.iterdir() if d.is_dir() and d.name.startswith("backup_")]
        
        if not backups:
            logger.info("No backups found")
            return True
        
        logger.info("Available backups:")
        for backup in sorted(backups):
            backup_time = backup.name.replace("backup_", "")
            logger.info(f"- {backup} (created: {backup_time})")
        
        return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Integrate streaming functionality into production")
    
    # Main operations
    parser.add_argument("--integrate", action="store_true", help="Run the integration process")
    parser.add_argument("--restore", help="Restore from specified backup")
    parser.add_argument("--list-backups", action="store_true", help="List all available backups")
    
    # Components to integrate
    parser.add_argument("--bash-tool", action="store_true", help="Integrate streaming bash tool")
    parser.add_argument("--file-tool", action="store_true", help="Integrate streaming file operations")
    parser.add_argument("--unified-streaming", action="store_true", help="Integrate unified streaming implementation")
    
    # Feature toggles
    parser.add_argument("--enable-streaming-bash", type=bool, help="Enable streaming bash tool")
    parser.add_argument("--enable-streaming-file", type=bool, help="Enable streaming file operations")
    parser.add_argument("--enable-streaming-screenshot", type=bool, help="Enable streaming screenshot tool")
    parser.add_argument("--enable-unified-streaming", type=bool, help="Enable unified streaming implementation")
    parser.add_argument("--enable-streaming-thinking", type=bool, help="Enable streaming thinking capability")
    
    # Additional options
    parser.add_argument("--skip-backup", action="store_true", help="Skip creating a backup")
    parser.add_argument("--update-loop", action="store_true", help="Update main loop with streaming support")
    
    args = parser.parse_args()
    
    integrator = StreamingIntegrator(args)
    
    if args.list_backups:
        integrator.list_backups()
    elif args.restore:
        integrator.restore_from_backup(args.restore)
    elif args.integrate:
        integrator.run_integration()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")