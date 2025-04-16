"""
Safe file operations module that respects token limits.
"""

import logging
import time
import builtins
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any
import threading
import queue
from datetime import datetime
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

# Original open function
original_open = builtins.open
# Original Path.read_text method
original_path_read_text = Path.read_text

# Constants
MAX_TOKENS_PER_CHUNK = 10000  # Maximum tokens per chunk
MAX_RETRIES = 3  # Maximum retry attempts for file operations
RETRY_DELAY = 2  # Base delay for retries (in seconds)

class OperationQueue:
    """Queue for file operations to manage token throughput."""
    
    def __init__(self):
        self._queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        self._completed_ops = 0
        self._enqueued_ops = 0
        self._created_chunks = 0
    
    def enqueue(self, operation):
        """Add an operation to the queue."""
        self._enqueued_ops += 1
        self._queue.put(operation)
    
    def _process_queue(self):
        """Worker thread that processes operations in the queue."""
        while True:
            try:
                operation = self._queue.get()
                
                if operation['type'] == 'open':
                    self._process_open_operation(operation)
                elif operation['type'] == 'path_read_text':
                    self._process_read_text_operation(operation)
                
                self._queue.task_done()
                self._completed_ops += 1
                
            except Exception as e:
                logger.error(f"Error processing queue operation: {e}")
    
    def _process_open_operation(self, operation):
        """Process a file open operation from the queue."""
        path = operation['path']
        mode = operation['mode']
        args = operation['args']
        kwargs = operation['kwargs']
        callback = operation.get('callback')
        estimated_tokens = operation.get('estimated_tokens', 0)
        
        # Apply token rate limiting
        token_manager.delay_if_needed(estimated_tokens)
        
        try:
            # Use the original open function
            with original_open(path, mode, *args, **kwargs) as f:
                content = f.read()
                
            # Track token usage
            actual_tokens = token_manager.estimate_tokens(content)
            
            # If callback is provided, call it with the result
            if callback:
                callback(content)
        except Exception as e:
            logger.error(f"Error in open operation for {path}: {e}")
            if callback:
                callback(None, error=str(e))
    
    def _process_read_text_operation(self, operation):
        """Process a Path.read_text operation from the queue."""
        path = operation['path']
        encoding = operation.get('encoding', 'utf-8')
        errors = operation.get('errors', None)
        callback = operation.get('callback')
        estimated_tokens = operation.get('estimated_tokens', 0)
        
        # Apply token rate limiting
        token_manager.delay_if_needed(estimated_tokens)
        
        try:
            # Use the original read_text function
            if errors:
                content = original_path_read_text(path, encoding=encoding, errors=errors)
            else:
                content = original_path_read_text(path, encoding=encoding)
            
            # Track token usage
            actual_tokens = token_manager.estimate_tokens(content)
            
            # If callback is provided, call it with the result
            if callback:
                callback(content)
        except Exception as e:
            logger.error(f"Error in read_text operation for {path}: {e}")
            if callback:
                callback(None, error=str(e))
    
    def get_stats(self):
        """Get statistics about the operation queue."""
        return {
            'enqueued_operations': self._enqueued_ops,
            'completed_operations': self._completed_ops,
            'queue_size': self._queue.qsize(),
            'chunks_created': self._created_chunks,
        }

# Queue instance
operation_queue = OperationQueue()

class SubprocessWrapper:
    """Wrapper for subprocess to manage token usage from command outputs."""
    
    def __init__(self, token_manager):
        self.token_manager = token_manager
        self.output_cache = {}
        self.CHUNK_SIZE = 10000  # Token chunk size for large outputs
    
    def run(self, cmd, *args, **kwargs):
        """Intercept subprocess.run to manage token usage."""
        import subprocess
        
        original_run = subprocess.run
        result = original_run(cmd, *args, **kwargs)
        
        # If there's stdout/stderr content, estimate tokens and apply delays
        if hasattr(result, 'stdout') and result.stdout:
            if isinstance(result.stdout, bytes):
                # Try to decode bytes to get estimated token count
                try:
                    stdout_str = result.stdout.decode('utf-8')
                    stdout_tokens = self.token_manager.estimate_tokens(stdout_str)
                    if stdout_tokens > self.CHUNK_SIZE:
                        # Store in cache for potential chunking
                        import hashlib
                        cmd_hash = hashlib.md5(str(cmd).encode()).hexdigest()
                        self.output_cache[cmd_hash] = {
                            'content': stdout_str,
                            'chunks': self._chunk_text(stdout_str),
                            'current_chunk': 0
                        }
                        # Replace stdout with first chunk and notification
                        first_chunk = self.output_cache[cmd_hash]['chunks'][0]
                        warning = f"\n\n[Output truncated due to size. {len(self.output_cache[cmd_hash]['chunks'])} chunks total. Use 'cat_more' to see more.]"
                        result.stdout = (first_chunk + warning).encode('utf-8')
                    else:
                        # Apply delay based on token usage
                        self.token_manager.delay_if_needed(stdout_tokens)
                except UnicodeDecodeError:
                    # If we can't decode, it's binary data - let it pass through
                    pass
        
        return result
    
    def _chunk_text(self, text):
        """Split large text into chunks based on token count."""
        chunks = []
        lines = text.splitlines(True)
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.token_manager.estimate_tokens(line)
            if current_tokens + line_tokens > self.CHUNK_SIZE:
                chunks.append(''.join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        return chunks
    
    def get_next_chunk(self, cmd_hash):
        """Get the next chunk of output for a previously chunked command."""
        if cmd_hash not in self.output_cache:
            return "No cached output found for this command."
        
        cache_entry = self.output_cache[cmd_hash]
        current_index = cache_entry['current_chunk']
        
        if current_index >= len(cache_entry['chunks']):
            return "End of output reached."
        
        chunk = cache_entry['chunks'][current_index]
        cache_entry['current_chunk'] = current_index + 1
        
        # Add status info
        chunk_info = f"[Chunk {current_index + 1}/{len(cache_entry['chunks'])}]"
        if current_index + 1 < len(cache_entry['chunks']):
            chunk_info += " Use 'cat_more' to see next chunk."
        else:
            chunk_info += " End of output."
        
        return f"{chunk_info}\n\n{chunk}"

class ToolInterceptor:
    """Intercepts file operations and ensures they respect token limits."""
    
    def __init__(self):
        self.file_chunks = {}  # Stores chunked file contents
        self.current_chunk_index = {}  # Tracks current chunk for each file
    
    def intercept_open(self, path, mode='r', *args, **kwargs):
        """Intercept file open operations to manage token usage."""
        # Only intercept read operations in text mode
        if 'b' in mode or 'w' in mode or 'a' in mode:
            # Pass binary and write operations through
            return original_open(path, mode, *args, **kwargs)
        
        # For read operations, estimate token count
        try:
            # Get file size to estimate tokens
            path_obj = Path(path)
            if not path_obj.exists():
                # If file doesn't exist, let the original open handle the error
                return original_open(path, mode, *args, **kwargs)
            
            file_size = path_obj.stat().st_size
            # Rough estimate: 1 token ≈ 4 chars
            estimated_tokens = token_manager.estimate_tokens('x' * file_size)
            
            if estimated_tokens > MAX_TOKENS_PER_CHUNK:
                logger.warning(f"⚠️ File is large (~{estimated_tokens} tokens). Reading in chunks of max {MAX_TOKENS_PER_CHUNK} tokens...")
                
                # For large files, we'll read in chunks
                return self.read_large_file(path, mode, *args, **kwargs)
            else:
                # For smaller files, enqueue the operation
                result_queue = queue.Queue()
                
                def callback(content, error=None):
                    if error:
                        result_queue.put(('error', error))
                    else:
                        result_queue.put(('content', content))
                
                operation_queue.enqueue({
                    'type': 'open',
                    'path': path,
                    'mode': mode,
                    'args': args,
                    'kwargs': kwargs,
                    'callback': callback,
                    'estimated_tokens': estimated_tokens,
                })
                
                # Wait for the result
                result_type, result = result_queue.get()
                if result_type == 'error':
                    raise IOError(f"Error reading file: {result}")
                
                # Create a file-like object
                import io
                return io.StringIO(result)
                
        except Exception as e:
            logger.error(f"Error intercepting open for {path}: {e}")
            # Fall back to original open
            return original_open(path, mode, *args, **kwargs)
    
    def read_large_file(self, path, mode='r', *args, **kwargs):
        """Handle reading large files in chunks."""
        path_str = str(path)
        
        # Check if we already have chunks for this file
        if path_str in self.file_chunks:
            chunks = self.file_chunks[path_str]
            
            # Reset to first chunk if requested
            if path_str not in self.current_chunk_index:
                self.current_chunk_index[path_str] = 0
            
            # Get the current chunk
            current_index = self.current_chunk_index[path_str]
            chunk = chunks[current_index]
            
            # Update index for next time
            self.current_chunk_index[path_str] = (current_index + 1) % len(chunks)
            
            # Create a file-like object with the chunk
            import io
            
            # Add a note about chunking if there are more chunks
            if len(chunks) > 1:
                if current_index < len(chunks) - 1:
                    chunk += "\n\n[More content available. Use safe_cat for next chunk]"
                else:
                    chunk += "\n\n[End of file reached]"
            
            return io.StringIO(chunk)
        
        # If we don't have chunks yet, read the file in chunks
        try:
            chunks = []
            current_chunk = []
            current_chunk_tokens = 0
            
            with original_open(path, mode, *args, **kwargs) as f:
                for line in f:
                    line_tokens = token_manager.estimate_tokens(line)
                    
                    # If adding this line would exceed the chunk limit, start a new chunk
                    if current_chunk_tokens + line_tokens > MAX_TOKENS_PER_CHUNK:
                        chunks.append(''.join(current_chunk))
                        current_chunk = [line]
                        current_chunk_tokens = line_tokens
                    else:
                        current_chunk.append(line)
                        current_chunk_tokens += line_tokens
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(''.join(current_chunk))
            
            # Store the chunks for later access
            self.file_chunks[path_str] = chunks
            self.current_chunk_index[path_str] = 0
            
            # Return the first chunk
            import io
            first_chunk = chunks[0]
            
            # Add a note about chunking if there are more chunks
            if len(chunks) > 1:
                first_chunk += "\n\n[More content available. Use safe_cat for next chunk]"
            
            return io.StringIO(first_chunk)
            
        except Exception as e:
            logger.error(f"Error reading large file {path}: {e}")
            # Fall back to original open
            return original_open(path, mode, *args, **kwargs)
    
    def intercept_path_read_text(self, path_obj, encoding='utf-8', errors=None):
        """Intercept Path.read_text to manage token usage."""
        try:
            # Get file size to estimate tokens
            if not path_obj.exists():
                # If file doesn't exist, let the original method handle the error
                return original_path_read_text(path_obj, encoding=encoding, errors=errors)
            
            file_size = path_obj.stat().st_size
            # Rough estimate: 1 token ≈ 4 chars
            estimated_tokens = token_manager.estimate_tokens('x' * file_size)
            
            if estimated_tokens > MAX_TOKENS_PER_CHUNK:
                logger.warning(f"⚠️ File is large (~{estimated_tokens} tokens). Reading in chunks of max {MAX_TOKENS_PER_CHUNK} tokens...")
                
                # For large files, read and chunk the content
                path_str = str(path_obj)
                
                # Check if we already have chunks for this file
                if path_str in self.file_chunks:
                    chunks = self.file_chunks[path_str]
                    
                    # Reset to first chunk if requested
                    if path_str not in self.current_chunk_index:
                        self.current_chunk_index[path_str] = 0
                    
                    # Get the current chunk
                    current_index = self.current_chunk_index[path_str]
                    chunk = chunks[current_index]
                    
                    # Update index for next time
                    self.current_chunk_index[path_str] = (current_index + 1) % len(chunks)
                    
                    # Add a note about chunking if there are more chunks
                    if len(chunks) > 1:
                        if current_index < len(chunks) - 1:
                            chunk += "\n\n[More content available. Use safe_cat for next chunk]"
                        else:
                            chunk += "\n\n[End of file reached]"
                    
                    return chunk
                
                # If we don't have chunks yet, read and chunk the file
                try:
                    chunks = []
                    current_chunk = []
                    current_chunk_tokens = 0
                    
                    # Read the file using the original method to get all content
                    if errors:
                        content = original_path_read_text(path_obj, encoding=encoding, errors=errors)
                    else:
                        content = original_path_read_text(path_obj, encoding=encoding)
                    
                    # Split into lines and chunk
                    for line in content.splitlines(True):  # Keep line endings
                        line_tokens = token_manager.estimate_tokens(line)
                        
                        # If adding this line would exceed the chunk limit, start a new chunk
                        if current_chunk_tokens + line_tokens > MAX_TOKENS_PER_CHUNK:
                            chunks.append(''.join(current_chunk))
                            current_chunk = [line]
                            current_chunk_tokens = line_tokens
                        else:
                            current_chunk.append(line)
                            current_chunk_tokens += line_tokens
                    
                    # Add the last chunk if it's not empty
                    if current_chunk:
                        chunks.append(''.join(current_chunk))
                    
                    # Store the chunks for later access
                    self.file_chunks[path_str] = chunks
                    self.current_chunk_index[path_str] = 1  # Set to 1 because we're returning chunk 0
                    
                    # Return the first chunk
                    first_chunk = chunks[0]
                    
                    # Add a note about chunking if there are more chunks
                    if len(chunks) > 1:
                        first_chunk += "\n\n[More content available. Use safe_cat for next chunk]"
                    
                    return first_chunk
                    
                except Exception as e:
                    logger.error(f"Error reading large file {path_obj}: {e}")
                    # Fall back to original method
                    return original_path_read_text(path_obj, encoding=encoding, errors=errors)
            
            # For smaller files, enqueue the operation
            result_queue = queue.Queue()
            
            def callback(content, error=None):
                if error:
                    result_queue.put(('error', error))
                else:
                    result_queue.put(('content', content))
            
            operation_queue.enqueue({
                'type': 'path_read_text',
                'path': path_obj,
                'encoding': encoding,
                'errors': errors,
                'callback': callback,
                'estimated_tokens': estimated_tokens,
            })
            
            # Wait for the result
            result_type, result = result_queue.get()
            if result_type == 'error':
                raise IOError(f"Error reading file: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error intercepting read_text for {path_obj}: {e}")
            # Fall back to original method
            return original_path_read_text(path_obj, encoding=encoding, errors=errors)
    
    def intercept_path_read_bytes(self, path_obj):
        """
        Pass-through for read_bytes calls.
        This could be enhanced to manage binary data if needed.
        """
        return Path.read_bytes(path_obj)
    
    def get_next_chunk(self, path):
        """Get the next chunk of a file that was previously chunked."""
        path_str = str(path)
        
        if path_str not in self.file_chunks:
            raise ValueError(f"No chunked content available for {path}")
        
        chunks = self.file_chunks[path_str]
        
        if path_str not in self.current_chunk_index:
            self.current_chunk_index[path_str] = 0
        
        current_index = self.current_chunk_index[path_str]
        chunk = chunks[current_index]
        
        # Update index for next time
        self.current_chunk_index[path_str] = (current_index + 1) % len(chunks)
        
        # Add a note about chunking if there are more chunks
        if len(chunks) > 1:
            if current_index < len(chunks) - 1:
                chunk += "\n\n[More content available. Use safe_cat for next chunk]"
            else:
                chunk += "\n\n[End of file reached]"
        
        return chunk
    
    def get_file_metadata(self, path):
        """Get metadata about a file, including chunking information."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return {"exists": False, "error": "File does not exist"}
            
            stats = path_obj.stat()
            size_bytes = stats.st_size
            estimated_tokens = token_manager.estimate_tokens('x' * size_bytes)
            
            metadata = {
                "exists": True,
                "size_bytes": size_bytes,
                "estimated_tokens": estimated_tokens,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "chunked": str(path) in self.file_chunks,
            }
            
            if str(path) in self.file_chunks:
                metadata["chunks"] = len(self.file_chunks[str(path)])
                metadata["current_chunk"] = self.current_chunk_index.get(str(path), 0)
            
            if estimated_tokens > MAX_TOKENS_PER_CHUNK:
                metadata["warning"] = f"File exceeds token limits. Will be chunked into ~{(estimated_tokens // MAX_TOKENS_PER_CHUNK) + 1} parts."
            
            return metadata
        except Exception as e:
            return {"exists": False, "error": str(e)}

# Create singleton instance
interceptor = ToolInterceptor()

def safe_read_file(path, encoding='utf-8', errors=None, retry_count=0):
    """
    Safe wrapper to read file content with proper token management.
    Handles retries and chunking for large files.
    """
    try:
        path_obj = Path(path)
        
        # Get file metadata to check size
        metadata = interceptor.get_file_metadata(path)
        
        if not metadata["exists"]:
            return f"Error: {metadata.get('error', 'File does not exist')}"
        
        if metadata.get("chunked", False):
            # File is already chunked, get current chunk
            return interceptor.get_next_chunk(path)
        
        # Use intercepted read_text method
        return interceptor.intercept_path_read_text(path_obj, encoding, errors)
    
    except Exception as e:
        if retry_count < MAX_RETRIES:
            logger.warning(f"Error reading {path}, retrying ({retry_count+1}/{MAX_RETRIES}): {e}")
            # Exponential backoff
            time.sleep(RETRY_DELAY * (2**retry_count))
            return safe_read_file(path, encoding, errors, retry_count + 1)
        else:
            logger.error(f"Failed to read {path} after {MAX_RETRIES} attempts: {e}")
            return f"Error reading file after {MAX_RETRIES} retries: {e}"

def safe_cat(path):
    """
    A 'cat' like utility that respects token limits.
    If file was previously chunked, gets the next chunk.
    """
    try:
        # Check if file exists
        path_obj = Path(path)
        if not path_obj.exists():
            return f"Error: File {path} does not exist"
        
        # Get file metadata
        metadata = interceptor.get_file_metadata(path)
        
        if metadata.get("chunked", False):
            # File is already chunked, get next chunk
            content = interceptor.get_next_chunk(path)
            current_chunk = metadata.get("current_chunk", 0)
            total_chunks = metadata.get("chunks", 0)
            
            return f"[Chunk {current_chunk}/{total_chunks} of {path}]\n\n{content}"
        else:
            # File is not chunked yet, read it safely
            content = safe_read_file(path)
            return content
    
    except Exception as e:
        logger.error(f"Error in safe_cat for {path}: {e}")
        return f"Error: {e}"

def monkey_patch_all():
    """Apply all monkey patches to intercept file operations."""
    # Import modules needed for patching
    import builtins
    from pathlib import Path
    import subprocess
    
    # Patch builtins.open
    builtins.open = interceptor.intercept_open
    logger.info("Patched builtins.open")
    
    # Patch Path.read_text - create a wrapper that properly calls the instance method
    original_path_read_text = Path.read_text
    
    def path_read_text_wrapper(path_obj, encoding='utf-8', errors=None):
        return interceptor.intercept_path_read_text(path_obj, encoding, errors)
    
    Path.read_text = path_read_text_wrapper
    logger.info("Patched Path.read_text")
    
    # Patch Path.read_bytes
    original_path_read_bytes = Path.read_bytes
    
    def path_read_bytes_wrapper(path_obj):
        return interceptor.intercept_path_read_bytes(path_obj)
    
    Path.read_bytes = path_read_bytes_wrapper
    logger.info("Patched Path.read_bytes")
    
    # Patch other tools as needed
    try:
        from computer_use_demo.tools.edit import EditTool20250124
        
        # Save original method
        original_read_file = EditTool20250124.read_file
        
        # Define replacement method that uses our interceptor
        def safe_read_file_for_edit(self, path):
            return interceptor.intercept_path_read_text(Path(path))
        
        # Patch the method
        EditTool20250124.interceptor = interceptor
        EditTool20250124.read_file = safe_read_file_for_edit
        logger.info("Patched EditTool20250124.read_file")
    except ImportError:
        logger.warning("Could not patch EditTool20250124.read_file - module not found")
    
    logger.info("All file operation patches applied successfully")
    
    # Patch subprocess.run
    import subprocess
    original_run = subprocess.run
    subprocess_wrapper = SubprocessWrapper(token_manager)
    
    def wrapped_run(*args, **kwargs):
        return subprocess_wrapper.run(*args, **kwargs)
    
    subprocess.run = wrapped_run
    logger.info("Patched subprocess.run")
    
    # Add a method to get the next chunk from bash output
    def cat_more(cmd_hash):
        """Get the next chunk of output for a command."""
        return subprocess_wrapper.get_next_chunk(cmd_hash)
    
    # Make cat_more available globally
    import builtins
    builtins.cat_more = cat_more
    
    # Patch bash execution for BashTool
    try:
        from computer_use_demo.tools.bash import BashTool20250124
        
        # Save original method
        original_bash_execute = BashTool20250124._execute
        
        # Define replacement method
        def safe_bash_execute(self, *args, **kwargs):
            # Use the original method but capture the hash of the command
            result = original_bash_execute(self, *args, **kwargs)
            
            # If the output is large and likely chunked, add the hash reference
            if "Output truncated due to size" in result.output:
                import hashlib
                cmd_hash = hashlib.md5(str(args[0]).encode()).hexdigest()
                result.output += f"\n\nUse cat_more('{cmd_hash}') to see the next chunk."
            
            return result
        
        # Patch the method
        BashTool20250124._execute = safe_bash_execute
        logger.info("Patched BashTool20250124._execute")
    except ImportError:
        logger.warning("Could not patch BashTool20250124._execute - module not found")
    
    # Add better handling for binary file operations
    original_path_read_bytes = Path.read_bytes
    
    def path_read_bytes_wrapper(path_obj):
        """
        Wrapper for Path.read_bytes that applies basic token tracking.
        For binary data, we estimate 1 token per 4 bytes as a rough approximation.
        """
        try:
            # Get file size to estimate binary size impact
            file_size = path_obj.stat().st_size
            
            # Very rough token estimate for binary data
            estimated_tokens = file_size // 4
            
            # Only apply delay for larger files
            if estimated_tokens > 1000:  # Arbitrary threshold for binary data
                token_manager.delay_if_needed(estimated_tokens // 2)  # Using half estimate for binary
                logger.info(f"Reading binary file {path_obj} (~{estimated_tokens} token equivalent)")
            
            # Call original method
            return original_path_read_bytes(path_obj)
        except Exception as e:
            logger.error(f"Error in read_bytes wrapper for {path_obj}: {e}")
            return original_path_read_bytes(path_obj)
    
    Path.read_bytes = path_read_bytes_wrapper
    logger.info("Enhanced patch for Path.read_bytes")

# Initialize patches
monkey_patch_all()
