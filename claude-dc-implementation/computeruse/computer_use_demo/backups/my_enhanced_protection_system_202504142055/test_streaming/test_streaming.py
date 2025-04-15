#!/usr/bin/env python3
"""
Test Script for Enhanced Streaming Support

This script tests the enhanced streaming support module with various scenarios,
including long-running operations, error handling, and integration with other modules.
"""

import os
import sys
import time
import logging
import threading
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/streaming_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("streaming_test")

# Import the enhanced streaming client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from streaming_client import streaming_client

# Import token manager if available
try:
    sys.path.append('/home/computeruse/computer_use_demo')
    from token_management.token_manager import token_manager
    has_token_manager = True
    logger.info("Token manager found and imported")
except ImportError:
    has_token_manager = False
    logger.warning("Token manager not found, proceeding without token management")

# Import safe file operations if available
try:
    from safe_ops.safe_file_operations import read_file_safely, get_file_metadata
    has_safe_ops = True
    logger.info("Safe file operations found and imported")
except ImportError:
    has_safe_ops = False
    logger.warning("Safe file operations not found, proceeding without safe file operations")

def monitor_token_usage(duration, interval=5):
    """Monitor token usage over time
    
    Args:
        duration: Duration to monitor (seconds)
        interval: Interval between checks (seconds)
    """
    end_time = time.time() + duration
    
    print(f"\nMonitoring token usage for {duration} seconds...")
    print("Time | Input Tokens | Output Tokens | % of Limit")
    print("-" * 60)
    
    while time.time() < end_time:
        if has_token_manager:
            input_tokens = token_manager.input_tokens_per_minute
            output_tokens = token_manager.output_tokens_per_minute
            input_limit = token_manager.org_input_limit
            percent = (input_tokens / input_limit) * 100 if input_limit > 0 else 0
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{timestamp} | {input_tokens:12d} | {output_tokens:13d} | {percent:6.2f}%")
            
            # Log to file as well
            logger.info(f"Token usage: {input_tokens}/{input_limit} input, {output_tokens}/{token_manager.org_output_limit} output")
        else:
            print("Token manager not available for monitoring")
            break
        
        # Sleep for the interval
        time.sleep(interval)

def test_streaming_with_callback():
    """Test streaming with callback"""
    print("\n===== Test Streaming with Callback =====")
    
    received_chunks = []
    
    def stream_callback(chunk):
        received_chunks.append(chunk)
        print(f"Received chunk: {chunk[:20]}..." + ("..." if len(chunk) > 20 else ""))
    
    prompt = "Write a detailed paragraph about cloud computing technology."
    
    print(f"Sending prompt: {prompt}")
    start_time = time.time()
    
    response = streaming_client.create_message(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        thinking_budget=None,  # Disable thinking for this test
        stream_callback=stream_callback
    )
    
    duration = time.time() - start_time
    
    # Extract content from response
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                full_text = content[0]["text"]
                print(f"\nFull response: {full_text[:100]}...")
    
    print(f"\nReceived {len(received_chunks)} chunks in {duration:.2f} seconds")
    
    # Check token usage
    usage = streaming_client.last_token_usage
    print(f"Token usage: {usage['input']} input, {usage['output']} output")

def test_long_running_operation():
    """Test a long-running operation with streaming"""
    print("\n===== Test Long-Running Operation =====")
    
    # Prompt designed to generate a longer response
    prompt = """
Write a comprehensive explanation of how machine learning systems work, 
including:
1. The basic principles of ML
2. Different types of algorithms
3. Training and testing processes
4. Evaluation metrics
5. Common challenges
6. Recent advances in the field

Be thorough and detailed in your explanation of each section.
"""
    
    chunks_received = 0
    last_update = time.time()
    update_interval = 3  # seconds
    
    def stream_callback(chunk):
        nonlocal chunks_received, last_update
        chunks_received += 1
        
        current_time = time.time()
        if current_time - last_update >= update_interval:
            print(f"Received {chunks_received} chunks so far...")
            last_update = current_time
    
    print(f"Starting long-running operation with large response...")
    start_time = time.time()
    
    # Start token usage monitoring in a separate thread
    monitor_thread = threading.Thread(
        target=monitor_token_usage,
        args=(300,)  # Monitor for up to 5 minutes
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Make the API call with streaming
    response = streaming_client.create_message(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,  # Request a large number of tokens
        stream_callback=stream_callback
    )
    
    duration = time.time() - start_time
    
    # Extract content length from response
    content_length = 0
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                full_text = content[0]["text"]
                content_length = len(full_text)
    
    print(f"\nCompleted long-running operation in {duration:.2f} seconds")
    print(f"Received {chunks_received} chunks, total content length: {content_length} characters")
    
    # Check token usage
    usage = streaming_client.last_token_usage
    print(f"Token usage: {usage['input']} input, {usage['output']} output")
    
    # Wait for monitor thread to finish
    monitor_thread.join(timeout=1.0)

def test_file_integration():
    """Test integration with safe file operations"""
    if not has_safe_ops:
        print("\n===== Skipping File Integration Test (Safe Ops not available) =====")
        return
    
    print("\n===== Test Integration with Safe File Operations =====")
    
    # Read a file using safe operations
    file_path = "/home/computeruse/computer_use_demo/streaming/streaming_client.py"
    
    print(f"Reading file: {file_path}")
    content = read_file_safely(file_path)
    
    # Get metadata
    metadata = get_file_metadata(file_path)
    print(f"File metadata: {metadata}")
    
    # Create a prompt that includes file content
    prompt = f"Summarize the following Python code in a few sentences:\n\n```python\n{content[:2000]}\n```"
    
    print(f"Sending prompt with file content ({len(prompt)} characters)...")
    start_time = time.time()
    
    # Make the API call with streaming
    response = streaming_client.create_message(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        thinking_budget=None  # Disable thinking for this test
    )
    
    # Extract content
    content = ""
    if isinstance(response, dict) and "content" in response:
        if isinstance(response["content"], list) and response["content"] and "text" in response["content"][0]:
            content = response["content"][0]["text"]
    
    duration = time.time() - start_time
    
    print(f"\nReceived response in {duration:.2f} seconds")
    print(f"Response summary: {content[:150]}...")
    
    # Check token usage
    usage = streaming_client.last_token_usage
    print(f"Token usage: {usage['input']} input, {usage['output']} output")

def test_error_handling():
    """Test error handling and recovery"""
    print("\n===== Test Error Handling and Recovery =====")
    print("Note: This test simulates API errors and tests the retry mechanism")
    
    # Override the create method temporarily to simulate errors
    original_create = streaming_client.client.messages.create
    error_count = 0
    max_errors = 2
    
    def mock_create(**kwargs):
        nonlocal error_count
        # Simulate transient errors for the first few calls
        if error_count < max_errors:
            error_count += 1
            print(f"Simulating API error ({error_count}/{max_errors})...")
            raise Exception(f"Simulated API error {error_count}/{max_errors}")
        # Then succeed
        return original_create(**kwargs)
    
    # Apply the mock
    streaming_client.client.messages.create = mock_create
    
    try:
        print("Sending request (expecting retries)...")
        start_time = time.time()
        
        response = streaming_client.create_message(
            messages=[{"role": "user", "content": "Write a short sentence about error handling."}],
            max_tokens=50,
            thinking_budget=None  # Disable thinking for this test
        )
        
        # Extract content
        content = ""
        if isinstance(response, dict) and "content" in response:
            if isinstance(response["content"], list) and response["content"] and "text" in response["content"][0]:
                content = response["content"][0]["text"]
        
        duration = time.time() - start_time
        
        print(f"\nReceived response after {error_count} errors in {duration:.2f} seconds")
        print(f"Response: {content}")
        
        # Check if we got through the expected number of errors
        if error_count >= max_errors:
            print("✅ Successfully handled simulated errors and completed the request")
        else:
            print("❌ Did not encounter expected number of errors")
    finally:
        # Restore the original method
        streaming_client.client.messages.create = original_create

def main():
    parser = argparse.ArgumentParser(description="Test enhanced streaming support")
    parser.add_argument("--skip-callback", action="store_true", help="Skip callback test")
    parser.add_argument("--skip-long", action="store_true", help="Skip long-running operation test")
    parser.add_argument("--skip-file", action="store_true", help="Skip file integration test")
    parser.add_argument("--skip-error", action="store_true", help="Skip error handling test")
    args = parser.parse_args()
    
    print("Starting enhanced streaming support tests")
    
    if not args.skip_callback:
        test_streaming_with_callback()
    
    if not args.skip_long:
        test_long_running_operation()
    
    if not args.skip_file:
        test_file_integration()
    
    if not args.skip_error:
        test_error_handling()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()