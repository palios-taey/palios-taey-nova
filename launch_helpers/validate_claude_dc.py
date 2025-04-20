#!/usr/bin/env python3
"""
Validation script for Claude DC Phase 2 Enhancements
Checks if all required components and features are properly set up
"""

import importlib
import os
import sys
import subprocess
from pathlib import Path

# Add repository root to Python path
REPO_ROOT = Path('/home/jesse/projects/palios-taey-nova')
CLAUDE_DC_ROOT = REPO_ROOT / 'claude-dc-implementation'
COMPUTER_USE_DEMO = CLAUDE_DC_ROOT / 'computeruse' / 'computer_use_demo'

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CLAUDE_DC_ROOT))
sys.path.insert(0, str(CLAUDE_DC_ROOT / 'computeruse'))

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_imports():
    """Check if required imports work correctly"""
    print_section("Checking imports")
    
    try:
        import computer_use_demo
        from computer_use_demo import (
            PROMPT_CACHING_BETA_FLAG,
            OUTPUT_128K_BETA_FLAG,
            DEFAULT_MAX_TOKENS,
            ENABLE_PROMPT_CACHING,
            ENABLE_EXTENDED_OUTPUT,
        )
        print("✅ Base module imports work")
    except ImportError as e:
        print(f"❌ Failed to import from computer_use_demo: {e}")
        return False
    
    # Scan for StrEnum imports across all Python files
    print("\nChecking for StrEnum compatibility issues:")
    try:
        import sys
        
        # Create custom StrEnum for Python 3.10 if needed
        has_strenum = False
        try:
            from enum import StrEnum
            has_strenum = True
            print("✅ Native StrEnum is available in current Python version")
        except ImportError:
            print("❌ Native StrEnum not available - checking for custom implementation")
            
        # Check all Python files for direct StrEnum imports
        python_files = []
        
        # Check loop.py and streamlit.py specifically
        key_files = ['loop.py', 'streamlit.py']
        for filename in key_files:
            filepath = COMPUTER_USE_DEMO / filename
            if os.path.exists(filepath):
                python_files.append(filepath)
                    
        # Analyze each file for StrEnum usage
        problematic_files = []
        custom_implementation_found = False
        
        for filepath in python_files:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Check if file has direct import from enum without custom implementation
            if "from enum import StrEnum" in content and not "if sys.version_info < (3, 11)" in content:
                if not has_strenum:
                    problematic_files.append(os.path.basename(filepath))
                    
            # Check for custom StrEnum implementation
            if "class StrEnum(str, Enum)" in content:
                custom_implementation_found = True
                print(f"✅ Found custom StrEnum implementation in {os.path.basename(filepath)}")
                
        # Report findings
        if custom_implementation_found:
            print("✅ Custom StrEnum implementation exists")
        else:
            print("❌ No custom StrEnum implementation found, but needed for Python 3.10")
            
        if problematic_files:
            print(f"❌ Found direct 'from enum import StrEnum' in: {', '.join(problematic_files)}")
            print("   This will cause errors on Python 3.10")
            return False
        else:
            print("✅ No problematic direct StrEnum imports found")
    except Exception as e:
        print(f"❌ StrEnum compatibility check failed: {e}")
        return False
    
    try:
        # Check if sampling_loop exists in loop.py without importing it
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if "async def sampling_loop" in loop_content:
            print("✅ sampling_loop function exists in loop.py")
        else:
            print("❌ sampling_loop function not found in loop.py")
            return False
    except Exception as e:
        print(f"❌ Checking loop.py failed: {e}")
        return False
    
    try:
        # Check if tools module exists by checking for tool files
        if os.path.exists(COMPUTER_USE_DEMO / 'tools'):
            tool_files = os.listdir(COMPUTER_USE_DEMO / 'tools')
            if '__init__.py' in tool_files and 'base.py' in tool_files:
                print("✅ tools module exists with required files")
            else:
                print("⚠️ tools module exists but may be missing key files")
        else:
            print("❌ tools module directory not found")
            return False
    except Exception as e:
        print(f"❌ Checking tools module failed: {e}")
        return False
    
    try:
        # Try testing streamlit imports
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit is not installed")
        return False
    
    return True

def check_api_functionality():
    """Check if Anthropic API functionality works"""
    print_section("Checking Anthropic API functionality")
    
    try:
        from anthropic import Anthropic
        print("✅ Anthropic SDK is installed")
    except ImportError:
        print("❌ Anthropic SDK is not installed")
        return False
    
    # Check API key configuration
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("✅ ANTHROPIC_API_KEY is set in environment")
    else:
        anthropic_dir = Path.home() / '.anthropic'
        api_key_file = anthropic_dir / 'api_key'
        if api_key_file.exists():
            print("✅ API key file exists at ~/.anthropic/api_key")
        else:
            print("⚠️ No API key found in environment or ~/.anthropic/api_key")
            print("   You will need to enter an API key in the UI")
    
    return True

def check_streaming_support():
    """Check if streaming support is properly configured"""
    print_section("Checking streaming support")
    
    try:
        # Check loop.py for streaming parameter
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if '"stream": True' in loop_content:
            print("✅ Streaming is enabled in loop.py")
        else:
            print("❌ Streaming parameter not found in loop.py")
            return False
        
        # Check streamlit.py for streaming callbacks
        with open(COMPUTER_USE_DEMO / 'streamlit.py', 'r') as f:
            streamlit_content = f.read()
            
        if '_streaming_output_callback' in streamlit_content:
            print("✅ Streaming callback handler found in streamlit.py")
        else:
            print("❌ Streaming callback handler not found in streamlit.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking streaming support: {e}")
        return False

def check_prompt_caching():
    """Check if prompt caching is properly configured"""
    print_section("Checking prompt caching beta")
    
    try:
        # Read the config and loop files directly instead of importing
        with open(COMPUTER_USE_DEMO / '__init__.py', 'r') as f:
            init_content = f.read()
            
        # Check if prompt caching is enabled in config
        if "ENABLE_PROMPT_CACHING = True" in init_content:
            print("✅ Prompt caching is enabled in configuration")
        else:
            print("⚠️ Prompt caching is disabled in configuration")
        
        # Check loop.py for prompt caching functionality
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        # Define what we're looking for - just essential pieces
        cache_indicators = [
            "_inject_prompt_caching",  # Function name
            "PROMPT_CACHING_BETA_FLAG", # Constant reference
            "cache_control"  # Cache control setting
        ]
        
        # Check each indicator
        missing = []
        for indicator in cache_indicators:
            if indicator in loop_content:
                print(f"✅ Found {indicator} in loop.py")
            else:
                missing.append(indicator)
                print(f"❌ Missing {indicator} in loop.py")
        
        if not missing:
            print("✅ Prompt caching implementation is complete in loop.py")
            return True
        else:
            print(f"❌ Prompt caching incomplete: missing {', '.join(missing)}")
            return False
        
    except Exception as e:
        print(f"❌ Error checking prompt caching: {e}")
        return False

def check_extended_output():
    """Check if 128K extended output is properly configured"""
    print_section("Checking 128K extended output")
    
    try:
        # Read the configuration and loop file directly
        with open(COMPUTER_USE_DEMO / '__init__.py', 'r') as f:
            init_content = f.read()
        
        # Check if extended output is enabled in config
        if "ENABLE_EXTENDED_OUTPUT = True" in init_content:
            print("✅ Extended output is enabled in configuration")
        else:
            print("⚠️ Extended output is disabled in configuration (optional feature)")
        
        # Check if max tokens is properly set 
        if "DEFAULT_MAX_TOKENS = 65536" in init_content:
            print("✅ Default max tokens set to 65536")
        else:
            print("❌ Default max tokens not properly configured")
            return False
        
        # Check loop.py for extended output features
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
        
        # Define the indicators we're looking for
        extended_output_indicators = [
            "claude-3-7",
            "extended output",
            "max_tokens"
        ]
        
        # Check each indicator
        for indicator in extended_output_indicators:
            if indicator in loop_content.lower():
                print(f"✅ Found {indicator} in loop.py")
            else:
                print(f"❌ Missing {indicator} in loop.py")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking extended output: {e}")
        return False

def check_real_time_tool_output():
    """Check if real-time tool output is properly configured"""
    print_section("Checking real-time tool output")
    
    try:
        # Check loop.py for tool streaming
        with open(COMPUTER_USE_DEMO / 'loop.py', 'r') as f:
            loop_content = f.read()
            
        if "streaming=True" in loop_content and "set_stream_callback" in loop_content:
            print("✅ Real-time tool streaming is configured in loop.py")
        else:
            print("❌ Real-time tool streaming not properly configured in loop.py")
            return False
        
        # Check streamlit.py for tool callbacks
        with open(COMPUTER_USE_DEMO / 'streamlit.py', 'r') as f:
            streamlit_content = f.read()
            
        if "is_streaming" in streamlit_content and "tool_placeholders" in streamlit_content:
            print("✅ Tool streaming UI handlers found in streamlit.py")
        else:
            print("❌ Tool streaming UI handlers not found in streamlit.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking real-time tool output: {e}")
        return False

def check_runtime_imports():
    """Advanced runtime import validation by actually executing imports"""
    print_section("Runtime Import Testing")
    
    try:
        print("Simulating runtime environment...")
        # Create a temporary script to test imports in a realistic environment
        test_script = Path("/tmp/claude_dc_import_test.py")
        with open(test_script, "w") as f:
            f.write('''
import os
import sys
import traceback

# Store original path
original_sys_path = list(sys.path)

# Add repo paths
repo_root = os.path.abspath(os.path.expanduser("'''+str(REPO_ROOT)+'''"))
module_path = os.path.join(repo_root, "claude-dc-implementation/computeruse")
sys.path.insert(0, repo_root)
sys.path.insert(0, module_path)

# Set PYTHONPATH to match what the launcher would do
os.environ["PYTHONPATH"] = f"{repo_root}:{module_path}"

print("\\nTesting direct imports...")
success = True
errors = []

# Track what was imported
imported = {}

try:
    # Test direct imports
    try:
        from computer_use_demo import (
            PROMPT_CACHING_BETA_FLAG,
            OUTPUT_128K_BETA_FLAG,
            DEFAULT_MAX_TOKENS
        )
        imported["constants"] = True
        print("✅ Direct constants import worked")
    except Exception as e:
        success = False
        imported["constants"] = False
        errors.append(f"❌ Failed to import constants: {e}\\n{traceback.format_exc()}")
    
    try:
        from enum import StrEnum
        imported["strenum"] = "native"
        print("✅ Native StrEnum import worked")
    except ImportError:
        # Expected on Python 3.10
        print("⚠️ Native StrEnum not available (this is expected on Python 3.10)")
        imported["strenum"] = False
    
    print("\\nTesting streamlit module...")
    try:
        import streamlit
        imported["streamlit"] = True
        print("✅ Streamlit import worked")
    except Exception as e:
        success = False
        imported["streamlit"] = False
        errors.append(f"❌ Failed to import streamlit: {e}")
    
    print("\\nTesting relative imports...")
    try:
        sys.path.append(os.path.join(module_path, 'computer_use_demo'))
        os.chdir(os.path.join(module_path, 'computer_use_demo'))
        try:
            # This is the critical import that would fail in streamlit.py
            from computer_use_demo.tools import ToolResult
            imported["tool_direct"] = True
            print("✅ Direct tool imports worked")
        except Exception as e:
            try:
                # Try relative import
                from .tools import ToolResult
                imported["tool_relative"] = True
                print("✅ Relative tool imports worked")
            except Exception as e2:
                success = False
                imported["tool_any"] = False
                errors.append(f"❌ Failed both direct and relative tool imports:\\nDirect: {e}\\nRelative: {e2}")
    except Exception as e:
        success = False
        errors.append(f"❌ Failed setting up relative import test: {e}")
    
    print("\\nValidating fallback mechanisms...")
    # Test if our fallback constants would work
    if not imported.get("constants", False):
        try:
            # Define fallback constants directly as in streamlit.py
            PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
            OUTPUT_128K_BETA_FLAG = "output-128k-2025-02-19"
            DEFAULT_MAX_TOKENS = 65536
            print("✅ Fallback constants defined successfully")
        except Exception as e:
            success = False
            errors.append(f"❌ Failed to define fallback constants: {e}")
            
    # Reset path
    sys.path = original_sys_path
    
    print("\\nImport test summary:")
    for key, value in imported.items():
        print(f"- {key}: {'✅ Successful' if value else '❌ Failed'}")
        
    if errors:
        print("\\nDetailed errors:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}\\n")
            
    # Return success flag from the try block
    print(f"Test complete, success={success}")
    
# End of try/finally in script
except Exception as e:
    import traceback
    with open("/tmp/claude_dc_import_test_error.log", "w") as f:
        f.write(traceback.format_exc())
    print(f"❌ Runtime import test failed with error: {e}")
    print(f"Check /tmp/claude_dc_import_test_error.log for details")
    sys.exit(1)
            ''')
            
        # Make the script executable
        os.chmod(test_script, 0o755)
        
        # Execute the test script in a separate process
        print("Executing import test script...")
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                check=False,
                text=True,
                timeout=10
            )
            
            # Display output
            print(result.stdout)
            if result.returncode != 0:
                print(f"Script exited with code: {result.returncode}")
            if result.stderr:
                print(f"Errors detected:\n{result.stderr}")
                
            # Check for specific import error patterns
            if "No module named" in result.stderr or "ModuleNotFoundError" in result.stderr:
                print("❌ Module import errors detected in runtime test")
                return False
                
            # Check for success=True in the output
            # Note: We expect strenum to fail but that's ok as we have our custom implementation
            return "success=True" in result.stdout
        except subprocess.TimeoutExpired:
            print("❌ Import test timed out - likely an import hang or circular dependency")
            return False
        finally:
            # Clean up
            if test_script.exists():
                os.unlink(test_script)
                
    except Exception as e:
        print(f"❌ Failed to create or run import test script: {e}")
        return False


def check_environment_paths():
    """Check if PYTHONPATH and other environment variables would work correctly"""
    print_section("Environment Path Validation")
    
    # Create a temporary script to test environment setup
    test_script = Path("/tmp/claude_dc_path_test.py")
    try:
        with open(test_script, "w") as f:
            # Escape curly braces with double curly braces for f-string
            f.write(f'''
#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Key directories
REPO_ROOT = Path("{REPO_ROOT}")
CLAUDE_DC_ROOT = REPO_ROOT / "claude-dc-implementation"
COMPUTER_USE_DEMO = CLAUDE_DC_ROOT / "computeruse" / "computer_use_demo"

# Check if directories exist
print("Checking directories:")
for dirname, path in [
    ("Repository root", REPO_ROOT),
    ("Claude DC root", CLAUDE_DC_ROOT),
    ("Computer use demo dir", COMPUTER_USE_DEMO),
]:
    if path.exists():
        print(f"✅ {{dirname}} exists: {{path}}")
    else:
        print(f"❌ {{dirname}} NOT FOUND: {{path}}")

# Test Python module paths
print("\\nChecking Python import paths:")
paths_to_check = [
    str(REPO_ROOT),
    str(CLAUDE_DC_ROOT),
    str(CLAUDE_DC_ROOT / "computeruse"),
    str(COMPUTER_USE_DEMO),
]

# Show current sys.path
print("Current sys.path:")
for i, path in enumerate(sys.path):
    print(f"  {{i}}: {{path}}")

# Check if paths are in sys.path
for path in paths_to_check:
    if path in sys.path:
        print(f"✅ Path already in sys.path: {{path}}")
    else:
        print(f"⚠️ Path NOT in sys.path: {{path}}")

# Check PYTHONPATH
pythonpath = os.environ.get("PYTHONPATH", "")
print(f"\\nCurrent PYTHONPATH: {{pythonpath}}")

# Simulate what the launch script would do
new_pythonpath = os.pathsep.join([pythonpath] + paths_to_check)
print(f"Simulated PYTHONPATH would be: {{new_pythonpath}}")

# Try importing after setting path
os.environ["PYTHONPATH"] = new_pythonpath
sys.path = paths_to_check + sys.path  # Add to front of path

print("\\nTrying to import computer_use_demo after path changes:")
try:
    import computer_use_demo
    print(f"✅ Successfully imported computer_use_demo")
    print(f"  Module location: {{computer_use_demo.__file__}}")
except ImportError as e:
    print(f"❌ Failed to import computer_use_demo: {{e}}")

# Try importing tools directly
print("\\nTrying to import tools module:")
try:
    from computer_use_demo import tools
    print(f"✅ Successfully imported tools module")
    print(f"  Module location: {{tools.__file__}}")
except ImportError as e:
    print(f"❌ Failed to import tools module: {{e}}")
            ''')
            
        # Make it executable
        os.chmod(test_script, 0o755)
        
        # Run the script to test paths
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            check=False,
            text=True
        )
        
        # Print output
        print(result.stdout.strip())
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
            
        # Check for success/failure indicators
        success = (
            "✅ Successfully imported computer_use_demo" in result.stdout and
            "Failed to import" not in result.stdout
        )
        
        if success:
            print("\n✅ Environment paths and imports working correctly")
        else:
            print("\n❌ Environment path validation failed")
            
        return success
    except Exception as e:
        print(f"❌ Failed to create or run path test: {e}")
        return False
    finally:
        # Clean up
        if test_script.exists():
            os.unlink(test_script)


def main():
    """Run all validation checks"""
    print("\nClaude DC Phase 2 Enhancements Validation")
    print("=========================================")
    
    # Run all checks
    imports_ok = check_imports()
    api_ok = check_api_functionality()
    streaming_ok = check_streaming_support()
    caching_ok = check_prompt_caching()
    extended_output_ok = check_extended_output()
    tool_streaming_ok = check_real_time_tool_output()
    
    # Adding runtime validation checks
    runtime_imports_ok = check_runtime_imports()
    environment_paths_ok = check_environment_paths()
    
    # Print summary
    print_section("Validation Summary")
    all_checks = [
        ("Module Imports (Static)", imports_ok),
        ("Module Imports (Runtime)", runtime_imports_ok),
        ("Environment Paths", environment_paths_ok),
        ("Anthropic API", api_ok),
        ("Streaming Responses", streaming_ok),
        ("Prompt Caching", caching_ok),
        ("128K Extended Output", extended_output_ok),
        ("Real-Time Tool Output", tool_streaming_ok)
    ]
    
    for name, result in all_checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    # Final result
    if all(result for _, result in all_checks):
        print("\n✅ All checks passed! Claude DC Phase 2 enhancements are properly configured.")
        print("You can now run Claude DC with: ./claude_dc_launch.sh")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues before running Claude DC.")
        print("  Try running the tests one by one to identify the specific issue.")
        return 1

def run_runtime_imports_only():
    """Run only the runtime imports validation"""
    print("\nClaude DC Runtime Import Validation")
    print("==================================")
    
    runtime_imports_ok = check_runtime_imports()
    environment_paths_ok = check_environment_paths()
    
    print_section("Validation Summary")
    all_checks = [
        ("Module Imports (Runtime)", runtime_imports_ok),
        ("Environment Paths", environment_paths_ok),
    ]
    
    for name, result in all_checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    # Final result
    if all(result for _, result in all_checks):
        print("\n✅ Runtime import validation passed!")
        return 0
    else:
        print("\n❌ Runtime import validation failed.")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--runtime-imports-only":
        sys.exit(run_runtime_imports_only())
    else:
        sys.exit(main())