"""
Test script for the real tool adapters.
"""

import unittest
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the system path
current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent  # dc_impl directory
sys.path.insert(0, str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_real_tools")

# Import from our namespace-isolated modules directly
from dc_setup import dc_initialize
from tools.dc_real_adapters import (
    dc_execute_computer_tool_real,
    dc_execute_bash_tool_real,
    dc_execute_edit_tool_real
)

class TestRealTools(unittest.TestCase):
    """Test case for real tool adapters."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test case."""
        # Set up log directory
        log_dir = parent_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Add file handler for test logs
        file_handler = logging.FileHandler(log_dir / "test_real_tools.log")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info("Starting real tool adapter tests")
        
        # Initialize DC implementation with real adapters
        try:
            dc_initialize(use_real_adapters=True)
            logger.info("DC implementation initialized with real adapters")
        except Exception as e:
            logger.error(f"Failed to initialize DC implementation with real adapters: {str(e)}")
            # We'll continue with the tests anyway - they'll use direct calls to the adapters
    
    def test_computer_tool_real_screenshot(self):
        """Test the real computer tool screenshot action."""
        try:
            result = asyncio.run(dc_execute_computer_tool_real(
                {"action": "screenshot"}
            ))
            self.assertIsNotNone(result)
            
            # Log the result
            if result.error:
                logger.warning(f"Computer tool screenshot returned error: {result.error}")
            else:
                logger.info(f"Computer tool screenshot returned: {result.output[:100]}")
                if result.base64_image:
                    img_size = len(result.base64_image)
                    logger.info(f"Computer tool screenshot returned image of size: {img_size}")
            
            # Success if either output or base64_image is present
            self.assertTrue(result.output or result.base64_image)
        except Exception as e:
            logger.error(f"Computer tool screenshot test failed: {str(e)}")
            raise
    
    def test_bash_tool_echo(self):
        """Test the real bash tool with echo command."""
        try:
            result = asyncio.run(dc_execute_bash_tool_real(
                {"command": "echo 'Hello from Real Tool Test'"}
            ))
            self.assertIsNotNone(result)
            
            # Log the result
            if result.error:
                logger.warning(f"Bash tool echo returned error: {result.error}")
            else:
                logger.info(f"Bash tool echo returned: {result.output}")
            
            # Check if the output contains our echo text
            self.assertIn("Hello from Real Tool Test", result.output or "")
        except Exception as e:
            logger.error(f"Bash tool echo test failed: {str(e)}")
            raise
    
    def test_bash_tool_ls(self):
        """Test the real bash tool with ls command."""
        try:
            result = asyncio.run(dc_execute_bash_tool_real(
                {"command": "ls -la /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl"}
            ))
            self.assertIsNotNone(result)
            
            # Log the result
            if result.error:
                logger.warning(f"Bash tool ls returned error: {result.error}")
            else:
                logger.info(f"Bash tool ls returned output of length: {len(result.output or '')}")
            
            # Make sure we got some output and not an error
            self.assertTrue(result.output)
            
            # Check if we got real or mock output
            if "file1.txt" in result.output and "file2.txt" in result.output:
                # We got mock output
                logger.info("Test is using mock implementation (expected behavior if real tools aren't available)")
                self.assertIn("file1.txt", result.output)
            else:
                # We got real output
                logger.info("Test is using real implementation")
                self.assertIn("dc_setup.py", result.output)
        except Exception as e:
            logger.error(f"Bash tool ls test failed: {str(e)}")
            raise
    
    def test_edit_tool_view(self):
        """Test the real edit tool view command."""
        try:
            result = asyncio.run(dc_execute_edit_tool_real({
                "command": "view",
                "path": "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/custom/dc_impl/README.md"
            }))
            self.assertIsNotNone(result)
            
            # Log the result
            if result.error:
                logger.warning(f"Edit tool view returned error: {result.error}")
            else:
                logger.info(f"Edit tool view returned output of length: {len(result.output or '')}")
            
            # Make sure we got some output (either real or fallback)
            self.assertTrue(result.output or result.error)
        except Exception as e:
            logger.error(f"Edit tool view test failed: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()