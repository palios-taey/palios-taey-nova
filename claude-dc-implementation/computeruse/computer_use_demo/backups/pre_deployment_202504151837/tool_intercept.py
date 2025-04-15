"""
Universal Tool Interception Module

This module monkey-patches Python's built-in file operations and tool functions
to enforce rate limiting and chunking for ALL file operations.
"""

import os
import sys
import time
import builtins
import io
import logging
import threading
import asyncio
import inspect
import functools
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/tool_intercept.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tool_intercept")

# Add the computer_use_demo directory to the path
sys.path.append('/home/computeruse/computer_use_demo')

# Import token management - we'll use this for rate limiting
from token_management.token_manager import token_manager

# Try to import tiktoken for token estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    # Initialize tokenizer - this approximates Claude's tokenization
    ENCODING = tiktoken.get_encoding("cl100k_base")
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, falling back to character-based estimation")

# Save original functions before monkey-patching
original_open = builtins.open
original_path_read_text = Path.read_text
original_path_read_bytes = Path.read_bytes

class OperationQueue:
    """
    Queue for file operations that enforces rate limits and chunking
    """
    
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.queue_thread = None
        self.running = False
        self.max_chunk_tokens = 10000  # Conservative chunk size
        
        # Statistics
        self.operations_queued = 0
        self.operations_completed = 0
        self.chunks_created = 0
        
        logger.info("Operation queue initialized")
    
    def start(self):
        """Start the queue processor thread"""
        if self.queue_thread is None or not self.queue_thread.is_alive():
            self.running = True
            self.queue_thread = threading.Thread(target=self._process_queue)
            self.queue_thread.daemon = True
            self.queue_thread.start()
            logger.info("Queue processor thread started")
    
    def stop(self):
        """Stop the queue processor thread"""
        self.running = False
        if self.queue_thread and self.queue_thread.is_alive():
            self.queue_thread.join(timeout=5)
            logger.info("Queue processor thread stopped")
    
    def add_operation(self, func, args=None, kwargs=None, callback=None, 
                     estimated_tokens=None, operation_id=None):
        """
        Add an operation to the queue
        
        Args:
            func: Function to execute
            args: Arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            callback: Callback function to call with the result
            estimated_tokens: Estimated token cost of the operation
            operation_id: Optional ID for the operation
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        
        # If no token estimation provided, use a conservative default
        if estimated_tokens is None:
            estimated_tokens = 1000  # Default conservative estimate
        
        # Create operation object
        operation = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'callback': callback,
            'estimated_tokens': estimated_tokens,
            'operation_id': operation_id or f"op_{self.operations_queued}",
            'queued_at': time.time()
        }
        
        # Add to queue with lock to avoid race conditions
        with self.lock:
            self.queue.append(operation)
            self.operations_queued += 1
        
        # Log the operation
        logger.info(f"Queued operation {operation['operation_id']} with estimated {estimated_tokens} tokens")
        
        # Make sure the processor is running
        self.start()
        
        return operation['operation_id']
    
    def _process_queue(self):
        """Process operations in the queue"""
        while self.running:
            # Get the next operation if available
            operation = None
            with self.lock:
                if self.queue:
                    operation = self.queue[0]
            
            if operation:
                # Check if we have enough token budget for this operation
                stats = token_manager.get_stats()
                current_usage = stats.get('input_tokens_per_minute', 0)
                input_limit = stats.get('input_limit', 40000)
                
                # Calculate percentage of limit used
                if input_limit > 0:
                    percent_used = (current_usage / input_limit) * 100
                else:
                    percent_used = 0
                
                # If we're using less than 50% of our limit, we can proceed
                if percent_used < 50:
                    # Pop the operation from the queue with lock
                    with self.lock:
                        operation = self.queue.pop(0)
                    
                    # Execute the operation
                    try:
                        logger.info(f"Executing operation {operation['operation_id']} (queued for {time.time() - operation['queued_at']:.2f}s)")
                        
                        # Delay briefly to avoid burst operations
                        time.sleep(0.1)
                        
                        # Execute the function
                        result = operation['func'](*operation['args'], **operation['kwargs'])
                        
                        # Record token usage
                        token_manager.track_usage(operation['estimated_tokens'], 0)
                        
                        # Call the callback if provided
                        if operation['callback']:
                            operation['callback'](result, None)
                        
                        # Update statistics
                        with self.lock:
                            self.operations_completed += 1
                        
                        logger.info(f"Completed operation {operation['operation_id']}")
                    except Exception as e:
                        logger.error(f"Error executing operation {operation['operation_id']}: {e}")
                        
                        # Call the callback with the error if provided
                        if operation['callback']:
                            operation['callback'](None, e)
                else:
                    # Not enough token budget, wait a bit
                    logger.info(f"Waiting for token budget to refresh (currently at {percent_used:.1f}% of limit)")
                    time.sleep(1)
            else:
                # No operations, wait a bit
                time.sleep(0.1)
    
    def get_stats(self):
        """Get queue statistics"""
        with self.lock:
            return {
                'operations_queued': self.operations_queued,
                'operations_completed': self.operations_completed,
                'queue_length': len(self.queue),
                'chunks_created': self.chunks_created
            }

class ToolInterceptor:
    """
    Universal interceptor for all file operations
    """
    
    def __init__(self):
        # Create the operation queue
        self.operation_queue = OperationQueue()
        self.operation_queue.start()
        
        # Token estimation settings
        self.chars_per_token = 3.5  # Conservative estimate
        
        # Chunking settings
        self.max_chunk_tokens = 10000  # Conservative chunk size
        self.max_chunk_chars = int(self.max_chunk_tokens * self.chars_per_token)
        
        # File chunk tracking
        self.file_chunks = {}  # file_path -> [chunks]
        self.file_callback_chain = {}  # file_path -> callback chain
        
        logger.info("Tool interceptor initialized")
        logger.info(f"Max chunk size: {self.max_chunk_tokens} tokens (~{self.max_chunk_chars} chars)")
    
    def estimate_tokens(self, text):
        """
        Estimate the number of tokens in a text
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        if TIKTOKEN_AVAILABLE:
            try:
                # Use tiktoken for accurate estimation
                return len(ENCODING.encode(text))
            except Exception as e:
                logger.warning(f"Error estimating tokens with tiktoken: {e}")
        
        # Fall back to character-based estimation
        return int(len(text) / self.chars_per_token)
    
    def intercept_open(self, file, mode='r', *args, **kwargs):
        """
        Intercept the built-in open function
        
        This allows us to monitor and control all file opens
        """
        # Only intercept files opened for reading in text mode
        if 'r' in mode and 'b' not in mode:
            logger.info(f"Intercepted open call for {file} in mode {mode}")
            
            # Create a proxied file object
            return self._create_proxied_file(file, mode, *args, **kwargs)
        
        # For other modes (writing, binary), pass through to the original
        return original_open(file, mode, *args, **kwargs)
    
    def _create_proxied_file(self, file, mode='r', *args, **kwargs):
        """
        Create a proxied file object that chunks content when read
        """
        # Open the actual file
        real_file = original_open(file, mode, *args, **kwargs)
        
        # Create a proxy object
        class ProxiedFile(io.TextIOBase):
            def __init__(self, real_file, tool_interceptor):
                self.real_file = real_file
                self.interceptor = tool_interceptor
                self.file_path = str(file)
                self.position = 0
                self.content_chunks = []
                self.current_chunk_index = 0
                
                # Get file size for estimation
                try:
                    self.file_size = os.path.getsize(self.file_path)
                except:
                    self.file_size = 0
                
                logger.info(f"Created proxied file for {self.file_path} (size: {self.file_size} bytes)")
            
            def read(self, size=-1):
                # If reading whole file or large chunk, we need to be careful
                if size < 0 or size > self.interceptor.max_chunk_chars:
                    logger.info(f"Large read requested ({size if size > 0 else 'all'} chars) for {self.file_path}")
                    
                    # Estimate the tokens in the entire file
                    if self.file_size > 0:
                        estimated_tokens = int(self.file_size / self.interceptor.chars_per_token)
                    else:
                        estimated_tokens = 10000  # Conservative default
                    
                    # If it's a large file, we need to chunk it
                    if estimated_tokens > self.interceptor.max_chunk_tokens:
                        logger.info(f"File is large (~{estimated_tokens} tokens), chunking...")
                        
                        # Check if we already have chunks for this file
                        if self.file_path in self.interceptor.file_chunks:
                            chunks = self.interceptor.file_chunks[self.file_path]
                        else:
                            # Read the file in chunks
                            chunks = self._read_in_chunks()
                            self.interceptor.file_chunks[self.file_path] = chunks
                        
                        # Return the first chunk and note that there's more
                        if chunks:
                            first_chunk = chunks[0]
                            self.current_chunk_index = 1
                            
                            # Add a note about chunking
                            if len(chunks) > 1:
                                chunk_note = f"\n\n[Note: This file is large and has been chunked. This is chunk 1 of {len(chunks)}. Use the safe_cat function to view the next chunk.]\n"
                                return first_chunk + chunk_note
                            else:
                                return first_chunk
                        else:
                            return ""
                    else:
                        # Small enough to read directly, but still queue the operation
                        return self._read_full_safe()
                else:
                    # Small read, can use original behavior
                    return self.real_file.read(size)
            
            def _read_in_chunks(self):
                """Read the file in chunks to avoid rate limit issues"""
                chunks = []
                self.real_file.seek(0)
                current_chunk = ""
                current_chunk_tokens = 0
                
                # Read line by line
                for line in self.real_file:
                    line_tokens = self.interceptor.estimate_tokens(line)
                    
                    # If adding this line would exceed the chunk size, start a new chunk
                    if current_chunk_tokens + line_tokens > self.interceptor.max_chunk_tokens:
                        chunks.append(current_chunk)
                        current_chunk = line
                        current_chunk_tokens = line_tokens
                    else:
                        current_chunk += line
                        current_chunk_tokens += line_tokens
                
                # Add the final chunk if there's anything left
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Update statistics
                with self.interceptor.operation_queue.lock:
                    self.interceptor.operation_queue.chunks_created += len(chunks)
                
                logger.info(f"Split {self.file_path} into {len(chunks)} chunks")
                return chunks
            
            def _read_full_safe(self):
                """Read the entire file safely through the operation queue"""
                result = [None]
                event = threading.Event()
                
                def callback(content, error):
                    if error:
                        logger.error(f"Error reading {self.file_path}: {error}")
                        result[0] = ""
                    else:
                        result[0] = content
                    event.set()
                
                # Queue the operation
                self.interceptor.operation_queue.add_operation(
                    self.real_file.read,
                    estimated_tokens=int(self.file_size / self.interceptor.chars_per_token),
                    callback=callback
                )
                
                # Wait for the operation to complete
                event.wait()
                return result[0]
            
            def readlines(self):
                """Read all lines from the file"""
                content = self.read()
                if content:
                    return content.splitlines(True)
                return []
            
            def readline(self, size=-1):
                """Read a single line from the file"""
                # If we're reading through chunks, return the next line from the current chunk
                if self.file_path in self.interceptor.file_chunks:
                    chunks = self.interceptor.file_chunks[self.file_path]
                    if self.current_chunk_index < len(chunks):
                        lines = chunks[self.current_chunk_index].splitlines(True)
                        if lines:
                            line = lines[0]
                            chunks[self.current_chunk_index] = ''.join(lines[1:])
                            if not chunks[self.current_chunk_index]:
                                self.current_chunk_index += 1
                            return line
                        else:
                            self.current_chunk_index += 1
                            return self.readline(size)
                    elif self.current_chunk_index == len(chunks):
                        # End of file
                        return ""
                
                # Otherwise, use the real file
                return self.real_file.readline(size)
            
            def close(self):
                """Close the underlying file"""
                self.real_file.close()
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()
        
        return ProxiedFile(real_file, self)
    
    def intercept_path_read_text(self, path_obj, encoding=None, errors=None):
        """
        Intercept Path.read_text calls
        
        This is used by many tools to read files
        """
        logger.info(f"Intercepted Path.read_text call for {path_obj}")
        
        # Convert Path object to string
        path_str = str(path_obj)
        
        # Get file size for token estimation
        try:
            file_size = os.path.getsize(path_str)
            estimated_tokens = int(file_size / self.chars_per_token)
        except:
            estimated_tokens = 10000  # Conservative default
        
        # For large files, use chunking
        if estimated_tokens > self.max_chunk_tokens:
            logger.info(f"File is large (~{estimated_tokens} tokens), chunking...")
            
            # Check if we already have chunks for this file
            if path_str in self.file_chunks:
                chunks = self.file_chunks[path_str]
                
                # Return the first chunk with a note about chunking
                if chunks:
                    first_chunk = chunks[0]
                    if len(chunks) > 1:
                        chunk_note = f"\n\n[Note: This file is large and has been chunked. This is chunk 1 of {len(chunks)}. Use the safe_cat function to view the next chunk.]\n"
                        return first_chunk + chunk_note
                    else:
                        return first_chunk
                else:
                    return ""
            
            # Read the file in chunks
            with original_open(path_str, 'r', encoding=encoding, errors=errors) as f:
                chunks = []
                current_chunk = ""
                current_chunk_tokens = 0
                
                # Read line by line
                for line in f:
                    line_tokens = self.estimate_tokens(line)
                    
                    # If adding this line would exceed the chunk size, start a new chunk
                    if current_chunk_tokens + line_tokens > self.max_chunk_tokens:
                        chunks.append(current_chunk)
                        current_chunk = line
                        current_chunk_tokens = line_tokens
                    else:
                        current_chunk += line
                        current_chunk_tokens += line_tokens
                
                # Add the final chunk if there's anything left
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Store the chunks for later
                self.file_chunks[path_str] = chunks
                
                # Update statistics
                with self.operation_queue.lock:
                    self.operation_queue.chunks_created += len(chunks)
                
                logger.info(f"Split {path_str} into {len(chunks)} chunks")
                
                # Return the first chunk with a note about chunking
                if chunks:
                    first_chunk = chunks[0]
                    if len(chunks) > 1:
                        chunk_note = f"\n\n[Note: This file is large and has been chunked. This is chunk 1 of {len(chunks)}. Use the safe_cat function to view the next chunk.]\n"
                        return first_chunk + chunk_note
                    else:
                        return first_chunk
                else:
                    return ""
        
        # For smaller files, queue the operation
        result = [None]
        event = threading.Event()
        
        def callback(content, error):
            if error:
                logger.error(f"Error reading {path_str}: {error}")
                result[0] = ""
            else:
                result[0] = content
            event.set()
        
        # Create a function that calls the original read_text
        def read_text_func():
            return original_path_read_text(path_obj, encoding, errors)
        
        # Queue the operation
        self.operation_queue.add_operation(
            read_text_func,
            estimated_tokens=estimated_tokens,
            callback=callback
        )
        
        # Wait for the operation to complete
        event.wait()
        return result[0]
    
    def intercept_path_read_bytes(self, path_obj):
        """
        Intercept Path.read_bytes calls
        
        Binary data is just passed through as it doesn't affect token usage as much
        """
        logger.info(f"Intercepted Path.read_bytes call for {path_obj}")
        return original_path_read_bytes(path_obj)
    
    def patch_tools(self):
        """
        Patch known tools to use safe file operations
        """
        from importlib import import_module
        
        # Try to patch known tools
        try:
            # Patch the edit tool
            edit_module = import_module('computer_use_demo.tools.edit')
            if hasattr(edit_module, 'EditTool20250124'):
                original_read_file = edit_module.EditTool20250124.read_file
                
                def safe_read_file(self, path):
                    logger.info(f"Intercepted EditTool.read_file call for {path}")
                    return self._interceptor.intercept_path_read_text(path, 'utf-8', 'ignore')
                
                # Add interceptor to the class
                edit_module.EditTool20250124._interceptor = self
                edit_module.EditTool20250124.read_file = safe_read_file
                logger.info("Patched EditTool20250124.read_file")
            
            # Patch other tools as needed
            # ...
            
            logger.info("Tool patching completed")
        except Exception as e:
            logger.error(f"Error patching tools: {e}")
    
    def monkey_patch_all(self):
        """
        Apply all monkey patches
        """
        logger.info("Applying monkey patches to intercept file operations")
        
        # Patch built-in open
        builtins.open = lambda file, mode='r', *args, **kwargs: self.intercept_open(file, mode, *args, **kwargs)
        logger.info("Patched builtins.open")
        
        # Patch Path.read_text
        Path.read_text = lambda self, encoding=None, errors=None: interceptor.intercept_path_read_text(self, encoding, errors)
        logger.info("Patched Path.read_text")
        
        # Patch Path.read_bytes
        Path.read_bytes = lambda self: interceptor.intercept_path_read_bytes(self)
        logger.info("Patched Path.read_bytes")
        
        # Patch specific tools
        self.patch_tools()
        
        logger.info("All monkey patches applied successfully")

# Create the interceptor
interceptor = ToolInterceptor()

# Export functions
def get_next_chunk(file_path):
    """
    Get the next chunk of a file that was previously chunked
    
    Args:
        file_path: Path to the file
        
    Returns:
        The next chunk of the file, or None if there are no more chunks
    """
    # Convert to string if it's a Path object
    if isinstance(file_path, Path):
        file_path = str(file_path)
    
    # Check if we have chunks for this file
    if file_path in interceptor.file_chunks:
        chunks = interceptor.file_chunks[file_path]
        
        # Check if there's a callback chain for this file
        if file_path in interceptor.file_callback_chain:
            callback_chain = interceptor.file_callback_chain[file_path]
            index = callback_chain['index']
            
            # If there are more chunks
            if index < len(chunks):
                chunk = chunks[index]
                callback_chain['index'] += 1
                
                # Add a note about chunking
                if index < len(chunks) - 1:
                    chunk_note = f"\n\n[Note: This is chunk {index + 1} of {len(chunks)}. Use the safe_cat function to view the next chunk.]\n"
                    return chunk + chunk_note
                else:
                    return chunk
            else:
                # No more chunks
                return None
        else:
            # Create a new callback chain
            interceptor.file_callback_chain[file_path] = {
                'index': 1  # Start from the second chunk (index 1)
            }
            
            # If there are more chunks
            if len(chunks) > 1:
                chunk = chunks[1]
                
                # Add a note about chunking
                if len(chunks) > 2:
                    chunk_note = f"\n\n[Note: This is chunk 2 of {len(chunks)}. Use the safe_cat function to view the next chunk.]\n"
                    return chunk + chunk_note
                else:
                    return chunk
            else:
                # No more chunks
                return None
    else:
        # No chunks for this file
        return None

def safe_cat(file_path):
    """
    Safe version of the cat command that respects rate limits
    
    Args:
        file_path: Path to the file
        
    Returns:
        The content of the file, possibly chunked
    """
    # Check if this is a request for the next chunk
    next_chunk = get_next_chunk(file_path)
    if next_chunk is not None:
        return next_chunk
    
    # Convert to string if it's a Path object
    if isinstance(file_path, Path):
        file_path = str(file_path)
    
    logger.info(f"Safe cat requested for {file_path}")
    
    # Open the file using our intercepted open
    with open(file_path, 'r') as f:
        content = f.read()
    
    return content

def safe_ls(directory_path):
    """
    Safe version of the ls command that respects rate limits
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        A list of items in the directory
    """
    # Convert to string if it's a Path object
    if isinstance(directory_path, Path):
        directory_path = str(directory_path)
    
    logger.info(f"Safe ls requested for {directory_path}")
    
    # Queue the operation
    result = [None]
    event = threading.Event()
    
    def callback(items, error):
        if error:
            logger.error(f"Error listing directory {directory_path}: {error}")
            result[0] = f"Error: {error}"
        else:
            result[0] = items
        event.set()
    
    # Create a function that lists the directory
    def list_dir_func():
        # List the directory using the original Python functions
        items = os.listdir(directory_path)
        
        # Format the output similar to ls
        result = []
        for item in items:
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                result.append(f"{item}/")
            else:
                size = os.path.getsize(item_path)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                result.append(f"{item} ({size_str})")
        
        return "\n".join(result)
    
    # Queue the operation
    interceptor.operation_queue.add_operation(
        list_dir_func,
        estimated_tokens=500,  # Conservative estimate for directory listing
        callback=callback
    )
    
    # Wait for the operation to complete
    event.wait()
    return result[0]

def get_stats():
    """
    Get statistics about the interceptor
    
    Returns:
        Dictionary with statistics
    """
    queue_stats = interceptor.operation_queue.get_stats()
    token_stats = token_manager.get_stats()
    
    return {
        **queue_stats,
        **token_stats
    }

# Apply all monkey patches to intercept file operations
interceptor.monkey_patch_all()

logger.info("Tool interception module initialized and ready")
