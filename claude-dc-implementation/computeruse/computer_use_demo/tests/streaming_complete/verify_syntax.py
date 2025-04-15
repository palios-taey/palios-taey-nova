"""
Syntax verification for all Python files
"""
import sys
import os
import py_compile

def verify_file_syntax(file_path):
    """Verify the syntax of a Python file"""
    print(f"Checking syntax for: {file_path}")
    try:
        # Try to compile the file to check syntax
        py_compile.compile(file_path, doraise=True)
        print(f"✅ {file_path}: Syntax OK")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ {file_path}: Syntax ERROR")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Unexpected error")
        print(f"   Error: {e}")
        return False

def verify_all_python_files(directory):
    """Verify syntax for all Python files in a directory"""
    success = True
    
    # Check all .py files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not verify_file_syntax(file_path):
                    success = False
    
    return success

if __name__ == "__main__":
    print("Verifying syntax for all Python files...")
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    success = verify_all_python_files(directory)
    
    if success:
        print("\n✅ All files passed syntax verification")
    else:
        print("\n❌ Some files have syntax errors - MUST FIX BEFORE DEPLOYMENT")
        sys.exit(1)