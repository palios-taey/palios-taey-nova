"""
PALIOS-TAEY Models and Routing Integration

This module provides the integration layer for the model registry and routing components.
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
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to find the src directory
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Display the path for debugging
logger.info(f"Python path: {sys.path}")
logger.info(f"Current directory: {current_dir}")
logger.info(f"Parent directory: {parent_dir}")
logger.info(f"Looking for src/palios_taey/models/registry.py")

# Import model registry
try:
    # Try direct import first
    from src.palios_taey.models.registry import get_model_registry
    logger.info("Successfully imported model registry via direct import")
    MODEL_REGISTRY_IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"Direct import failed: {e}")
    # Try fallback import with explicit paths
    try:
        # Try to find the module in various paths
        import importlib.util
        import os
        
        # Look for the module in likely locations
        potential_paths = [
            os.path.join(parent_dir, "src", "palios_taey", "models", "registry.py"),
            os.path.join(current_dir, "src", "palios_taey", "models", "registry.py"),
            os.path.join(os.path.dirname(parent_dir), "src", "palios_taey", "models", "registry.py")
        ]
        
        module_path = None
        for path in potential_paths:
            if os.path.exists(path):
                module_path = path
                logger.info(f"Found module at: {module_path}")
                break
        
        if module_path:
            spec = importlib.util.spec_from_file_location("registry", module_path)
            registry_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(registry_module)
            get_model_registry = registry_module.get_model_registry
            logger.info("Successfully imported model registry via spec loader")
            MODEL_REGISTRY_IMPORT_SUCCESS = True
        else:
            # Final fallback - create a mock registry
            logger.error("Could not find model registry module, using mock implementation")
            MODEL_REGISTRY_IMPORT_SUCCESS = False
    except Exception as secondary_error:
        logger.error(f"Secondary import attempt failed: {secondary_error}")
        MODEL_REGISTRY_IMPORT_SUCCESS = False

# Import model router with similar robust approach
try:
    from src.palios_taey.routing.router import get_model_router
    logger.info("Successfully imported model router")
    MODEL_ROUTER_IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"Direct import of model router failed: {e}")
    # Try fallback import with explicit paths
    try:
        # Try to find the module in various paths
        import importlib.util
        
        potential_paths = [
            os.path.join(parent_dir, "src", "palios_taey", "routing", "router.py"),
            os.path.join(current_dir, "src", "palios_taey", "routing", "router.py"),
            os.path.join(os.path.dirname(parent_dir), "src", "palios_taey", "routing", "router.py")
        ]
        
        module_path = None
        for path in potential_paths:
            if os.path.exists(path):
                module_path = path
                logger.info(f"Found router module at: {module_path}")
                break
        
        if module_path:
            spec = importlib.util.spec_from_file_location("router", module_path)
            router_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(router_module)
            get_model_router = router_module.get_model_router
            logger.info("Successfully imported model router via spec loader")
            MODEL_ROUTER_IMPORT_SUCCESS = True
        else:
            # Final fallback - create a mock router
            logger.error("Could not find model router module, using mock implementation")
            MODEL_ROUTER_IMPORT_SUCCESS = False
    except Exception as secondary_error:
        logger.error(f"Secondary import attempt for router failed: {secondary_error}")
        MODEL_ROUTER_IMPORT_SUCCESS = False

# Mock model registry class if import fails
class MockModelRegistry:
    def __init__(self):
        self.model_capabilities = {
            "claude": {
                "document_summary": 0.95,
                "transcript_processing": 0.9,
                "general": 0.92
            },
            "gemini": {
                "document_summary": 0.9,
                "code_generation": 0.85,
                "general": 0.8
            }
        }
        logger.info("Initialized mock model registry with default models")
    
    def list_models(self, task_type=None, min_capability=None):
        models = []
        for model_id, capabilities in self.model_capabilities.items():
            if task_type:
                score = capabilities.get(task_type, 0.0)
                if min_capability and score < min_capability:
                    continue
                models.append({
                    'model_id': model_id,
                    'capability_score': score,
                    'capabilities': capabilities
                })
            else:
                models.append({
                    'model_id': model_id,
                    'capabilities': capabilities
                })
        return models
    
    def register_model(self, model_id, capabilities, persist=True):
        self.model_capabilities[model_id] = capabilities
        logger.info(f"Registered model {model_id} in mock registry")
        return True
    
    def get_model_capabilities(self, model_id):
        return self.model_capabilities.get(model_id, {})
    
    def get_capability_summary(self):
        return {
            'model_count': len(self.model_capabilities),
            'task_types': list(set(task for model in self.model_capabilities.values() for task in model))
        }

# Mock model router class if import fails
class MockModelRouter:
    def __init__(self, model_registry=None):
        self.model_registry = model_registry
        logger.info("Initialized mock model router")
    
    def route_task(self, task, excluded_models=None):
        task_type = task.get('task_type', 'general')
        # Simply return 'claude' for document tasks, 'gemini' for code tasks
        if task_type == 'document_summary' or task_type == 'transcript_processing':
            return 'claude'
        elif task_type == 'code_generation':
            return 'gemini'
        else:
            return 'claude'  # Default
    
    def get_model_suggestions(self, task_type='general', count=3):
        if task_type == 'document_summary':
            return [
                {'model_id': 'claude', 'reason': 'Best for document tasks'},
                {'model_id': 'gemini', 'reason': 'Good alternative for documents'}
            ][:count]
        elif task_type == 'code_generation':
            return [
                {'model_id': 'gemini', 'reason': 'Best for code tasks'},
                {'model_id': 'claude', 'reason': 'Good alternative for code'}
            ][:count]
        else:
            return [
                {'model_id': 'claude', 'reason': 'Best general model'},
                {'model_id': 'gemini', 'reason': 'Good alternative model'}
            ][:count]
    
    def get_status(self):
        return {'status': 'active', 'mode': 'mock'}

def initialize_model_registry():
    """
    Initialize the model registry with GCP-specific configuration
    
    Returns:
        Initialized model registry instance
    """
    if not MODEL_REGISTRY_IMPORT_SUCCESS:
        logger.warning("Using mock model registry implementation")
        return MockModelRegistry()
    
    # Get configuration from environment
    config_dir = os.environ.get("MODELS_CONFIG_DIR", "config/model_capabilities")
    use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    
    try:
        # Create the model registry using the factory function from the original module
        model_registry = get_model_registry(config_dir=config_dir)
        
        # Ensure the registry has at least default models
        if not model_registry.model_capabilities and (use_mock or len(model_registry.model_capabilities) == 0):
            # Initialize with some default models for testing
            model_registry.register_model(
                "claude", 
                {
                    "document_summary": 0.95,
                    "transcript_processing": 0.9,
                    "general": 0.92
                }
            )
            
            model_registry.register_model(
                "gemini", 
                {
                    "document_summary": 0.9,
                    "code_generation": 0.85,
                    "general": 0.8
                }
            )
            
            logger.info("Registered default models in model registry")
        
        logger.info("Model registry initialized successfully")
        return model_registry
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {e}")
        logger.warning("Falling back to mock model registry")
        return MockModelRegistry()

def initialize_model_router(model_registry=None):
    """
    Initialize the model router with GCP-specific configuration
    
    Args:
        model_registry: Existing model registry instance
        
    Returns:
        Initialized model router instance
    """
    if not MODEL_ROUTER_IMPORT_SUCCESS:
        logger.warning("Using mock model router implementation")
        return MockModelRouter(model_registry)
    
    # Get configuration from environment
    min_capability_score = float(os.environ.get("MIN_CAPABILITY_SCORE", "0.7"))
    use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    
    try:
        # Create the model router using the factory function from the original module
        model_router = get_model_router(
            min_capability_score=min_capability_score,
            use_mock=use_mock
        )
        
        logger.info(f"Model router initialized with min_capability_score: {min_capability_score}")
        return model_router
    except Exception as e:
        logger.error(f"Failed to initialize model router: {e}")
        logger.warning("Falling back to mock model router")
        return MockModelRouter(model_registry)
