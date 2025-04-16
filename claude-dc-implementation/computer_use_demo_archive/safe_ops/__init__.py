"""
Safe File Operations Module

This module provides functions for safely reading files and listing directories
with rate limit awareness.

Functions:
    safe_cat: Safely read a file
    safe_ls: Safely list a directory
    safe_file_info: Get detailed file metadata
"""

# Import and rename functions for consistent API
from .safe_file_operations import read_file_safely as safe_cat
from .safe_file_operations import list_directory_safely as safe_ls  
from .safe_file_operations import get_file_metadata as safe_file_info

# For backward compatibility
from .safe_file_operations import read_file_safely, list_directory_safely, get_file_metadata