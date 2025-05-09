#!/usr/bin/env python3
"""
Test Runner for Claude DC Streaming Implementation Tests

This script runs all the tests for Claude DC's streaming implementation
and generates a comprehensive report of test results.
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"claude_dc_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger('claude_dc.test_runner')

# Import test modules
sys.path.insert(0, str(Path(__file__).parent))
from test_framework import TestSuite
import mock_streamlit_tests
import error_fix_tests

async def run_all_test_suites():
    """Run all test suites and generate a report."""
    start_time = time.time()
    
    # Print header
    print("\n" + "=" * 80)
    print("CLAUDE DC STREAMING WITH TOOL USE - TEST SUITE")
    print("=" * 80)
    print(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print("=" * 80 + "\n")
    
    # Collect all test suites
    test_suites = [
        # Mock Streamlit Tests
        mock_streamlit_tests.streamlit_ui_suite,
        mock_streamlit_tests.callback_validation_suite,
        mock_streamlit_tests.error_path_suite,
        mock_streamlit_tests.api_interaction_suite,
        mock_streamlit_tests.deployment_suite,
        
        # Error Fix Tests
        error_fix_tests.none_type_error_suite,
        error_fix_tests.type_iteration_error_suite,
    ]
    
    # Run all test suites
    results = []
    for suite in test_suites:
        logger.info(f"Running test suite: {suite.name}")
        await suite.run()
        suite.print_results()
        results.append(suite)
    
    # Generate summary report
    total_tests = sum(len(suite.results) for suite in results)
    total_passed = sum(sum(1 for r in suite.results if r.status.value == "PASSED") for suite in results)
    total_failed = sum(sum(1 for r in suite.results if r.status.value == "FAILED") for suite in results)
    total_errors = sum(sum(1 for r in suite.results if r.status.value == "ERROR") for suite in results)
    total_skipped = sum(sum(1 for r in suite.results if r.status.value == "SKIPPED") for suite in results)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total test suites: {len(results)}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    print(f"Duration: {duration:.2f} seconds")
    print("=" * 80)
    
    # Add suite-specific details
    for suite in results:
        passed = sum(1 for r in suite.results if r.status.value == "PASSED")
        total = len(suite.results)
        print(f"{suite.name}: {passed}/{total} passed")
    
    print("\n" + "=" * 80)
    print("TEST ACTIONS REQUIRED")
    print("=" * 80)
    
    if total_failed > 0 or total_errors > 0:
        print("⚠️ TESTS FAILED - Action required:")
        for suite in results:
            for result in suite.results:
                if result.status.value in ["FAILED", "ERROR"]:
                    print(f"- {suite.name}.{result.name}: {result.message}")
        print("\nRecommendation: Apply fixes from fixed_loop.py and fixed_streamlit_api_callback.py")
    else:
        print("✅ ALL TESTS PASSED")
        print("\nRecommendation: Deploy the fixed implementations to production")
    
    print("=" * 80)
    return results

if __name__ == "__main__":
    asyncio.run(run_all_test_suites())