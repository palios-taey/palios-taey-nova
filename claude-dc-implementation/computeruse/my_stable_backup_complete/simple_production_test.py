#!/usr/bin/env python3
"""
Simplified Production Test Script
"""

import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("production_test")

# Import protection components
from computer_use_demo.safe_ops.safe_file_operations import (
    read_file_safely, list_directory_safely, get_file_metadata, safe_file_ops
)
from computer_use_demo.token_management.token_manager import token_manager

def main():
    """Main test function"""
    test_start = datetime.now()
    logger.info(f"Starting simplified production test at {test_start}")
    
    # 1. Test safe file operations
    logger.info("\n--- Testing Safe File Operations ---")
    
    # List a directory
    logger.info("Listing directory: /home/computeruse/computer_use_demo")
    dir_contents = list_directory_safely("/home/computeruse/computer_use_demo")
    logger.info(f"Listed {len(dir_contents)} items")
    
    # Get metadata for a file
    sample_file = "/home/computeruse/computer_use_demo/requirements.txt"
    logger.info(f"Getting metadata for: {sample_file}")
    metadata = get_file_metadata(sample_file)
    logger.info(f"Metadata: {metadata}")
    
    # Read a file
    logger.info(f"Reading file: {sample_file}")
    content = read_file_safely(sample_file)
    logger.info(f"Read {len(content)} characters")
    
    # Check token usage after file operations
    logger.info(f"Token usage after file operations:")
    logger.info(f"Input tokens per minute: {token_manager.input_tokens_per_minute}/{token_manager.org_input_limit}")
    logger.info(f"Output tokens per minute: {token_manager.output_tokens_per_minute}/{token_manager.org_output_limit}")
    
    # 2. Test with a larger file
    logger.info("\n--- Testing with Larger File ---")
    
    # Read a larger file (token_manager.py)
    large_file = "/home/computeruse/computer_use_demo/token_management/token_manager.py"
    logger.info(f"Reading larger file: {large_file}")
    large_content = read_file_safely(large_file)
    logger.info(f"Read {len(large_content)} characters")
    
    # Check token usage after large file operation
    logger.info(f"Token usage after large file operation:")
    logger.info(f"Input tokens per minute: {token_manager.input_tokens_per_minute}/{token_manager.org_input_limit}")
    logger.info(f"Input token limit proximity: {token_manager.input_tokens_per_minute / token_manager.org_input_limit * 100:.2f}%")
    
    # Generate summary 
    test_end = datetime.now()
    test_duration = (test_end - test_start).total_seconds()
    
    logger.info("\n--- Test Summary ---")
    logger.info(f"Test duration: {test_duration:.2f} seconds")
    logger.info(f"Safe Operations target usage: {safe_file_ops.target_usage_percent}%")
    logger.info(f"Token Manager warning threshold: {token_manager.input_token_warning_threshold * 100}%")
    logger.info(f"Input tokens per minute: {token_manager.input_tokens_per_minute}/{token_manager.org_input_limit}")
    logger.info(f"Output tokens per minute: {token_manager.output_tokens_per_minute}/{token_manager.org_output_limit}")
    
    is_success = token_manager.input_tokens_per_minute < token_manager.org_input_limit * 0.8
    logger.info(f"Test result: {'SUCCESS' if is_success else 'WARNING - High token usage'}")

if __name__ == "__main__":
    main()