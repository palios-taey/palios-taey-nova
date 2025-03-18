#!/bin/bash
# deploy_modules.sh
# Deploys the PALIOS-TAEY system with proper module structure

set -e  # Exit on any error

# Configuration
PROJECT_ID=${PROJECT_ID:-"palios-taey-dev"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"palios-taey-service"}
IMAGE_NAME="palios-taey"
TAG=${TAG:-"modules-fixed"}

# Display configuration
echo "Deploying PALIOS-TAEY with fixed module structure:"
echo "  Project ID:   $PROJECT_ID"
echo "  Region:       $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image:        $IMAGE_NAME:$TAG"
echo ""

# Prepare directory structure for the modules
echo "Creating package structure..."
mkdir -p src/palios_taey/core
mkdir -p src/palios_taey/memory
mkdir -p src/palios_taey/models
mkdir -p src/palios_taey/routing
mkdir -p src/palios_taey/api
mkdir -p src/palios_taey/tasks
mkdir -p src/palios_taey/transcripts

# Create __init__.py files for proper Python packages
touch src/__init__.py
touch src/palios_taey/__init__.py
touch src/palios_taey/core/__init__.py
touch src/palios_taey/memory/__init__.py
touch src/palios_taey/models/__init__.py
touch src/palios_taey/routing/__init__.py
touch src/palios_taey/api/__init__.py
touch src/palios_taey/tasks/__init__.py
touch src/palios_taey/transcripts/__init__.py

# Copy the core modules from the repository
echo "Copying core module..."
cp ../src/palios_taey/core/errors.py src/palios_taey/core/
cp ../src/palios_taey/core/utils.py src/palios_taey/core/

# Copy the memory modules
echo "Copying memory module..."
cp ../src/palios_taey/memory/models.py src/palios_taey/memory/
cp ../src/palios_taey/memory/service.py src/palios_taey/memory/

# Copy the models module
echo "Copying models module..."
cp ../src/palios_taey/models/registry.py src/palios_taey/models/

# Copy the routing module
echo "Copying routing module..."
cp ../src/palios_taey/routing/router.py src/palios_taey/routing/

# Create a minimal setup.py file to make the package installable
cat > setup.py <<'SETUPEOF'
from setuptools import setup, find_packages

setup(
    name="palios_taey",
    version="0.1.0",
    packages=find_packages(),
)
SETUPEOF

# Create a Dockerfile that properly sets up the module
cat > Dockerfile <<'DOCKEREOF'
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY *.py .
COPY templates/ templates/
COPY config/ config/

# Copy source modules
COPY src/ /app/src/

# Install the package in development mode
RUN pip install -e .

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]
DOCKEREOF

# Update app.py to use proper imports
cat > app.py <<'APPEOF'
"""
PALIOS-TAEY Main Application

This is the main entry point for the PALIOS-TAEY application,
integrating the core modules with the GCP environment.
"""
import os
import logging
import json
from flask import Flask, jsonify, request, render_template
from functools import wraps
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import core error types
from src.palios_taey.core.errors import (
    PaliosTaeyError, ValidationError, NotFoundError,
    AuthorizationError, ConfigurationError, ExternalServiceError
)
logger.info("Successfully imported core error types")

# Import core utilities
from src.palios_taey.core.utils import generate_id, to_json, from_json, deep_merge
logger.info("Successfully imported core utilities")

# Import memory system
from src.palios_taey.memory.service import create_memory_system
from src.palios_taey.memory.models import MemoryItem, MemoryQuery, MemoryTier, MemoryUpdateRequest
logger.info("Successfully imported memory system")

# Import model registry and router
from src.palios_taey.models.registry import get_model_registry
from src.palios_taey.routing.router import get_model_router
logger.info("Successfully imported model registry and router")

# Initialize components
def initialize_components():
    """Initialize all system components"""
    # Get configuration from environment
    project_id = os.environ.get("PROJECT_ID", "palios-taey-dev")
    collection_prefix = os.environ.get("COLLECTION_PREFIX", "")
    use_emulator = os.environ.get("USE_FIRESTORE_EMULATOR", "False").lower() == "true"
    use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    
    # Initialize memory system
    try:
        memory_system = create_memory_system(
            project_id=project_id,
            collection_prefix=collection_prefix,
            use_emulator=use_emulator,
            use_mock=use_mock
        )
        logger.info("Memory system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize memory system: {e}")
        memory_system = None
    
    # Initialize model registry
    try:
        model_registry = get_model_registry()
        logger.info("Model registry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {e}")
        model_registry = None
    
    # Initialize model router
    try:
        model_router = get_model_router()
        logger.info("Model router initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model router: {e}")
        model_router = None
    
    return memory_system, model_registry, model_router

# Initialize components
memory_system, model_registry, model_router = initialize_components()

# Flask application instance
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
    # Check component health
    memory_status = "healthy"
    memory_mode = "unknown"
    model_registry_status = "healthy"
    model_router_status = "healthy"
    
    # Check memory system
    if memory_system:
        try:
            memory_mode = "mock" if getattr(memory_system, 'use_mock', True) else "firestore"
        except Exception as e:
            memory_status = f"error: {str(e)}"
    else:
        memory_status = "not_initialized"
    
    # Check model registry
    if model_registry:
        try:
            # Verify model registry by checking capabilities
            if hasattr(model_registry, 'get_capability_summary'):
                capabilities = model_registry.get_capability_summary()
                model_count = capabilities.get('model_count', 0)
                if model_count == 0:
                    model_registry_status = "warning: no models registered"
        except Exception as e:
            model_registry_status = f"error: {str(e)}"
    else:
        model_registry_status = "not_initialized"
    
    # Check model router
    if model_router:
        try:
            if hasattr(model_router, 'get_status'):
                router_status = model_router.get_status()
                if router_status.get('status') != 'active':
                    model_router_status = f"error: {router_status.get('status')}"
        except Exception as e:
            model_router_status = f"error: {str(e)}"
    else:
        model_router_status = "not_initialized"

    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "memory": {
                "status": memory_status,
                "mode": memory_mode
            },
            "model_registry": {
                "status": model_registry_status
            },
            "model_router": {
                "status": model_router_status
            }
        }
    })

# Memory API endpoints
@app.route('/api/memory/store', methods=['POST'])
@require_api_key
def memory_store():
    """Store a memory item"""
    try:
        # Validate memory system is available
        if not memory_system:
            return jsonify({"error": "Memory system not available"}), 503
            
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        content = data.get("content")
        context_id = data.get("context_id")
        metadata = data.get("metadata")
        tags = data.get("tags")
        relationships = data.get("relationships")
        tier = data.get("tier")
        
        # Use the memory system to store the item
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
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in memory_store: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/retrieve/<memory_id>', methods=['GET'])
@require_api_key
def memory_retrieve(memory_id):
    """Retrieve a memory item"""
    try:
        # Validate memory system is available
        if not memory_system:
            return jsonify({"error": "Memory system not available"}), 503
            
        # Get request parameters
        context_id = request.args.get('context_id')
        
        # Retrieve the memory item
        memory_item = memory_system.retrieve(
            memory_id=memory_id,
            context_id=context_id
        )
        
        # Check if item was found
        if memory_item is None:
            return jsonify({"error": "Memory item not found"}), 404
        
        return jsonify({
            "memory_item": memory_item,
            "status": "success"
        })
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error in memory_retrieve: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/query', methods=['POST'])
@require_api_key
def memory_query():
    """Query memory items"""
    try:
        # Validate memory system is available
        if not memory_system:
            return jsonify({"error": "Memory system not available"}), 503
            
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "No query parameters provided"}), 400
        
        # Extract query parameters
        query_text = data.get("query_text")
        filters = data.get("filters")
        context_id = data.get("context_id")
        limit = data.get("limit", 10)
        include_tiers = data.get("include_tiers")
        
        # Execute the query
        memory_items = memory_system.query(
            query_text=query_text,
            filters=filters,
            context_id=context_id,
            limit=limit,
            include_tiers=include_tiers
        )
        
        return jsonify({
            "results": memory_items,
            "count": len(memory_items),
            "status": "success"
        })
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in memory_query: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Model Registry API endpoints
@app.route('/api/models/list', methods=['GET'])
@require_api_key
def models_list():
    """List available models"""
    try:
        # Validate model registry is available
        if not model_registry:
            return jsonify({"error": "Model registry not available"}), 503
        
        # Get request parameters
        task_type = request.args.get('task_type')
        min_capability = request.args.get('min_capability')
        
        if min_capability:
            try:
                min_capability = float(min_capability)
            except ValueError:
                return jsonify({"error": "Invalid min_capability value"}), 400
        
        # Get models from registry
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
    """Register a model in the registry"""
    try:
        # Validate model registry is available
        if not model_registry:
            return jsonify({"error": "Model registry not available"}), 503
        
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        model_id = data.get("model_id")
        if not model_id:
            return jsonify({"error": "Model ID is required"}), 400
            
        capabilities = data.get("capabilities", {})
        persist = data.get("persist", True)
        
        # Register the model
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
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in models_register: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/capabilities/<model_id>', methods=['GET'])
@require_api_key
def models_get_capabilities(model_id):
    """Get capabilities for a specific model"""
    try:
        # Validate model registry is available
        if not model_registry:
            return jsonify({"error": "Model registry not available"}), 503
        
        # Get capabilities
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

# Model Router API endpoints
@app.route('/api/router/route', methods=['POST'])
@require_api_key
def router_route_task():
    """Route a task to the appropriate model"""
    try:
        # Validate model router is available
        if not model_router:
            return jsonify({"error": "Model router not available"}), 503
        
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "No task data provided"}), 400
        
        # Extract excluded models if provided
        excluded_models = data.get("excluded_models", [])
        
        # Route the task
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
    """Get model suggestions for a task type"""
    try:
        # Validate model router is available
        if not model_router:
            return jsonify({"error": "Model router not available"}), 503
        
        # Get request parameters
        task_type = request.args.get('task_type', 'general')
        count = request.args.get('count', '3')
        
        try:
            count = int(count)
        except ValueError:
            count = 3
        
        # Get suggestions
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
APPEOF

# Ensure gcloud is set to the correct project
echo "Setting gcloud project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Build the container image
echo "Building container image..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/palios-taey/$IMAGE_NAME:$TAG

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/palios-taey/$IMAGE_NAME:$TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ENVIRONMENT=dev,COLLECTION_PREFIX=memory_,MODELS_CONFIG_DIR=config/model_capabilities,MIN_CAPABILITY_SCORE=0.7,USE_MOCK_RESPONSES=true,PYTHONPATH=/app"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')
echo ""
echo "Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo ""

# Verify the deployment
echo "Verifying deployment..."
curl -s $SERVICE_URL/health

echo ""
echo "To run the verification tests against the deployed service:"
echo "export API_URL=$SERVICE_URL"
echo "export API_KEY=test_key"
echo "python verify_memory.py"
echo "python verify_models.py"
