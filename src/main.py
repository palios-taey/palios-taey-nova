"""
PALIOS-TAEY System Main Server
This module serves as the main entry point for the PALIOS-TAEY system,
integrating all components and providing API endpoints.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from flask import Flask, request, jsonify
import uuid
import fix_environment_config

# Initialize environment before any other components
fix_environment_config.initialize_environment()

# Try to import dotenv for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', 'server.log'))
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Flag for mock mode (used when real services are unavailable)
USE_MOCK = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"

# Initialize Flask app
app = Flask(__name__)

# Global component instances
memory_system = None
transcript_processor = None
model_registry = None
task_decomposer = None
task_executor = None
model_router = None

def load_config() -> Dict[str, Any]:
    """Load configuration from config file or environment variables with robust error handling"""
    try:
        config_file = os.path.join('config', 'config.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading config file: {str(e)}")
                # Fall back to default configuration
        
        # Default configuration
        return {
            "project_id": os.environ.get("PROJECT_ID", "ai-execution-system"),
            "collection_prefix": os.environ.get("COLLECTION_PREFIX", "dev_"),
            "use_emulator": os.environ.get("USE_EMULATOR", "False").lower() == "true",
            "use_mock": USE_MOCK,
            "memory": {
                "cache_size": int(os.environ.get("MEMORY_CACHE_SIZE", "1000"))
            },
            "transcript": {
                "confidence_threshold": float(os.environ.get("CONFIDENCE_THRESHOLD", "0.7"))
            },
            "server": {
                "host": os.environ.get("HOST", "0.0.0.0"),
                "port": int(os.environ.get("PORT", "8080")),
                "debug": os.environ.get("DEBUG", "False").lower() == "true"
            }
        }
    except Exception as e:
        logger.error(f"Error in load_config: {str(e)}")
        # Return minimal configuration for basic operation
        return {
            "project_id": "ai-execution-system",
            "collection_prefix": "dev_",
            "use_emulator": False,
            "use_mock": True,
            "memory": {"cache_size": 1000},
            "transcript": {"confidence_threshold": 0.7},
            "server": {"host": "0.0.0.0", "port": 8080, "debug": False}
        }

def initialize_components(config: Dict[str, Any]) -> None:
    """Initialize system components with graceful failure handling"""
    global memory_system, transcript_processor, model_registry, task_decomposer, task_executor, model_router
    
    logger.info("Initializing PALIOS-TAEY system components...")
    
    # Extract configuration values
    project_id = config.get("project_id", "ai-execution-system")
    collection_prefix = config.get("collection_prefix", "dev_")
    use_emulator = config.get("use_emulator", False)
    use_mock = config.get("use_mock", USE_MOCK)
    
    # Initialize memory system
    try:
        from memory_service import create_memory_system
        memory_system = create_memory_system(
            project_id=project_id,
            collection_prefix=collection_prefix,
            use_emulator=use_emulator,
            use_mock=use_mock,
            cache_size=config.get("memory", {}).get("cache_size", 1000)
        )
        
        logger.info("Memory system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize memory system: {str(e)}")
        memory_system = None
    
    # Initialize model registry
    try:
        from model_registry import get_model_registry
        model_registry = get_model_registry()
        logger.info("Model registry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {str(e)}")
        model_registry = None
    
    # Initialize task decomposer
    try:
        from task_decomposition import get_task_decomposition_engine
        task_decomposer = get_task_decomposition_engine(use_mock=use_mock)
        logger.info("Task decomposition engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize task decomposition engine: {str(e)}")
        task_decomposer = None
    
    # Initialize model router
    try:
        from model_routing import get_model_router
        model_router = get_model_router(use_mock=use_mock)
        logger.info("Model router initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model router: {str(e)}")
        model_router = None
    
    # Initialize task executor with memory system integration
    try:
        # Create store/retrieve functions that use memory system
        def store_task(task: Dict[str, Any]) -> str:
            task_id = task.get('task_id', str(uuid.uuid4()))
            
            if memory_system:
                try:
                    memory_system.store(
                        content=task,
                        context_id=None,  # No specific context
                        metadata={
                            'memory_id': f"task_{task_id}",
                            'task_id': task_id,
                            'task_type': task.get('task_type', 'general'),
                            'status': task.get('status', 'pending')
                        },
                        tags=['task', task.get('task_type', 'general')]
                    )
                except Exception as e:
                    logger.error(f"Failed to store task in memory system: {str(e)}")
            else:
                logger.warning(f"Memory system not available, task {task_id} will not be persisted")
            
            return task_id
        
        def retrieve_task(task_id: str) -> Optional[Dict[str, Any]]:
            if not memory_system:
                logger.warning("Memory system not available, cannot retrieve task")
                return None
            
            try:
                memory_item = memory_system.retrieve(f"task_{task_id}")
                if memory_item:
                    return memory_item.get('content')
            except Exception as e:
                logger.error(f"Failed to retrieve task from memory system: {str(e)}")
            
            return None
        
        from task_execution import get_task_execution_engine
        task_executor = get_task_execution_engine(
            store_func=store_task,
            retrieve_func=retrieve_task,
            use_mock=use_mock
        )
        
        logger.info("Task execution engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize task execution engine: {str(e)}")
        task_executor = None
    
    # Initialize transcript processor
    try:
        from transcript_processor import create_transcript_processor
        transcript_processor = create_transcript_processor(
            memory_system=memory_system,
            project_id=project_id,
            collection_prefix=collection_prefix,
            use_mock=use_mock
        )
        
        logger.info("Transcript processor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize transcript processor: {str(e)}")
        transcript_processor = None
    
    logger.info("Component initialization completed")

# API routes

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "status": "healthy",
        "system": "PALIOS-TAEY",
        "version": "1.0.0",
        "components": {
            "memory_system": "active" if memory_system else "inactive",
            "model_registry": "active" if model_registry else "inactive",
            "task_decomposer": "active" if task_decomposer else "inactive",
            "task_executor": "active" if task_executor else "inactive",
            "model_router": "active" if model_router else "inactive",
            "transcript_processor": "active" if transcript_processor else "inactive"
        }
    })

@app.route('/leader/submit_task', methods=['POST'])
def submit_task():
    """Submit a new task with robust error handling"""
    try:
        if not task_executor:
            return jsonify({"status": "error", "message": "Task execution engine not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        # Process PURE_AI_LANGUAGE format if present
        if data.get('message_type') == 'request':
            task_data = {
                'task_id': data.get('message_id', str(uuid.uuid4())),
                'task_type': data.get('tags', ['general'])[0] if data.get('tags') else 'general',
                'content': data.get('content', {}),
                'sender_id': data.get('sender_id', 'unknown'),
                'receiver_id': data.get('receiver_id', 'system'),
                'protocol_version': data.get('protocol_version', 'unknown'),
                'created_at': datetime.now().isoformat()
            }
        else:
            # Process standard format
            task_data = {
                'task_id': data.get('task_id', str(uuid.uuid4())),
                'task_type': data.get('task_type', 'general'),
                'content': data.get('content', {}),
                'sender_id': data.get('sender_id', 'unknown'),
                'created_at': datetime.now().isoformat()
            }
        
        # Route to an appropriate model if not already assigned
        if 'assigned_model' not in task_data and model_router:
            try:
                model_id = model_router.route_task(task_data)
                task_data['assigned_model'] = model_id
            except Exception as e:
                logger.error(f"Error routing task: {str(e)}")
                # Continue without assigned model, task executor will handle it
        
        # Submit task
        task_id = task_executor.submit_task(task_data)
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "message": "Task submitted successfully"
        })
    except Exception as e:
        logger.error(f"Error submitting task: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/leader/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status with robust error handling"""
    try:
        if not task_executor:
            return jsonify({"status": "error", "message": "Task execution engine not initialized"}), 500
        
        status = task_executor.get_task_status(task_id)
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "task_status": status.get('status', 'unknown'),
            "created_at": status.get('created_at'),
            "updated_at": status.get('updated_at'),
            "result": status.get('result')
        })
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/leader/execute_task/<task_id>', methods=['POST'])
def execute_task(task_id):
    """Execute a pending task with robust error handling"""
    try:
        if not task_executor:
            return jsonify({"status": "error", "message": "Task execution engine not initialized"}), 500
        
        future = task_executor.execute_task(task_id)
        
        # Wait for completion (could make this async instead)
        result = future.result()
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "result": result
        })
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/store', methods=['POST'])
def memory_store():
    """Store item in memory with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        content = data.get("content")
        context_id = data.get("context_id")
        metadata = data.get("metadata")
        tags = data.get("tags")
        relationships = data.get("relationships")
        initial_tier = data.get("initial_tier", 1)
        
        memory_id = memory_system.store(
            content=content,
            context_id=context_id,
            metadata=metadata,
            tags=tags,
            relationships=relationships,
            initial_tier=initial_tier
        )
        
        return jsonify({
            "status": "success",
            "memory_id": memory_id
        })
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/retrieve/<memory_id>', methods=['GET'])
def memory_retrieve(memory_id):
    """Retrieve item from memory with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        context_id = request.args.get('context_id')
        
        memory_item = memory_system.retrieve(
            memory_id=memory_id,
            context_id=context_id
        )
        
        if memory_item:
            return jsonify({
                "status": "success",
                "memory_item": memory_item
            })
        else:
            return jsonify({"status": "error", "message": "Memory item not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/query', methods=['POST'])
def memory_query():
    """Query memory items with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        query_text = data.get("query_text")
        filters = data.get("filters")
        embedding = data.get("embedding")
        context_id = data.get("context_id")
        limit = data.get("limit", 10)
        include_tiers = data.get("include_tiers")
        
        memory_items = memory_system.query(
            query_text=query_text,
            filters=filters,
            embedding=embedding,
            context_id=context_id,
            limit=limit,
            include_tiers=include_tiers
        )
        
        return jsonify({
            "status": "success",
            "count": len(memory_items),
            "memory_items": memory_items
        })
    except Exception as e:
        logger.error(f"Error querying memory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcript/process', methods=['POST'])
def transcript_process():
    """Process a transcript with robust error handling"""
    try:
        if not transcript_processor:
            return jsonify({"status": "error", "message": "Transcript processor not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        transcript_data = data.get("transcript_data")
        if not transcript_data:
            return jsonify({"status": "error", "message": "No transcript data provided"}), 400
            
        format_type = data.get("format_type", "raw")
        transcript_id = data.get("transcript_id")
        metadata = data.get("metadata")
        
        processed_id = transcript_processor.process_transcript(
            transcript_data=transcript_data,
            format_type=format_type,
            transcript_id=transcript_id,
            metadata=metadata
        )
        
        return jsonify({
            "status": "success",
            "transcript_id": processed_id
        })
    except Exception as e:
        logger.error(f"Error processing transcript: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcript/analyze/<transcript_id>', methods=['GET'])
def transcript_analyze(transcript_id):
    """Analyze a transcript with robust error handling"""
    try:
        if not transcript_processor:
            return jsonify({"status": "error", "message": "Transcript processor not initialized"}), 500
        
        include_content = request.args.get('include_content', 'true').lower() == 'true'
        
        analysis = transcript_processor.analyze_transcript(
            transcript_id=transcript_id,
            include_content=include_content
        )
        
        return jsonify({
            "status": "success",
            "analysis": analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcript/convert/<transcript_id>', methods=['GET'])
def transcript_convert(transcript_id):
    """Convert a transcript to another format with robust error handling"""
    try:
        if not transcript_processor:
            return jsonify({"status": "error", "message": "Transcript processor not initialized"}), 500
        
        format_type = request.args.get('format', 'deepsearch')
        
        if format_type.lower() == 'deepsearch':
            result = transcript_processor.convert_to_deepsearch_format(transcript_id)
            return jsonify({
                "status": "success",
                "format": format_type,
                "result": result
            })
        elif format_type.lower() == 'pure_ai':
            result = transcript_processor.convert_to_pure_ai_format(transcript_id)
            return jsonify({
                "status": "success",
                "format": format_type,
                "result": result
            })
        else:
            return jsonify({"status": "error", "message": f"Unsupported format: {format_type}"}), 400
    except Exception as e:
        logger.error(f"Error converting transcript: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcript/actions/<transcript_id>', methods=['GET'])
def transcript_actions(transcript_id):
    """Extract actions from a transcript with robust error handling"""
    try:
        if not transcript_processor:
            return jsonify({"status": "error", "message": "Transcript processor not initialized"}), 500
        
        actions = transcript_processor.extract_actions(transcript_id)
        
        return jsonify({
            "status": "success",
            "count": len(actions),
            "actions": actions
        })
    except Exception as e:
        logger.error(f"Error extracting actions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models/list', methods=['GET'])
def list_models():
    """List available AI models and their capabilities with robust error handling"""
    try:
        if not model_registry:
            return jsonify({"status": "error", "message": "Model registry not initialized"}), 500
        
        task_type = request.args.get('task_type')
        min_capability = request.args.get('min_capability')
        
        if min_capability:
            try:
                min_capability = float(min_capability)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid min_capability value"}), 400
        
        models = model_registry.list_models(
            task_type=task_type,
            min_capability=min_capability
        )
        
        # Convert to format expected by API
        model_capabilities = {}
        for model in models:
            model_id = model['model_id']
            
            if task_type:
                # Only include the requested task type
                model_capabilities[model_id] = {
                    task_type: model['capability_score']
                }
            else:
                # Include all capabilities
                model_capabilities[model_id] = model['capabilities']
        
        return jsonify({
            "status": "success",
            "models": model_capabilities
        })
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models/update/<model_id>', methods=['POST'])
def update_model(model_id):
    """Update model capabilities with robust error handling"""
    try:
        if not model_registry:
            return jsonify({"status": "error", "message": "Model registry not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        capabilities = data.get('capabilities', {})
        
        # Register or update model
        success = model_registry.register_model(
            model_id=model_id,
            capabilities=capabilities,
            persist=True
        )
        
        if success:
            return jsonify({
                "status": "success",
                "model_id": model_id,
                "message": "Model capabilities updated successfully"
            })
        else:
            return jsonify({"status": "error", "message": "Failed to update model capabilities"}), 500
    except Exception as e:
        logger.error(f"Error updating model: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models/discover/<model_id>', methods=['POST'])
def discover_model_capabilities(model_id):
    """Discover model capabilities through testing with robust error handling"""
    try:
        if not model_registry:
            return jsonify({"status": "error", "message": "Model registry not initialized"}), 500
        
        data = request.json
        test_task_types = data.get('test_task_types') if data else None
        
        # Discover capabilities
        capabilities = model_registry.discover_capabilities(
            model_id=model_id,
            test_task_types=test_task_types
        )
        
        return jsonify({
            "status": "success",
            "model_id": model_id,
            "capabilities": capabilities,
            "message": "Model capabilities discovered successfully"
        })
    except Exception as e:
        logger.error(f"Error discovering model capabilities: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models/optimize', methods=['POST'])
def optimize_models():
    """Optimize model registry with robust error handling"""
    try:
        if not model_registry:
            return jsonify({"status": "error", "message": "Model registry not initialized"}), 500
        
        changes = model_registry.self_optimize()
        
        return jsonify({
            "status": "success",
            "changes": changes,
            "message": "Model registry optimized successfully"
        })
    except Exception as e:
        logger.error(f"Error optimizing model registry: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models/suggest', methods=['GET'])
def suggest_models():
    """Get model suggestions for a task type with robust error handling"""
    try:
        if not model_router:
            return jsonify({"status": "error", "message": "Model router not initialized"}), 500
        
        task_type = request.args.get('task_type', 'general')
        count = request.args.get('count', '3')
        
        try:
            count = int(count)
        except ValueError:
            count = 3
        
        suggestions = model_router.get_model_suggestions(
            task_type=task_type,
            count=count
        )
        
        return jsonify({
            "status": "success",
            "task_type": task_type,
            "suggestions": suggestions
        })
    except Exception as e:
        logger.error(f"Error getting model suggestions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "components": {
            "core": "healthy"
        }
    })

@app.route('/health', methods=['GET'])
def health_check_detailed():
    """Detailed health check endpoint with component status"""
    try:
        # Function to determine component status
        def get_component_status(component):
            if component is None:
                return "unavailable"
            try:
                # Try a basic operation to check if component is working
                if component == memory_system and memory_system:
                    # Try accessing a collection
                    memory_system._get_collection("test")
                    return "active"
                elif component == model_registry and model_registry:
                    # Try accessing model capabilities
                    if model_registry.model_capabilities:
                        return "active"
                elif component == task_decomposer and task_decomposer:
                    return task_decomposer.get_status().get("status", "inactive")
                elif component == task_executor and task_executor:
                    return task_executor.get_status().get("status", "inactive")
                elif component == model_router and model_router:
                    return model_router.get_status().get("status", "inactive")
                elif component == transcript_processor and transcript_processor:
                    return transcript_processor.get_status().get("status", "inactive")
                
                # If we couldn't verify it's active
                return "inactive"
            except Exception as e:
                logger.warning(f"Error checking component status: {str(e)}")
                return "error"
        
        # Get status for each component
        memory_status = get_component_status(memory_system)
        model_registry_status = get_component_status(model_registry)
        task_decomposer_status = get_component_status(task_decomposer)
        task_executor_status = get_component_status(task_executor)
        model_router_status = get_component_status(model_router)
        transcript_processor_status = get_component_status(transcript_processor)
        
        status = {
            "status": "healthy",
            "system": "PALIOS-TAEY",
            "components": {
                "memory_system": memory_status,
                "model_registry": model_registry_status,
                "task_decomposer": task_decomposer_status,
                "task_executor": task_executor_status,
                "model_router": model_router_status,
                "transcript_processor": transcript_processor_status
            },
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall health based on component status
        component_states = list(status["components"].values())
        if "unavailable" in component_states:
            status["status"] = "degraded"
        elif "error" in component_states:
            status["status"] = "error"
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "system": "PALIOS-TAEY",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/memory/create_context', methods=['POST'])
def create_memory_context():
    """Create a memory context with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        name = data.get("name")
        if not name:
            return jsonify({"status": "error", "message": "Context name is required"}), 400
        
        description = data.get("description", "")
        initial_memory_ids = data.get("initial_memory_ids", [])
        
        context_id = memory_system.create_context(
            name=name,
            description=description,
            initial_memory_ids=initial_memory_ids
        )
        
        return jsonify({
            "status": "success",
            "context_id": context_id
        })
    except Exception as e:
        logger.error(f"Error creating memory context: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/get_context/<context_id>', methods=['GET'])
def get_memory_context(context_id):
    """Get memory context details with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        context = memory_system.get_context(context_id)
        
        if context:
            return jsonify({
                "status": "success",
                "context": context
            })
        else:
            return jsonify({"status": "error", "message": "Context not found"}), 404
    except Exception as e:
        logger.error(f"Error getting memory context: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/add_to_context/<memory_id>/<context_id>', methods=['POST'])
def add_to_memory_context(memory_id, context_id):
    """Add a memory item to a context with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        success = memory_system.add_to_context(memory_id, context_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Memory item {memory_id} added to context {context_id}"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to add memory item to context"
            }), 500
    except Exception as e:
        logger.error(f"Error adding memory item to context: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/remove_from_context/<memory_id>/<context_id>', methods=['POST'])
def remove_from_memory_context(memory_id, context_id):
    """Remove a memory item from a context with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        success = memory_system.remove_from_context(memory_id, context_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Memory item {memory_id} removed from context {context_id}"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to remove memory item from context"
            }), 500
    except Exception as e:
        logger.error(f"Error removing memory item from context: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/update/<memory_id>', methods=['POST'])
def memory_update(memory_id):
    """Update a memory item with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        content = data.get("content")
        metadata = data.get("metadata")
        tags = data.get("tags")
        relationships = data.get("relationships")
        
        success = memory_system.update(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            tags=tags,
            relationships=relationships
        )
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Memory item {memory_id} updated successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to update memory item {memory_id}"
            }), 500
    except Exception as e:
        logger.error(f"Error updating memory item: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/memory/forget/<memory_id>', methods=['POST'])
def memory_forget(memory_id):
    """Remove a memory item with robust error handling"""
    try:
        if not memory_system:
            return jsonify({"status": "error", "message": "Memory system not initialized"}), 500
        
        data = request.json or {}
        permanent = data.get("permanent", False)
        
        success = memory_system.forget(memory_id, permanent=permanent)
        
        if success:
            action = "permanently deleted" if permanent else "archived"
            return jsonify({
                "status": "success",
                "message": f"Memory item {memory_id} {action} successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to remove memory item {memory_id}"
            }), 500
    except Exception as e:
        logger.error(f"Error removing memory item: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/task/decompose', methods=['POST'])
def decompose_task():
    """Decompose a task into subtasks with robust error handling"""
    try:
        if not task_decomposer:
            return jsonify({"status": "error", "message": "Task decomposition engine not initialized"}), 500
        
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        # Process task data
        task_data = {
            'task_id': data.get('task_id', str(uuid.uuid4())),
            'task_type': data.get('task_type', 'general'),
            'content': data.get('content', {}),
            'sender_id': data.get('sender_id', 'unknown'),
            'created_at': datetime.now().isoformat()
        }
        
        # Decompose task
        subtasks = task_decomposer.decompose_task(task_data)
        
        # Generate dependency graph
        if len(subtasks) > 1:
            dependency_graph = task_decomposer.get_dependency_graph(subtasks)
        else:
            dependency_graph = {'nodes': [], 'edges': []}
        
        return jsonify({
            "status": "success",
            "task_id": task_data['task_id'],
            "subtask_count": len(subtasks),
            "subtasks": subtasks,
            "dependency_graph": dependency_graph
        })
    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/task/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """Cancel a running task with robust error handling"""
    try:
        if not task_executor:
            return jsonify({"status": "error", "message": "Task execution engine not initialized"}), 500
        
        success = task_executor.cancel_task(task_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Task {task_id} cancelled successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to cancel task {task_id}. Task may not be active."
            }), 404
    except Exception as e:
        logger.error(f"Error cancelling task: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/task/active', methods=['GET'])
def get_active_tasks():
    """Get list of currently active tasks with robust error handling"""
    try:
        if not task_executor:
            return jsonify({"status": "error", "message": "Task execution engine not initialized"}), 500
        
        active_tasks = task_executor.get_active_tasks()
        
        return jsonify({
            "status": "success",
            "count": len(active_tasks),
            "active_tasks": active_tasks
        })
    except Exception as e:
        logger.error(f"Error getting active tasks: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/system/shutdown', methods=['POST'])
def shutdown_system():
    """Gracefully shutdown the system with robust error handling"""
    try:
        # Authenticate the request (in a real system, you would use proper authentication)
        data = request.json or {}
        shutdown_key = data.get('shutdown_key')
        
        if shutdown_key != os.environ.get('SHUTDOWN_KEY'):
            return jsonify({"status": "error", "message": "Unauthorized shutdown request"}), 401
        
        # Shutdown task executor
        if task_executor:
            try:
                task_executor.shutdown(wait=False)
                logger.info("Task executor shutdown initiated")
            except Exception as e:
                logger.error(f"Error shutting down task executor: {str(e)}")
        
        logger.info("System shutdown initiated")
        
        # Return response before shutting down
        response = jsonify({
            "status": "success",
            "message": "System shutdown initiated"
        })
        
        # Schedule shutdown after response is sent
        def shutdown_server():
            # Give a moment for the response to be sent
            time.sleep(1)
            # Shutdown the Flask server
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
        
        import threading
        threading.Thread(target=shutdown_server).start()
        
        return response
    except Exception as e:
        logger.error(f"Error during system shutdown: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/system/status', methods=['GET'])
def system_status():
    """Get detailed system status with robust error handling"""
    try:
        # Gather component statuses
        components_status = {}
        
        # Memory system status
        if memory_system:
            try:
                # Try to get a basic status
                memory_in_use = len(memory_system.cache) if hasattr(memory_system, 'cache') else "unknown"
                components_status["memory_system"] = {
                    "status": "active",
                    "mode": "mock" if getattr(memory_system, 'use_mock', False) else "normal",
                    "cache_items": memory_in_use
                }
            except Exception as e:
                components_status["memory_system"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["memory_system"] = {"status": "unavailable"}
        
        # Model registry status
        if model_registry:
            try:
                summary = model_registry.get_capability_summary()
                components_status["model_registry"] = {
                    "status": "active",
                    "model_count": summary.get('model_count', 0),
                    "task_types": summary.get('task_types', [])
                }
            except Exception as e:
                components_status["model_registry"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["model_registry"] = {"status": "unavailable"}
        
        # Task decomposer status
        if task_decomposer:
            try:
                decomposer_status = task_decomposer.get_status()
                components_status["task_decomposer"] = decomposer_status
            except Exception as e:
                components_status["task_decomposer"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["task_decomposer"] = {"status": "unavailable"}
        
        # Task executor status
        if task_executor:
            try:
                executor_status = task_executor.get_status()
                active_tasks = len(task_executor.active_tasks) if hasattr(task_executor, 'active_tasks') else "unknown"
                components_status["task_executor"] = {
                    **executor_status,
                    "active_tasks": active_tasks
                }
            except Exception as e:
                components_status["task_executor"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["task_executor"] = {"status": "unavailable"}
        
        # Model router status
        if model_router:
            try:
                router_status = model_router.get_status()
                components_status["model_router"] = router_status
            except Exception as e:
                components_status["model_router"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["model_router"] = {"status": "unavailable"}
        
        # Transcript processor status
        if transcript_processor:
            try:
                processor_status = transcript_processor.get_status()
                components_status["transcript_processor"] = processor_status
            except Exception as e:
                components_status["transcript_processor"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            components_status["transcript_processor"] = {"status": "unavailable"}
        
        # System information
        system_info = {
            "version": "1.0.0",
            "start_time": getattr(app, 'start_time', datetime.now().isoformat()),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "mock_mode": USE_MOCK,
            "python_version": sys.version
        }
        
        # Determine overall status
        component_states = [comp.get("status") for comp in components_status.values()]
        if "unavailable" in component_states:
            overall_status = "degraded"
        elif "error" in component_states:
            overall_status = "error"
        else:
            overall_status = "healthy"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": components_status,
            "system_info": system_info
        })
    except Exception as e:
        logger.error(f"Error generating system status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def main():
    """Main entry point with robust error handling"""
    try:
        parser = argparse.ArgumentParser(description="Start PALIOS-TAEY server")
        parser.add_argument("--host", help="Host to bind to")
        parser.add_argument("--port", type=int, help="Port to bind to")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument("--mock", action="store_true", help="Use mock mode")
        args = parser.parse_args()
        
        # Load configuration
        config = load_config()
        
        # Override with command line arguments
        if args.host:
            config["server"]["host"] = args.host
        if args.port:
            config["server"]["port"] = args.port
        if args.debug:
            config["server"]["debug"] = True
        if args.mock:
            config["use_mock"] = True
            global USE_MOCK
            USE_MOCK = True
        
        # Initialize components
        initialize_components(config)
        
        # Store start time for uptime tracking
        app.start_time = datetime.now().isoformat()
        
        # Start the server
        logger.info(f"Starting server on {config['server']['host']}:{config['server']['port']}")
        app.run(
            host=config["server"]["host"],
            port=config["server"]["port"],
            debug=config["server"]["debug"]
        )
    except Exception as e:
        logger.critical(f"Fatal error starting server: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    import time  # Import at top of file instead
    main()