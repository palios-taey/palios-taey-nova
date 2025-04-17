"""
Computer Use Demo package initialization.
"""

# Import core components
try:
    from .adaptive_client import create_adaptive_client
    from .token_manager import token_manager
except ImportError:
    pass  # Allow partial imports during initialization
