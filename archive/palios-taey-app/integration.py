"""
PALIOS-TAEY GCP Integration Module

This module provides the integration layer between the existing PALIOS-TAEY
modules and the Google Cloud Platform environment.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the core error handling
try:
    from src.palios_taey.core.errors import (
        PaliosTaeyError,
        ValidationError,
        NotFoundError,
        AuthorizationError,
        ConfigurationError,
        ExternalServiceError,
    )
    logger.info("Successfully imported core error types")
except ImportError as e:
    logger.error(f"Failed to import core error types: {e}")
    # Define fallback error types for critical functionality
    class PaliosTaeyError(Exception): pass
    class ValidationError(PaliosTaeyError): pass
    class NotFoundError(PaliosTaeyError): pass
    class AuthorizationError(PaliosTaeyError): pass
    class ConfigurationError(PaliosTaeyError): pass
    class ExternalServiceError(PaliosTaeyError): pass

# Import core utilities
try:
    from src.palios_taey.core.utils import generate_id, to_json, from_json, deep_merge
    logger.info("Successfully imported core utilities")
except ImportError as e:
    logger.error(f"Failed to import core utilities: {e}")
    # These will be needed, so provide minimal fallback implementations
    import uuid
    import json
    
    def generate_id(prefix: str = "") -> str:
        uuid_str = str(uuid.uuid4())
        return f"{prefix}{uuid_str}" if prefix else uuid_str
    
    def to_json(obj: any) -> str:
        def default_serializer(o):
            if isinstance(o, datetime):
                return o.isoformat()
            return str(o)
        return json.dumps(obj, default=default_serializer)
    
    def from_json(json_str: str) -> any:
        return json.loads(json_str)
    
    def deep_merge(dict1: dict, dict2: dict) -> dict:
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

# Import the memory service
try:
    from src.palios_taey.memory.service import create_memory_system, UnifiedMemorySystem
    from src.palios_taey.memory.models import MemoryItem, MemoryQuery, MemoryTier, MemoryUpdateRequest
    logger.info("Successfully imported memory system")
    MEMORY_IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"Failed to import memory system: {e}")
    MEMORY_IMPORT_SUCCESS = False

def initialize_memory_system():
    """
    Initialize the memory system with GCP-specific configuration
    
    Returns:
        Initialized memory system instance
    """
    if not MEMORY_IMPORT_SUCCESS:
        logger.error("Cannot initialize memory system - import failed")
        return None
    
    # Get configuration from environment
    project_id = os.environ.get("PROJECT_ID", "palios-taey-dev")
    collection_prefix = os.environ.get("COLLECTION_PREFIX", "")
    use_emulator = os.environ.get("USE_FIRESTORE_EMULATOR", "False").lower() == "true"
    use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    cache_size = int(os.environ.get("MEMORY_CACHE_SIZE", "1000"))
    
    try:
        # Create the memory system using the factory function from the original module
        memory_system = create_memory_system(
            project_id=project_id, 
            collection_prefix=collection_prefix,
            use_emulator=use_emulator,
            use_mock=use_mock,
            cache_size=cache_size
        )
        
        logger.info(f"Memory system initialized with project: {project_id}, mode: {'mock' if use_mock else 'firestore'}")
        return memory_system
    except Exception as e:
        logger.error(f"Failed to initialize memory system: {e}")
        return None
