# Safe File Operations

This module provides file operations that respect rate limits to prevent 429 errors.

## Key Features
- Estimates token counts before reading files
- Uses sliding window approach to track input token usage
- Chunks large files and adds delays when needed
- Provides safe alternatives to common file operations

## Usage Example
```python
from safe_ops.safe_tools import safe_cat, safe_ls, safe_file_info

# Safely read a file
content = safe_cat("/path/to/file.txt")

# Safely list a directory
items = safe_ls("/path/to/directory")

# Get file metadata
metadata = safe_file_info("/path/to/file.txt")
```

Created on: $(date)