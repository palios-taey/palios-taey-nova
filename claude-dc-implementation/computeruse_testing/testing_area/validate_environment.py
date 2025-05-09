#!/usr/bin/env python3
"""
Environment Validation Script for Claude DC Phase 2 Enhancements
Checks that the development environment is properly set up.
"""

import os
import sys
import importlib
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude_dc.validate_env')

# Environment variables and constants
TEST_ENV = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/testing_area"
PROD_ENV = "/home/computeruse/computer_use_demo"
MAX_TOKENS = 16384
THINKING_BUDGET = 12000

def check_paths():
    """Verify that required paths exist."""
    paths = [
        (PROD_ENV, "Production environment"),
        (TEST_ENV, "Test environment"),
        (os.path.join(PROD_ENV, "loop.py"), "Production loop.py"),
        (os.path.join(PROD_ENV, "streamlit.py"), "Production streamlit.py"),
        (os.path.join(TEST_ENV, "backups"), "Backups directory")
    ]
    
    all_exist = True
    print("\nChecking required paths:")
    for path, description in paths:
        exists = os.path.exists(path)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{status} - {description}: {path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_python_modules():
    """Verify that required Python modules are available."""
    required_modules = [
        "anthropic", "streamlit", "asyncio", "httpx", "json", "logging"
    ]
    
    all_available = True
    print("\nChecking required Python modules:")
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ AVAILABLE - {module}")
        except ImportError:
            print(f"❌ MISSING - {module}")
            all_available = False
    
    return all_available

def check_anthropic_version():
    """Check that the anthropic SDK version is compatible."""
    try:
        import anthropic
        version = getattr(anthropic, "__version__", "unknown")
        print(f"\nAnthropicSDK Version: {version}")
        
        # Parse version
        if version != "unknown":
            major, minor, patch = map(int, version.split('.'))
            if major >= 0 and minor >= 39:
                print("✅ Version is compatible with prompt caching")
                return True
            else:
                print(f"❌ Version {version} may not support prompt caching (requires 0.39.0+)")
                return False
        else:
            print("⚠️ Could not determine Anthropic SDK version")
            return False
    except Exception as e:
        print(f"❌ Error checking Anthropic SDK version: {e}")
        return False

def check_api_key():
    """Check if the Anthropic API key is available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key_path = Path.home() / ".anthropic" / "api_key"
        if api_key_path.exists():
            print("\n✅ Anthropic API key found in ~/.anthropic/api_key")
            return True
        else:
            print("\n❌ Anthropic API key not found")
            return False
    else:
        print("\n✅ Anthropic API key found in environment")
        return True

def check_feature_flags():
    """Check if feature flags are properly set."""
    flags = {
        "ENABLE_STREAMING": os.environ.get("ENABLE_STREAMING", ""),
        "ENABLE_PROMPT_CACHE": os.environ.get("ENABLE_PROMPT_CACHE", ""),
        "ENABLE_EXTENDED_OUTPUT": os.environ.get("ENABLE_EXTENDED_OUTPUT", "")
    }
    
    print("\nFeature flags status:")
    for flag, value in flags.items():
        if value.lower() in ("true", "t", "yes", "y", "1"):
            print(f"✅ {flag}=true")
        elif value.lower() in ("false", "f", "no", "n", "0"):
            print(f"⚠️ {flag}=false")
        else:
            print(f"❌ {flag} not set")
    
    # Set default values if not set
    if not flags["ENABLE_STREAMING"]:
        os.environ["ENABLE_STREAMING"] = "false"
        print("Set default value: ENABLE_STREAMING=false")
    
    if not flags["ENABLE_PROMPT_CACHE"]:
        os.environ["ENABLE_PROMPT_CACHE"] = "false"
        print("Set default value: ENABLE_PROMPT_CACHE=false")
    
    if not flags["ENABLE_EXTENDED_OUTPUT"]:
        os.environ["ENABLE_EXTENDED_OUTPUT"] = "false"
        print("Set default value: ENABLE_EXTENDED_OUTPUT=false")
    
    return True

def run_test_command():
    """Run a test command to verify Python environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import sys; print(f'Python {sys.version} on {sys.platform}')"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"\nPython environment: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"\nError running Python test command: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Claude DC Environment Validation")
    print("=" * 80)
    
    # Run all checks
    paths_ok = check_paths()
    modules_ok = check_python_modules()
    api_key_ok = check_api_key()
    anthropic_version_ok = check_anthropic_version()
    feature_flags_ok = check_feature_flags()
    test_command_ok = run_test_command()
    
    # Overall status
    all_ok = paths_ok and modules_ok and api_key_ok and feature_flags_ok and test_command_ok
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ Environment validation PASSED - Ready to proceed with testing")
    else:
        print("❌ Environment validation FAILED - Please fix the issues above before proceeding")
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if all_ok else 1)