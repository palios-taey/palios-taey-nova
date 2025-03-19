#!/bin/bash

# Create environment_config.py if it doesn't exist
mkdir -p src
cat > src/environment_config.py << 'EOF'
"""
Environment configuration for PALIOS-TAEY
This module handles environment setup and configuration
"""

import os
import logging

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
        os.environ['USE_MOCK_RESPONSES'] = 'True'
    
    logging.info(f"Environment initialized: {os.environ.get('ENVIRONMENT')}")
EOF

echo "Environment config module created successfully at src/environment_config.py"
