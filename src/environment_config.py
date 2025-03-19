"""
Environment configuration for PALIOS-TAEY
This module handles environment setup and configuration
"""

import os
import logging
from pathlib import Path

def initialize_environment():
    """Initialize environment variables and configuration"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Set default environment variables if not already set
    if 'PROJECT_ID' not in os.environ:
        os.environ['PROJECT_ID'] = os.environ.get('GOOGLE_CLOUD_PROJECT', 'palios-taey-dev')
    
    if 'ENVIRONMENT' not in os.environ:
        os.environ['ENVIRONMENT'] = 'production'
        
    if 'USE_MOCK_RESPONSES' not in os.environ:
        os.environ['USE_MOCK_RESPONSES'] = 'true'
    
    # Initialize component imports
    initialize_component_imports()
    
    logging.info(f"Environment initialized: {os.environ.get('ENVIRONMENT')}")

def initialize_component_imports():
    """Initialize component imports with robust error handling"""
    try:
        # Add src to path if needed for local development
        import sys
        root_path = Path(__file__).parent.parent
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))
    except Exception as e:
        logging.warning(f"Error setting up path: {str(e)}")
