#!/usr/bin/env python3
"""
Test Suite for Claude DC Phase 2 Enhancements
Follows DCCC's test plan for comprehensive validation.
"""

import os
import sys
import argparse
import subprocess
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_suite.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_dc.test_suite')

# Environment variables and constants
TEST_ENV = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/testing_area"
PROD_ENV = "/home/computeruse/computer_use_demo"
MAX_TOKENS = 16384
THINKING_BUDGET = 12000

# Define test modules according to DCCC's plan
TEST_MODULES = {
    "stream": [
        {"name": "Incremental token output", "script": "stream/stream_test.py"},
        {"name": "Tool use during streaming", "script": "stream/stream_tool_test.py"}
    ],
    "cache": [
        {"name": "Ephemeral message flagging", "script": "cache/cache_test.py"}
    ],
    "output": [
        {"name": "128K token generation", "script": "output/output_test.py"}
    ],
    "integration": [
        {"name": "All features combined", "script": "integration_test.py"}
    ]
}

FEATURE_STATUS = {
    "streaming": "NOT_IMPLEMENTED",
    "prompt_cache": "NOT_IMPLEMENTED",
    "extended_output": "NOT_IMPLEMENTED"
}

# Test sequence: STREAM→CACHE→OUTPUT→INTEGRATE
TEST_SEQUENCE = ["stream", "cache", "output", "integration"]

def setup_test_environment():
    """Set up the test environment and create necessary directories."""
    logger.info("Setting up test environment")
    
    try:
        # Create directory structure if it doesn't exist
        for dir_name in ["backups", "stream", "cache", "output", "logs"]:
            os.makedirs(os.path.join(TEST_ENV, dir_name), exist_ok=True)
        
        # Set environment variables for tests
        os.environ["MAX_TOKENS"] = str(MAX_TOKENS)
        os.environ["THINKING_BUDGET"] = str(THINKING_BUDGET)
        
        # Create feature flags
        os.environ["ENABLE_STREAMING"] = "false"
        os.environ["ENABLE_PROMPT_CACHE"] = "false"
        os.environ["ENABLE_EXTENDED_OUTPUT"] = "false"
        
        logger.info("Test environment set up successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to set up test environment: {e}")
        return False

def backup_production_files():
    """Create backups of critical production files."""
    logger.info("Backing up production files")
    
    try:
        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(TEST_ENV, "backups", timestamp)
        os.makedirs(backup_dir, exist_ok=True)
        
        # List of files to backup
        files_to_backup = ["loop.py", "streamlit.py", "__init__.py"]
        
        # Create backups
        for file in files_to_backup:
            src = os.path.join(PROD_ENV, file)
            dst = os.path.join(backup_dir, f"{file}.bak")
            if os.path.exists(src):
                with open(src, 'r') as f_src, open(dst, 'w') as f_dst:
                    f_dst.write(f_src.read())
                logger.info(f"Backed up {src} to {dst}")
            else:
                logger.warning(f"Source file {src} not found, skipping backup")
        
        logger.info("Production files backed up successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to backup production files: {e}")
        return False

def run_test(test_script):
    """Run a single test script and return success status."""
    logger.info(f"Running test: {test_script}")
    
    full_path = os.path.join(TEST_ENV, test_script)
    if not os.path.exists(full_path):
        logger.error(f"Test script not found: {full_path}")
        return False
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, full_path],
            check=False,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Use current environment variables
        )
        end_time = time.time()
        
        # Log results
        log_file = os.path.join(TEST_ENV, "logs", f"{os.path.basename(test_script)}.log")
        with open(log_file, 'w') as f:
            f.write(f"Test: {test_script}\n")
            f.write(f"Exit Code: {result.returncode}\n")
            f.write(f"Duration: {end_time - start_time:.2f} seconds\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")
        
        # Print summary to console
        print(f"\n{'=' * 80}")
        print(f"TEST RESULTS: {test_script}")
        print(f"{'=' * 80}")
        print(f"Duration: {end_time - start_time:.2f} seconds")
        print(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            print(f"\nOutput preview:")
            print("\n".join(result.stdout.splitlines()[:10]))
            if len(result.stdout.splitlines()) > 10:
                print(f"... (see {log_file} for full output)")
        
        if result.stderr:
            print(f"\nErrors:")
            print(result.stderr)
        
        success = result.returncode == 0
        logger.info(f"Test {test_script} {'succeeded' if success else 'failed'} with exit code {result.returncode}")
        
        return success
    except Exception as e:
        logger.error(f"Error running test {test_script}: {e}")
        print(f"\nError running test: {e}")
        return False

def run_tests_by_feature(feature, verbose=False):
    """Run all tests for a specific feature."""
    if feature not in TEST_MODULES and feature != "all":
        logger.error(f"Unknown feature: {feature}")
        print(f"Unknown feature: {feature}")
        return False
    
    results = []
    
    if feature == "all":
        # Run tests in the specified sequence
        for seq_feature in TEST_SEQUENCE:
            # Enable appropriate feature flags
            if seq_feature == "stream":
                os.environ["ENABLE_STREAMING"] = "true"
                os.environ["ENABLE_PROMPT_CACHE"] = "false"
                os.environ["ENABLE_EXTENDED_OUTPUT"] = "false"
            elif seq_feature == "cache":
                os.environ["ENABLE_STREAMING"] = "true"
                os.environ["ENABLE_PROMPT_CACHE"] = "true"
                os.environ["ENABLE_EXTENDED_OUTPUT"] = "false"
            elif seq_feature == "output":
                os.environ["ENABLE_STREAMING"] = "true"
                os.environ["ENABLE_PROMPT_CACHE"] = "true"
                os.environ["ENABLE_EXTENDED_OUTPUT"] = "true"
            
            # Run tests for this feature
            for test_info in TEST_MODULES[seq_feature]:
                test_name = test_info["name"]
                test_script = test_info["script"]
                print(f"\nRunning {seq_feature} test: {test_name}")
                success = run_test(test_script)
                results.append({
                    "feature": seq_feature,
                    "name": test_name,
                    "script": test_script,
                    "success": success
                })
    else:
        # Enable only the specified feature
        os.environ["ENABLE_STREAMING"] = "true" if feature == "stream" else "false"
        os.environ["ENABLE_PROMPT_CACHE"] = "true" if feature == "cache" else "false"
        os.environ["ENABLE_EXTENDED_OUTPUT"] = "true" if feature == "output" else "false"
        
        # Run tests for this feature
        for test_info in TEST_MODULES[feature]:
            test_name = test_info["name"]
            test_script = test_info["script"]
            print(f"\nRunning {feature} test: {test_name}")
            success = run_test(test_script)
            results.append({
                "feature": feature,
                "name": test_name,
                "script": test_script,
                "success": success
            })
    
    # Calculate success rate
    total_tests = len(results)
    successful_tests = sum(1 for result in results if result["success"])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Print summary
    print(f"\n{'=' * 80}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total tests: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"{'=' * 80}")
    
    # Print detailed results if verbose
    if verbose:
        print("\nDetailed Results:")
        for result in results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status} - {result['feature']}: {result['name']} ({result['script']})")
    
    # Save results to file
    results_file = os.path.join(TEST_ENV, "logs", f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "results": results
        }, f, indent=2)
    
    # Update feature status based on test results
    if feature == "all" or feature == "stream":
        FEATURE_STATUS["streaming"] = "IMPLEMENTED" if all(r["success"] for r in results if r["feature"] == "stream") else "PARTIAL"
    if feature == "all" or feature == "cache":
        FEATURE_STATUS["prompt_cache"] = "IMPLEMENTED" if all(r["success"] for r in results if r["feature"] == "cache") else "PARTIAL"
    if feature == "all" or feature == "output":
        FEATURE_STATUS["extended_output"] = "IMPLEMENTED" if all(r["success"] for r in results if r["feature"] == "output") else "PARTIAL"
    
    # Save feature status
    status_file = os.path.join(TEST_ENV, "feature_status.json")
    with open(status_file, 'w') as f:
        json.dump(FEATURE_STATUS, f, indent=2)
    
    logger.info(f"Test results saved to {results_file}")
    logger.info(f"Feature status saved to {status_file}")
    
    return success_rate == 100

def verify_context_preservation():
    """Verify that context is preserved across restarts."""
    logger.info("Verifying context preservation")
    
    try:
        # This would call the context preservation test
        # For now, we'll just log that this would be implemented
        logger.info("Context preservation verification would be implemented here")
        print("Context preservation verification would be implemented here")
        return True
    except Exception as e:
        logger.error(f"Error verifying context preservation: {e}")
        return False

def check_error_logs():
    """Check error logs for unexpected behaviors."""
    logger.info("Checking error logs")
    
    try:
        # Look for errors in log files
        error_count = 0
        log_dir = os.path.join(TEST_ENV, "logs")
        
        for log_file in os.listdir(log_dir):
            if log_file.endswith(".log"):
                with open(os.path.join(log_dir, log_file), 'r') as f:
                    log_content = f.read()
                    # Count error occurrences
                    errors = log_content.count("ERROR")
                    warnings = log_content.count("WARNING")
                    error_count += errors
                    
                    if errors > 0 or warnings > 0:
                        print(f"Found {errors} errors and {warnings} warnings in {log_file}")
        
        print(f"Total errors found: {error_count}")
        return error_count == 0
    except Exception as e:
        logger.error(f"Error checking logs: {e}")
        return False

def monitor_token_usage():
    """Monitor token usage across operations."""
    logger.info("Monitoring token usage")
    
    try:
        # This would analyze token usage from test results
        # For now, we'll just log that this would be implemented
        logger.info("Token usage monitoring would be implemented here")
        print("Token usage monitoring would be implemented here")
        return True
    except Exception as e:
        logger.error(f"Error monitoring token usage: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Claude DC Phase 2 Enhancement Tests")
    parser.add_argument("--feature", choices=list(TEST_MODULES.keys()) + ["all"], default="all", help="Feature to test")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Set logging level")
    parser.add_argument("--skip-backup", action="store_true", help="Skip production file backup")
    parser.add_argument("--verify-context", action="store_true", help="Verify context preservation")
    parser.add_argument("--check-logs", action="store_true", help="Check error logs")
    parser.add_argument("--monitor-tokens", action="store_true", help="Monitor token usage")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    print("=" * 80)
    print("Claude DC Phase 2 Enhancement Test Suite")
    print("=" * 80)
    print(f"Testing feature: {args.feature}")
    print(f"Verbose output: {args.verbose}")
    print(f"Log level: {args.log_level}")
    print("=" * 80)
    
    # Set up test environment
    setup_test_environment()
    
    # Backup production files unless skipped
    if not args.skip_backup:
        backup_production_files()
    
    # Run tests
    test_success = run_tests_by_feature(args.feature, args.verbose)
    
    # Additional validation if requested
    if args.verify_context:
        verify_context_preservation()
    
    if args.check_logs:
        check_error_logs()
    
    if args.monitor_tokens:
        monitor_token_usage()
    
    # Exit with appropriate code
    sys.exit(0 if test_success else 1)