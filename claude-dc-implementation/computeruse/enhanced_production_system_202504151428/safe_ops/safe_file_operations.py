"""
Enhanced Safe File Operations Module

Provides functions for safely reading files and listing directories with rate limit awareness.
Integrated with Token Management module for unified token tracking and rate limit prevention.
Uses tiktoken for accurate token estimation.
"""

import os
import time
import logging
import random
from typing import Dict, List, Tuple, Optional, Callable, Any

# Import Token Management module
import sys
sys.path.append('/home/computeruse/computer_use_demo')
from token_management.token_manager import token_manager

# Import tiktoken for accurate token estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    # Initialize tokenizer - this approximates Claude's tokenization
    ENCODING = tiktoken.get_encoding("cl100k_base")  # Claude-like tokenizer
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("tiktoken not available, falling back to character-based estimation")

# Configure enhanced logging with more detailed information
log_file = '/tmp/safe_file_operations.log'
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
   handlers=[
       logging.FileHandler(log_file),
       logging.StreamHandler()
   ]
)
logger = logging.getLogger("safe_file_operations")

class SafeFileOperations:
    """
    Provides safe file operations that respect rate limits
    """
    
    def __init__(self):
        # Rate limit settings
        self.org_input_limit = 40000  # 40K tokens per minute
        self.target_usage_percent = 55  # Reduced from 60% to 55% for more safety
        self.max_chunk_tokens = int(self.org_input_limit * self.target_usage_percent / 100)
        
        # Delay settings
        self.min_operation_delay = 0.1  # 100ms minimum delay between operations
        self.max_operation_delay = 0.3  # 300ms maximum delay
        
        # Retry settings
        self.max_retries = 3
        self.retry_base_delay = 1.0  # Base delay for exponential backoff
        
        logger.info(f"Safe file operations initialized with max chunk size of {self.max_chunk_tokens} tokens (60% of rate limit)")
    
    def estimate_tokens(self, text):
        """
        Estimate token count for text using tiktoken if available
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Use tiktoken if available for accurate estimation
        if TIKTOKEN_AVAILABLE:
            try:
                return len(ENCODING.encode(text))
            except Exception as e:
                logger.warning(f"Error using tiktoken: {e}. Falling back to character-based estimation")
        
        # Fallback to character-based approximation if tiktoken fails or isn't available
        # More conservative ratio: 1 token ≈ 3.5 characters (instead of 4)
        return len(text) // 3.5
    
    def estimate_file_tokens(self, file_path):
        """
        Estimate token count for a file without reading the entire file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Estimated token count
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # For very small files, just read the whole thing
            if file_size < 50000:  # 50KB
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return self.estimate_tokens(content)
            
            # For larger files, sample from beginning, middle, and end for better estimation
            sample_size = min(file_size // 3, 10000)  # Up to 10KB from each part
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read from beginning
                beginning = file.read(sample_size)
                
                # Read from middle
                middle_pos = max(file_size // 2 - sample_size // 2, sample_size)
                file.seek(middle_pos)
                middle = file.read(sample_size)
                
                # Read from end
                end_pos = max(file_size - sample_size, 2 * sample_size)
                file.seek(end_pos)
                end = file.read(sample_size)
            
            # Combine samples and estimate
            combined_sample = beginning + middle + end
            sample_tokens = self.estimate_tokens(combined_sample)
            
            # Extrapolate to estimate total tokens with a 10% safety margin
            sample_bytes = len(combined_sample.encode('utf-8'))
            raw_estimate = int(sample_tokens * (file_size / sample_bytes))
            estimated_tokens = int(raw_estimate * 1.1)  # Add 10% safety margin
            
            logger.info(f"File {file_path}: {file_size} bytes, estimated {estimated_tokens} tokens")
            return estimated_tokens
        except Exception as e:
            logger.error(f"Error estimating tokens for {file_path}: {e}")
            # Return a very conservative high estimate to ensure caution
            return 80000  # Very conservative estimate
    
    def add_operation_delay(self):
        """Add a small random delay between operations to prevent burst requests"""
        delay = random.uniform(self.min_operation_delay, self.max_operation_delay)
        time.sleep(delay)
        logger.debug(f"Added {delay:.2f}s operation delay")
    
    def delay_if_needed(self, estimated_input_tokens, estimated_output_tokens=None):
        """
        Check if a delay is needed and delay if necessary using the token manager
        
        Args:
            estimated_input_tokens: Estimated input tokens for the operation
            estimated_output_tokens: Estimated output tokens (default is 20% of input)
        """
        if estimated_output_tokens is None:
            # Default estimate: output is ~20% of input for file operations
            estimated_output_tokens = int(estimated_input_tokens * 0.2)
        
        # Use token manager's delay mechanism to check both input and output limits
        token_manager.delay_if_needed(estimated_input_tokens, estimated_output_tokens)
        
        # Add additional small delay to prevent burst requests
        self.add_operation_delay()
    
    def safe_read_file(self, file_path, chunk_callback=None, max_retries=None):
        """
        Safely read a file with token limit awareness
        
        Args:
            file_path: Path to the file to read
            chunk_callback: Function to call with each chunk (optional)
            max_retries: Maximum number of retries on failure (uses default if None)
            
        Returns:
            The file content
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        for attempt in range(max_retries + 1):
            try:
                # First, estimate token count
                estimated_tokens = self.estimate_file_tokens(file_path)
                
                # Warn if file is large
                if estimated_tokens > self.org_input_limit * 0.4:  # Lower threshold for warnings
                    print(f"⚠️ WARNING: File is large ({estimated_tokens} estimated tokens)")
                    print(f"Reading in chunks of max {self.max_chunk_tokens} tokens with delays to avoid rate limits")
                
                # If file is small enough, read it directly
                if estimated_tokens <= self.max_chunk_tokens:
                    self.delay_if_needed(estimated_tokens)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    return content
                
                # For large files, read in chunks
                chunks = []
                with open(file_path, 'r', encoding='utf-8') as file:
                    current_chunk = ""
                    current_chunk_tokens = 0
                    
                    for line in file:
                        line_tokens = self.estimate_tokens(line)
                        
                        # If adding this line would exceed chunk size, process the current chunk
                        if current_chunk_tokens + line_tokens > self.max_chunk_tokens:
                            # Process current chunk
                            self.delay_if_needed(current_chunk_tokens)
                            chunks.append(current_chunk)
                            
                            if chunk_callback:
                                chunk_callback(current_chunk)
                            
                            # Reset chunk
                            current_chunk = line
                            current_chunk_tokens = line_tokens
                        else:
                            # Add line to current chunk
                            current_chunk += line
                            current_chunk_tokens += line_tokens
                    
                    # Process the final chunk if not empty
                    if current_chunk:
                        self.delay_if_needed(current_chunk_tokens)
                        chunks.append(current_chunk)
                        
                        if chunk_callback:
                            chunk_callback(current_chunk)
                
                return "".join(chunks)
            except Exception as e:
                if attempt < max_retries:
                    # Calculate backoff delay: 2^attempt * base_delay * (0.5-1.5 random jitter)
                    backoff = self.retry_base_delay * (2 ** attempt) * random.uniform(0.5, 1.5)
                    logger.warning(f"Attempt {attempt+1}/{max_retries+1} failed: {e}. Retrying in {backoff:.2f}s")
                    print(f"⚠️ File operation failed: Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Error reading {file_path} after {max_retries+1} attempts: {e}")
                    return f"ERROR: Could not read file {file_path} after {max_retries+1} attempts: {e}"
    
    def safe_list_directory(self, directory_path, max_retries=None):
        """
        Safely list directory contents with token awareness
        
        Args:
            directory_path: Path to the directory
            max_retries: Maximum number of retries on failure (uses default if None)
            
        Returns:
            List of directory contents with metadata
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        for attempt in range(max_retries + 1):
            try:
                # List directory contents
                items = os.listdir(directory_path)
                
                # Estimate tokens needed (improved estimation)
                estimated_tokens = 200 + len(items) * 70  # Base + per item
                
                # Delay if needed
                self.delay_if_needed(estimated_tokens)
                
                # Get metadata for each item
                result = []
                for item in items:
                    item_path = os.path.join(directory_path, item)
                    
                    if os.path.isdir(item_path):
                        result.append({
                            "name": item,
                            "type": "directory",
                            "size": "-"
                        })
                    else:
                        size = os.path.getsize(item_path)
                        result.append({
                            "name": item,
                            "type": "file",
                            "size": size,
                            "estimated_tokens": self.estimate_file_tokens(item_path) if size > 1000 else "-"
                        })
                    
                    # Small delay between processing items to prevent bursts
                    self.add_operation_delay()
                
                return result
            except Exception as e:
                if attempt < max_retries:
                    # Calculate backoff delay
                    backoff = self.retry_base_delay * (2 ** attempt) * random.uniform(0.5, 1.5)
                    logger.warning(f"Attempt {attempt+1}/{max_retries+1} failed: {e}. Retrying in {backoff:.2f}s")
                    print(f"⚠️ Directory operation failed: Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Error listing directory {directory_path} after {max_retries+1} attempts: {e}")
                    return f"ERROR: Could not list directory {directory_path} after {max_retries+1} attempts: {e}"

# Create a singleton instance
safe_file_ops = SafeFileOperations()

# Export safe functions
def read_file_safely(file_path):
    """Safe wrapper for reading files"""
    return safe_file_ops.safe_read_file(file_path)

def list_directory_safely(directory_path):
    """Safe wrapper for listing directories"""
    return safe_file_ops.safe_list_directory(directory_path)

def get_file_metadata(file_path):
    """Get metadata including estimated token count"""
    try:
        size = os.path.getsize(file_path)
        estimated_tokens = safe_file_ops.estimate_file_tokens(file_path)
        
        return {
            "path": file_path,
            "size_bytes": size,
            "estimated_tokens": estimated_tokens,
            "chunks_needed": estimated_tokens // safe_file_ops.max_chunk_tokens + 1
        }
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {e}")
        return f"ERROR: Could not get metadata for {file_path}: {e}"