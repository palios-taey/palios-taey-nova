#!/usr/bin/env python3
"""
Test Integration Between Safe File Operations and Token Management

This script tests the integration between the enhanced Safe File Operations module
and the Token Management module, verifying that they work together to prevent rate limit errors.
"""

import os
import sys
import time
import random
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
sys.path.append('/home/computeruse/computer_use_demo')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integration_test")

# Import the optimized Safe File Operations
sys.path.insert(0, '/home/computeruse/computer_use_demo/test_optimization')
from safe_file_operations import read_file_safely, list_directory_safely, get_file_metadata, safe_file_ops

# Import Token Manager
from token_management.token_manager import token_manager

def create_test_files(test_dir, num_files=5):
    """
    Create test files of various sizes for testing
    
    Args:
        test_dir: Directory to create files in
        num_files: Number of files to create
    """
    os.makedirs(test_dir, exist_ok=True)
    
    # Create files of increasing sizes
    for i in range(1, num_files + 1):
        size = i * 10000  # 10KB, 20KB, 30KB, etc.
        filename = os.path.join(test_dir, f"test_file_{i}.txt")
        
        with open(filename, 'w') as f:
            # Write random text to the file to achieve desired size
            while f.tell() < size:
                # Generate random paragraph
                paragraph_length = random.randint(50, 200)
                paragraph = ' '.join([
                    ''.join(random.choices('abcdefghijklmnopqrstuvwxyz ', k=random.randint(3, 10)))
                    for _ in range(paragraph_length)
                ])
                f.write(paragraph + '\n\n')
        
        logger.info(f"Created test file: {filename} ({os.path.getsize(filename)} bytes)")

def test_token_estimation_accuracy():
    """
    Test the accuracy of token estimation methods
    """
    test_strings = [
        "This is a simple test string.",
        "This string has some numbers like 12345 and symbols !@#$%^&*().",
        "A longer paragraph with multiple sentences. This tests how the estimation works with longer text."
        "It should account for various patterns and structures in natural language. Let's see how it performs.",
        """A much longer text that spans multiple paragraphs.
        
        This will test how the estimation handles whitespace and newlines.
        We want to make sure it's accurate for both short and long inputs.
        
        The final paragraph continues with more text to ensure we have a good sample.
        Testing with different types of content is important."""
    ]
    
    print("\n===== Token Estimation Accuracy Test =====")
    print("String | Character-based | tiktoken | Ratio")
    print("-" * 60)
    
    for text in test_strings:
        # Character-based estimation (old method: 1 token ≈ 4 chars)
        char_based = len(text) // 4
        
        # tiktoken estimation (new method)
        tiktoken_count = safe_file_ops.estimate_tokens(text)
        
        # Calculate ratio
        ratio = tiktoken_count / char_based if char_based > 0 else 0
        
        # Print shortened text for display
        display_text = text[:30] + "..." if len(text) > 30 else text
        print(f"\"{display_text}\" | {char_based} | {tiktoken_count} | {ratio:.2f}")
    
    print("\nConclusion: tiktoken provides more accurate token counts compared to character-based estimation.")

def test_file_operations(test_dir):
    """
    Test file operations with the enhanced Safe File Operations module
    
    Args:
        test_dir: Directory containing test files
    """
    print("\n===== File Operations Test =====")
    
    # List directory contents
    print("\nListing directory contents:")
    dir_contents = list_directory_safely(test_dir)
    for item in dir_contents:
        if item.get("type") == "file":
            print(f"File: {item['name']} - Size: {item['size']} bytes - Tokens: {item['estimated_tokens']}")
        else:
            print(f"Directory: {item['name']}")
    
    # Get metadata for each file
    print("\nFile metadata:")
    for item in dir_contents:
        if item.get("type") == "file":
            metadata = get_file_metadata(os.path.join(test_dir, item["name"]))
            print(f"Metadata for {item['name']}: {metadata}")
    
    # Read each file
    print("\nReading files:")
    for item in dir_contents:
        if item.get("type") == "file":
            file_path = os.path.join(test_dir, item["name"])
            print(f"Reading {item['name']}...")
            content = read_file_safely(file_path)
            print(f"Read {len(content)} characters from {item['name']}")
            
            # Print token stats after each operation
            print(f"Token usage after operation: {token_manager.input_tokens_per_minute}/{token_manager.org_input_limit} input tokens per minute")

def test_rate_limit_handling(test_dir):
    """
    Test handling of rate limits with concurrent operations
    
    Args:
        test_dir: Directory containing test files
    """
    print("\n===== Rate Limit Handling Test =====")
    print("Simulating high-frequency requests with concurrent operations...")
    
    # Get list of test files
    files = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
    
    # Define worker function for thread pool
    def worker(file_path):
        try:
            print(f"Thread reading {os.path.basename(file_path)}...")
            content = read_file_safely(file_path)
            return f"Successfully read {os.path.basename(file_path)}: {len(content)} characters"
        except Exception as e:
            return f"Error reading {os.path.basename(file_path)}: {e}"
    
    # Use ThreadPoolExecutor to simulate concurrent requests
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(worker, files * 2))  # Read each file twice to generate more requests
    
    # Print results
    for result in results:
        print(result)
    
    print("\nToken Manager stats after concurrent operations:")
    print(f"Input tokens per minute: {token_manager.input_tokens_per_minute}/{token_manager.org_input_limit}")
    print(f"Output tokens per minute: {token_manager.output_tokens_per_minute}/{token_manager.org_output_limit}")

def main():
    parser = argparse.ArgumentParser(description="Test integration between Safe File Operations and Token Management")
    parser.add_argument("--test-dir", default="/tmp/safe_ops_test", help="Directory for test files")
    parser.add_argument("--create-files", action="store_true", help="Create test files")
    parser.add_argument("--skip-estimation", action="store_true", help="Skip token estimation test")
    parser.add_argument("--skip-file-ops", action="store_true", help="Skip file operations test")
    parser.add_argument("--skip-rate-limit", action="store_true", help="Skip rate limit test")
    args = parser.parse_args()
    
    print("Starting integration test between Safe File Operations and Token Management")
    print(f"Safe File Operations target usage: {safe_file_ops.target_usage_percent}%")
    print(f"Token Manager input token warning threshold: {token_manager.input_token_warning_threshold * 100}%")
    
    # Create test files if requested
    if args.create_files:
        print("\nCreating test files...")
        create_test_files(args.test_dir)
    
    # Run token estimation accuracy test
    if not args.skip_estimation:
        test_token_estimation_accuracy()
    
    # Run file operations test
    if not args.skip_file_ops:
        test_file_operations(args.test_dir)
    
    # Run rate limit handling test
    if not args.skip_rate_limit:
        test_rate_limit_handling(args.test_dir)
    
    print("\nIntegration test completed!")

if __name__ == "__main__":
    main()