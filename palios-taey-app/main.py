from flask import Flask, jsonify, request, render_template
import os
from auth import require_api_key
from memory_system import MemorySystem
from model_integration import ModelRegistry, ClaudeModel, GrokModel
from router import TaskRouter

app = Flask(__name__)

# Initialize components
project_id = os.environ.get('PROJECT_ID', 'palios-taey-dev')
memory_system = MemorySystem(project_id=project_id)

# Initialize model registry
model_registry = ModelRegistry()
model_registry.register_model(ClaudeModel())
model_registry.register_model(GrokModel())

# Initialize task router
task_router = TaskRouter(model_registry)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": "1.0.0"})

@app.route('/api/models', methods=['GET'])
@require_api_key
def list_models():
    models = model_registry.list_models()
    return jsonify({"models": models})

@app.route('/api/tasks', methods=['POST'])
@require_api_key
def execute_task():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    if 'description' not in data:
        return jsonify({"error": "Task description required"}), 400
    
    # Route task to appropriate model
    result = task_router.route_task(
        task_description=data['description'],
        model_id=data.get('model_id')
    )
    
    # Store task in memory system
    memory_id = memory_system.store_memory(
        content=data['description'],
        context_id=data.get('context_id', 'default_context'),
        tier='working',
        metadata={
            "type": "task",
            "model_used": result.get("result", {}).get("model_used", "unknown"),
            "capability": result.get("analysis", {}).get("primary_capability", "unknown")
        }
    )
    
    # Add memory ID to result
    result["memory_id"] = memory_id
    
    return jsonify(result)

@app.route('/api/memory', methods=['GET'])
@require_api_key
def list_memories():
    context_id = request.args.get('context_id', 'default_context')
    limit = int(request.args.get('limit', 10))
    memories = memory_system.list_memories(context_id=context_id, limit=limit)
    return jsonify({"memories": memories})

@app.route('/api/memory', methods=['POST'])
@require_api_key
def store_memory():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    if 'content' not in data:
        return jsonify({"error": "Memory content required"}), 400
    
    context_id = data.get('context_id', 'default_context')
    tier = data.get('tier', 'working')
    metadata = data.get('metadata', {})
    
    memory_id = memory_system.store_memory(
        content=data['content'],
        context_id=context_id,
        tier=tier,
        metadata=metadata
    )
    
    return jsonify({
        "memory_id": memory_id,
        "status": "success"
    })

@app.route('/api/memory/<memory_id>', methods=['GET'])
@require_api_key
def get_memory(memory_id):
    memory = memory_system.retrieve_memory(memory_id)
    if memory is None:
        return jsonify({"error": "Memory not found"}), 404
    
    return jsonify(memory)

@app.route('/api/transcripts', methods=['POST'])
@require_api_key
def process_transcript():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "Transcript text required"}), 400
    
    # Simple processing for now
    word_count = len(data['text'].split())
    
    # Store transcript in memory system
    memory_id = memory_system.store_memory(
        content=data['text'],
        context_id=data.get('context_id', 'default_context'),
        tier='reference',
        metadata={"type": "transcript", "word_count": word_count}
    )
    
    return jsonify({
        "processed": True,
        "word_count": word_count,
        "memory_id": memory_id,
        "status": "success"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
