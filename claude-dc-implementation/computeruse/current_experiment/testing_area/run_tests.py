#!/usr/bin/env python3
"""
Test Runner for Claude DC Phase 2 Enhancements
This script allows running individual or combined tests for Phase 2 features.
"""

import os
import sys
import argparse
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test_runner')

# Define test scripts
TESTS = {
    "streaming": {
        "basic": "./streaming/basic_streaming_test.py",
        "validation": "./streaming/tool_validation_test.py",
        "tools": "./streaming/streaming_with_tools_test.py",
    },
    "prompt_cache": {
        "basic": "./prompt_cache/prompt_cache_test.py",
    },
    "extended_output": {
        "basic": "./extended_output/extended_output_test.py",
    },
    "integration": {
        "all": "./integration_test.py",
    }
}

def run_test(test_path):
    """Run a single test script and return success status."""
    logger.info(f"Running test: {test_path}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, test_path],
            check=False,
            capture_output=True,
            text=True
        )
        end_time = time.time()
        
        # Print output
        print(f"\n{'=' * 80}")
        print(f"TEST RESULTS: {os.path.basename(test_path)}")
        print(f"{'=' * 80}")
        print(result.stdout)
        
        if result.stderr:
            print(f"\nERRORS:")
            print(result.stderr)
        
        print(f"\nExecution time: {end_time - start_time:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        
        success = result.returncode == 0
        logger.info(f"Test {test_path} {'succeeded' if success else 'failed'} with exit code {result.returncode}")
        
        return success
    except Exception as e:
        logger.error(f"Error running test {test_path}: {e}")
        print(f"\nError running test: {e}")
        return False

def run_test_group(group):
    """Run all tests in a group."""
    if group not in TESTS:
        logger.error(f"Unknown test group: {group}")
        print(f"Unknown test group: {group}")
        return False
    
    success = True
    for test_name, test_path in TESTS[group].items():
        print(f"\nRunning {group} test: {test_name}")
        test_success = run_test(test_path)
        success = success and test_success
    
    return success

def run_all_tests():
    """Run all available tests."""
    success = True
    for group in TESTS:
        group_success = run_test_group(group)
        success = success and group_success
    
    return success

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Claude DC Phase 2 Enhancement Tests")
    parser.add_argument("--group", choices=list(TESTS.keys()) + ["all"], help="Test group to run")
    parser.add_argument("--test", help="Specific test to run (format: group:test)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Set up API key environment variable if available
    api_key_path = Path.home() / ".anthropic" / "api_key"
    if api_key_path.exists():
        os.environ["ANTHROPIC_API_KEY"] = api_key_path.read_text().strip()
    
    if not args.group and not args.test:
        print("Running integration test (recommended first test)")
        success = run_test(TESTS["integration"]["all"])
    elif args.group:
        if args.group == "all":
            success = run_all_tests()
        else:
            success = run_test_group(args.group)
    elif args.test:
        if ":" not in args.test:
            print(f"Invalid test format. Use 'group:test', e.g., 'streaming:basic'")
            sys.exit(1)
        
        group, test = args.test.split(":", 1)
        if group not in TESTS or test not in TESTS[group]:
            print(f"Unknown test: {args.test}")
            sys.exit(1)
        
        success = run_test(TESTS[group][test])
    
    if success:
        print("\nAll tests completed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed. Check the logs for details.")
        sys.exit(1)