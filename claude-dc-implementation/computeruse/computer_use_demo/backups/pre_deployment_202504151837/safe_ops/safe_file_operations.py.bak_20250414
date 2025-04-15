"""
Safe File Operations Module

Provides functions for safely reading files and listing directories with rate limit awareness.
Prevents 429 rate limit errors by intelligently chunking large files and introducing delays.
"""

import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Callable, Any

# Configure logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(levelname)s - %(message)s',
   filename='/tmp/safe_file_operations.log'
)
logger = logging.getLogger("safe_file_operations")

class SafeFileOperations:
   """
   Provides safe file operations that respect rate limits
   """
   
   def __init__(self):
       # Rate limit settings
       self.org_input_limit = 40000  # 40K tokens per minute
       self.target_usage_percent = 80  # Use 80% of limit for safety
       self.max_chunk_tokens = int(self.org_input_limit * self.target_usage_percent / 100)
       
       # Token tracking
       self.input_token_timestamps = []  # List of (timestamp, token_count) tuples
       
       logger.info(f"Safe file operations initialized with max chunk size of {self.max_chunk_tokens} tokens")
   
   def estimate_tokens(self, text):
       """
       Estimate token count for text
       
       Args:
           text: Text to estimate tokens for
           
       Returns:
           Estimated token count
       """
       # Rough approximation: 1 token ≈ 4 characters
       return len(text) // 4
   
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
           
           # Sample the file to get a more accurate token estimate
           sample_size = min(file_size, 10000)  # Sample up to 10KB
           
           with open(file_path, 'r', encoding='utf-8') as file:
               sample = file.read(sample_size)
           
           # Estimate tokens in the sample
           sample_tokens = self.estimate_tokens(sample)
           
           # Extrapolate to estimate total tokens
           estimated_tokens = int(sample_tokens * (file_size / len(sample.encode('utf-8'))))
           
           logger.info(f"File {file_path}: {file_size} bytes, estimated {estimated_tokens} tokens")
           return estimated_tokens
       except Exception as e:
           logger.error(f"Error estimating tokens for {file_path}: {e}")
           # Return a conservative high estimate to ensure caution
           return 50000
   
   def check_input_rate_limit(self, input_tokens):
       """
       Check if we're approaching the organization input token rate limit
       
       Args:
           input_tokens: Number of input tokens
           
       Returns:
           Tuple of (should_delay: bool, delay_time: float)
       """
       current_time = time.time()
       
       # Add this request to our sliding window
       self.input_token_timestamps.append((current_time, input_tokens))
       
       # Remove timestamps older than 1 minute
       one_minute_ago = current_time - 60
       self.input_token_timestamps = [
           (ts, tokens) for ts, tokens in self.input_token_timestamps 
           if ts >= one_minute_ago
       ]
       
       # Calculate current input tokens per minute
       tokens_per_minute = sum(tokens for _, tokens in self.input_token_timestamps)
       
       logger.info(f"Input tokens per minute: {tokens_per_minute}/{self.org_input_limit}")
       
       # Check if we're approaching the limit
       if tokens_per_minute + input_tokens >= self.org_input_limit:
           # Calculate how long we need to wait for the oldest request to drop off
           if self.input_token_timestamps:
               oldest_timestamp = min(ts for ts, _ in self.input_token_timestamps)
               seconds_to_wait = (oldest_timestamp + 60) - current_time
               
               # Add a 1 second safety buffer
               delay = max(seconds_to_wait, 0) + 1
               
               logger.warning(f"Rate limit approaching - need to wait {delay:.2f} seconds")
               return True, delay
       
       return False, 0
   
   def delay_if_needed(self, estimated_tokens):
       """
       Check if a delay is needed and delay if necessary
       
       Args:
           estimated_tokens: Estimated tokens for the operation
       """
       should_delay, delay_time = self.check_input_rate_limit(estimated_tokens)
       
       if should_delay:
           logger.info(f"Delaying for {delay_time:.2f} seconds to avoid rate limit")
           print(f"🕒 Delaying for {delay_time:.2f} seconds to avoid rate limit...")
           time.sleep(delay_time)
           print("✅ Resuming after delay")
   
   def safe_read_file(self, file_path, chunk_callback=None):
       """
       Safely read a file with token limit awareness
       
       Args:
           file_path: Path to the file to read
           chunk_callback: Function to call with each chunk (optional)
           
       Returns:
           The file content
       """
       try:
           # First, estimate token count
           estimated_tokens = self.estimate_file_tokens(file_path)
           
           # Warn if file is large
           if estimated_tokens > self.org_input_limit * 0.5:
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
           logger.error(f"Error reading {file_path}: {e}")
           return f"ERROR: Could not read file {file_path}: {e}"
   
   def safe_list_directory(self, directory_path):
       """
       Safely list directory contents with token awareness
       
       Args:
           directory_path: Path to the directory
           
       Returns:
           List of directory contents with metadata
       """
       try:
           # List directory contents
           items = os.listdir(directory_path)
           
           # Estimate tokens needed (rough approximation)
           estimated_tokens = 100 + len(items) * 50  # Base + per item
           
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
           
           return result
       except Exception as e:
           logger.error(f"Error listing directory {directory_path}: {e}")
           return f"ERROR: Could not list directory {directory_path}: {e}"

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