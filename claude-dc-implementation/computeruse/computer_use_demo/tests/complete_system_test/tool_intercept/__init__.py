"""Tool Intercept Module

This module monkey-patches Python's built-in file operations and tool functions
to enforce rate limiting and chunking for ALL file operations.
"""

# Import everything from the tool_intercept module
from .tool_intercept import *

# Define an initialization function for consistency
def initialize_interception():
    """Initialize the tool interception system. This is automatically called when the module is imported."""
    # The interceptor is automatically initialized when imported, so we don't need to do anything here
    return True