"""
Verify Python syntax for files without executing them
"""
import sys
import py_compile

def verify_syntax(file_path):
    """Verify Python syntax without executing the file"""
    print(f"Verifying syntax of {file_path}...")
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"✅ {file_path} syntax is valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in {file_path}:")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}:")
        print(f"   {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_syntax.py [file_path1] [file_path2] ...")
        sys.exit(1)
    
    success = True
    for file_path in sys.argv[1:]:
        if not verify_syntax(file_path):
            success = False
    
    if success:
        print("\n✅ All files passed syntax check")
    else:
        print("\n❌ Some files have syntax errors")
        sys.exit(1)