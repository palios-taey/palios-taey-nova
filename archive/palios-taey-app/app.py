"""
PALIOS-TAEY Main Application
"""
import os
import logging
from flask import Flask, jsonify, request, render_template
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import error types
try:
    from src.palios_taey.core.errors import (
        PaliosTaeyError, ValidationError, NotFoundError,
        AuthorizationError, ConfigurationError, ExternalServiceError
    )
    logger.info("Successfully imported core error types")
except ImportError as e:
    logger.error(f"Failed to import core error types: {e}")
    # Fallback error types
    class PaliosTaeyError(Exception): pass
    class ValidationError(PaliosTaeyError): pass
    class NotFoundError(PaliosTaeyError): pass
    class AuthorizationError(PaliosTaeyError): pass
    class ConfigurationError(PaliosTaeyError): pass
    class ExternalServiceError(PaliosTaeyError): pass

# Import memory system
try:
    from src.palios_taey.memory.service import UnifiedMemorySystem
    memory_system_import_success = True
    logger.info("Successfully imported memory system")
except ImportError as e:
    logger.error(f"Failed to import memory system: {e}")
    memory_system_import_success = False

# Import model registry
try:
    from src.palios_taey.models.registry import ModelRegistry
    model_registry_import_success = True
    logger.info("Successfully imported model registry")
except ImportError as e:
    logger.error(f"Failed to import model registry: {e}")
    model_registry_import_success = False

# Import model router
try:
    from src.palios_taey.routing.router import ModelRouter
    model_router_import_success = True
    logger.info("Successfully imported model router")
except ImportError as e:
    logger.error(f"Failed to import model router: {e}")
    model_router_import_success = False

# Initialize components
memory_system = None
if memory_system_import_success:
    try:
        memory_system = UnifiedMemorySystem(
            project_id=os.environ.get("PROJECT_ID", "palios-taey-dev"),
            collection_prefix=os.environ.get("COLLECTION_PREFIX", ""),
            use_emulator=os.environ.get("USE_FIRESTORE_EMULATOR", "False").lower() == "true",
            use_mock=os.environ.get("USE_MOCK_RESPONSES", "True").lower() == "true"
        )
        logger.info("Memory system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize memory system: {e}")

# Initialize model registry
model_registry = None
if model_registry_import_success:
    try:
        model_registry = ModelRegistry(
            config_dir=os.environ.get("MODELS_CONFIG_DIR", "config/model_capabilities")
        )
        logger.info("Model registry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {e}")

# Initialize model router
model_router = None
if model_router_import_success and model_registry:
    try:
        model_router = ModelRouter(
            model_registry=model_registry,
            min_capability_score=float(os.environ.get("MIN_CAPABILITY_SCORE", "0.7"))
        )
        logger.info("Model router initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model router: {e}")

# Flask application
app = Flask(__name__, template_folder="templates")

# API Key authentication
API_KEYS = {
    "test_key": "development"
}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key in API_KEYS:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page with dashboard"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "memory": {
                "status": "healthy" if memory_system else "not_initialized",
                "mode": "mock" if memory_system and hasattr(memory_system, "use_mock") and memory_system.use_mock else "unknown"
            },
            "model_registry": {
                "status": "healthy" if model_registry else "not_initialized"
            },
            "model_router": {
                "status": "healthy" if model_router else "not_initialized"
            }
        }
    })

# Memory API
@app.route('/api/memory/store', methods=['POST'])
@require_api_key
def memory_store():
    if not memory_system:
        return jsonify({"error": "Memory system not available"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        content = data.get("content")
        context_id = data.get("context_id")
        metadata = data.get("metadata")
        tags = data.get("tags")
        relationships = data.get("relationships")
        tier = data.get("tier")
        
        memory_id = memory_system.store(
            content=content,
            context_id=context_id,
            metadata=metadata,
            tags=tags,
            relationships=relationships,
            initial_tier=tier
        )
        
        return jsonify({
            "memory_id": memory_id,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in memory_store: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/retrieve/<memory_id>', methods=['GET'])
@require_api_key
def memory_retrieve(memory_id):
    if not memory_system:
        return jsonify({"error": "Memory system not available"}), 503
    
    try:
        context_id = request.args.get('context_id')
        memory_item = memory_system.retrieve(
            memory_id=memory_id,
            context_id=context_id
        )
        
        if memory_item is None:
            return jsonify({"error": "Memory item not found"}), 404
        
        return jsonify({
            "memory_item": memory_item,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in memory_retrieve: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/query', methods=['POST'])
@require_api_key
def memory_query():
    if not memory_system:
        return jsonify({"error": "Memory system not available"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "No query parameters provided"}), 400
    
    try:
        query_text = data.get("query_text")
        filters = data.get("filters")
        context_id = data.get("context_id")
        limit = data.get("limit", 10)
        include_tiers = data.get("include_tiers")
        
        results = memory_system.query(
            query_text=query_text,
            filters=filters,
            context_id=context_id,
            limit=limit,
            include_tiers=include_tiers
        )
        
        return jsonify({
            "results": results,
            "count": len(results),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in memory_query: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Model Registry API
@app.route('/api/models/list', methods=['GET'])
@require_api_key
def models_list():
    if not model_registry:
        return jsonify({"error": "Model registry not available"}), 503
    
    try:
        task_type = request.args.get('task_type')
        min_capability_str = request.args.get('min_capability')
        min_capability = None
        
        if min_capability_str:
            try:
                min_capability = float(min_capability_str)
            except ValueError:
                return jsonify({"error": "Invalid min_capability value"}), 400
        
        models = model_registry.list_models(
            task_type=task_type,
            min_capability=min_capability
        )
        
        return jsonify({
            "models": models,
            "count": len(models),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in models_list: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/register', methods=['POST'])
@require_api_key
def models_register():
    if not model_registry:
        return jsonify({"error": "Model registry not available"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        model_id = data.get("model_id")
        if not model_id:
            return jsonify({"error": "Model ID is required"}), 400
        
        capabilities = data.get("capabilities", {})
        persist = data.get("persist", True)
        
        success = model_registry.register_model(
            model_id=model_id,
            capabilities=capabilities,
            persist=persist
        )
        
        if not success:
            return jsonify({"error": "Failed to register model"}), 500
        
        return jsonify({
            "model_id": model_id,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in models_register: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/capabilities/<model_id>', methods=['GET'])
@require_api_key
def models_get_capabilities(model_id):
    if not model_registry:
        return jsonify({"error": "Model registry not available"}), 503
    
    try:
        capabilities = model_registry.get_model_capabilities(model_id)
        
        if not capabilities:
            return jsonify({"error": f"Model {model_id} not found"}), 404
        
        return jsonify({
            "model_id": model_id,
            "capabilities": capabilities,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in models_get_capabilities: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Model Router API
@app.route('/api/router/route', methods=['POST'])
@require_api_key
def router_route_task():
    if not model_router:
        return jsonify({"error": "Model router not available"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "No task data provided"}), 400
    
    try:
        excluded_models = data.get("excluded_models", [])
        selected_model = model_router.route_task(data, excluded_models)
        
        return jsonify({
            "task_id": data.get("task_id", "unknown"),
            "selected_model": selected_model,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in router_route_task: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/router/suggest', methods=['GET'])
@require_api_key
def router_suggest_models():
    if not model_router:
        return jsonify({"error": "Model router not available"}), 503
    
    try:
        task_type = request.args.get('task_type', 'general')
        count_str = request.args.get('count', '3')
        
        try:
            count = int(count_str)
        except ValueError:
            count = 3
        
        suggestions = model_router.get_model_suggestions(
            task_type=task_type,
            count=count
        )
        
        return jsonify({
            "task_type": task_type,
            "suggestions": suggestions,
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in router_suggest_models: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(NotFoundError)
def handle_not_found_error(e):
    return jsonify({"error": str(e)}), 404

@app.errorhandler(AuthorizationError)
def handle_authorization_error(e):
    return jsonify({"error": str(e)}), 401

@app.errorhandler(ConfigurationError)
def handle_configuration_error(e):
    return jsonify({"error": str(e)}), 500

@app.errorhandler(ExternalServiceError)
def handle_external_service_error(e):
    return jsonify({"error": str(e)}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting PALIOS-TAEY application on port {port}")
    logger.info(f"Memory system: {'Available' if memory_system else 'Not available'}")
    logger.info(f"Model registry: {'Available' if model_registry else 'Not available'}")
    logger.info(f"Model router: {'Available' if model_router else 'Not available'}")
    app.run(host="0.0.0.0", port=port)
