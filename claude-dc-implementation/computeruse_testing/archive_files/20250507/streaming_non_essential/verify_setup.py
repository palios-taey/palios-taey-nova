#!/usr/bin/env python3
"""
Verification script for the streaming implementation.

This script verifies that all required dependencies and files are in place
for the streaming implementation to work correctly.
"""

import os
import sys
import importlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("verify_setup")

def check_python_version():
    """Check that the Python version is compatible."""
    print(f"\nPython Version: {sys.version}")
    
    major, minor, micro = sys.version_info[:3]
    if major < 3 or (major == 3 and minor < 9):
        print("Warning: Python 3.9 or higher is recommended for the streaming implementation.")
        return False
    
    print("✓ Python version is compatible.")
    return True

def check_dependencies():
    """Check that required packages are installed."""
    required_packages = ["anthropic", "asyncio"]
    missing_packages = []
    
    print("\nChecking required packages:")
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} is installed.")
        except ImportError:
            print(f"✗ {package} is not installed.")
            missing_packages.append(package)
    
    if missing_packages:
        print("\nMissing packages:")
        print(" ".join(missing_packages))
        print("\nPlease install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_anthropic_version():
    """Check that the Anthropic SDK version is compatible."""
    try:
        import anthropic
        version = anthropic.__version__
        print(f"\nAnthropic SDK Version: {version}")
        
        # Check if the version is compatible
        major, minor, patch = map(int, version.split("."))
        if major < 0 or (major == 0 and minor < 5):
            print("Warning: Anthropic SDK 0.5.0 or higher is required for the streaming implementation.")
            return False
        
        print("✓ Anthropic SDK version is compatible.")
        return True
    except (ImportError, AttributeError):
        print("✗ Could not determine Anthropic SDK version.")
        return False

def check_required_files():
    """Check that all required files for the streaming implementation are in place."""
    files_to_check = [
        Path(__file__).parent / "unified_streaming_loop.py",
        Path(__file__).parent / "streaming_enhancements.py",
        Path(__file__).parent / "feature_toggles.json",
        Path(__file__).parent / "tools" / "dc_bash.py",
        Path(__file__).parent / "tools" / "dc_file.py",
        Path(__file__).parent / "models" / "dc_models.py"
    ]
    
    print("\nChecking required files:")
    missing_files = []
    
    for file_path in files_to_check:
        if file_path.exists():
            print(f"✓ {file_path.relative_to(Path(__file__).parent)} exists.")
        else:
            print(f"✗ {file_path.relative_to(Path(__file__).parent)} is missing.")
            missing_files.append(file_path)
    
    if missing_files:
        print("\nMissing files:")
        for file_path in missing_files:
            print(f"  {file_path.relative_to(Path(__file__).parent)}")
        return False
    
    return True

def check_api_key():
    """Check if the API key is available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:]
        print(f"\n✓ API key is set: {masked_key}")
        return True
    else:
        print("\n✗ API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
        return False

def main():
    """Run all verification checks."""
    print("===== Streaming Implementation Verification =====")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Dependencies", check_dependencies),
        ("Anthropic SDK Version", check_anthropic_version),
        ("Required Files", check_required_files),
        ("API Key", check_api_key)
    ]
    
    all_passed = True
    results = []
    
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
            all_passed = all_passed and passed
        except Exception as e:
            logger.exception(f"Error during {name} check")
            results.append((name, False))
            all_passed = False
    
    print("\n===== Verification Summary =====")
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
    
    if all_passed:
        print("\n✅ All checks passed! The streaming implementation is ready to use.")
        return 0
    else:
        print("\n❌ Some checks failed. Please address the issues before using the streaming implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())