"""
Safe file operations module - simplified version without subprocess patching.
"""

import logging
from computer_use_demo.token_manager import token_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/safe_file_operations.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('safe_file_operations')

def safe_read_file(path, encoding='utf-8', errors=None):
    """
    Safe wrapper to read file content with token management.
    """
    try:
        from pathlib import Path
        path_obj = Path(path)
        
        if not path_obj.exists():
            return f"Error: File {path} does not exist"
        
        # Estimate tokens
        file_size = path_obj.stat().st_size
        estimated_tokens = token_manager.estimate_tokens('x' * file_size)
        
        # Apply token rate limiting
        token_manager.delay_if_needed(estimated_tokens)
        
        # Read the file
        content = path_obj.read_text(encoding=encoding, errors=errors)
        return content
    
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return f"Error reading file: {e}"

def safe_cat(path):
    """
    A simple 'cat' like utility that respects token limits.
    """
    return safe_read_file(path)

# Export the interceptor for compatibility, but make it a no-op
class DummyInterceptor:
    def get_file_metadata(self, path):
        from pathlib import Path
        path_obj = Path(path)
        if not path_obj.exists():
            return {"exists": False, "error": "File does not exist"}
        
        file_size = path_obj.stat().st_size
        return {
            "exists": True,
            "size_bytes": file_size,
            "estimated_tokens": token_manager.estimate_tokens('x' * file_size)
        }
    
    def get_next_chunk(self, path):
        return safe_read_file(path)

interceptor = DummyInterceptor()
