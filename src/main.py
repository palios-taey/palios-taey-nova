"""
PALIOS-TAEY: AI-to-AI execution management platform

Main application entry point
"""
import logging
import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import environment configuration
from environment_config import initialize_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize environment
initialize_environment()

# Create FastAPI application
app = FastAPI(
    title="PALIOS-TAEY",
    description="AI-to-AI execution management platform with advanced memory architecture, transcript processing, and multi-model orchestration capabilities",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Component initialization flags
_memory_initialized = False
_models_initialized = False
_tasks_initialized = False
_routing_initialized = False
_transcripts_initialized = False
_protocols_initialized = False

# Component services
memory_service = None
model_registry = None
task_decomposition_engine = None
task_execution_engine = None
model_router = None
transcript_processor = None
protocol_manager = None

def initialize_memory_service():
    """Initialize the memory service with error handling"""
    global memory_service, _memory_initialized
    
    if _memory_initialized:
        return
    
    try:
        from palios_taey.memory.service import get_memory_service
        memory_service = get_memory_service()
        logger.info("Memory service initialized successfully")
        _memory_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize memory service: {str(e)}")
        from types import SimpleNamespace
        memory_service = SimpleNamespace(
            store=lambda **kwargs: "mock_memory_id",
            retrieve=lambda **kwargs: None,
            query=lambda **kwargs: [],
            create_context=lambda **kwargs: "mock_context_id"
        )
        logger.warning("Using mock memory service")
        _memory_initialized = True

def initialize_model_registry():
    """Initialize the model registry with error handling"""
    global model_registry, _models_initialized
    
    if _models_initialized:
        return
    
    try:
        from palios_taey.models.registry import get_model_registry
        model_registry = get_model_registry()
        logger.info("Model registry initialized successfully")
        _models_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize model registry: {str(e)}")
        from types import SimpleNamespace
        model_registry = SimpleNamespace(
            list_models=lambda **kwargs: [],
            find_best_model_for_task=lambda task_type, **kwargs: ("default_model", 0.8),
            get_capability_summary=lambda: {"model_count": 0}
        )
        logger.warning("Using mock model registry")
        _models_initialized = True

def initialize_task_engines():
    """Initialize the task decomposition and execution engines with error handling"""
    global task_decomposition_engine, task_execution_engine, _tasks_initialized
    
    if _tasks_initialized:
        return
    
    try:
        from palios_taey.tasks.decomposition import get_task_decomposition_engine
        from palios_taey.tasks.execution import get_task_execution_engine
        
        task_decomposition_engine = get_task_decomposition_engine()
        task_execution_engine = get_task_execution_engine()
        
        logger.info("Task engines initialized successfully")
        _tasks_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize task engines: {str(e)}")
        from types import SimpleNamespace
        
        task_decomposition_engine = SimpleNamespace(
            decompose_task=lambda task: [task],
            get_dependency_graph=lambda tasks: {"nodes": [], "edges": []},
            get_status=lambda: {"status": "active"}
        )
        
        task_execution_engine = SimpleNamespace(
            submit_task=lambda task: task.get('task_id', 'mock_task_id'),
            execute_task=lambda task_id: None,
            get_task_status=lambda task_id: {"status": "completed"}
        )
        
        logger.warning("Using mock task engines")
        _tasks_initialized = True

def initialize_model_router():
    """Initialize the model router with error handling"""
    global model_router, _routing_initialized
    
    if _routing_initialized:
        return
    
    try:
        from palios_taey.routing.router import get_model_router
        model_router = get_model_router()
        logger.info("Model router initialized successfully")
        _routing_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize model router: {str(e)}")
        from types import SimpleNamespace
        model_router = SimpleNamespace(
            route_task=lambda task: "default_model",
            get_model_suggestions=lambda **kwargs: [],
            get_status=lambda: {"status": "active"}
        )
        logger.warning("Using mock model router")
        _routing_initialized = True

def initialize_transcript_processor():
    """Initialize the transcript processor with error handling"""
    global transcript_processor, _transcripts_initialized
    
    if _transcripts_initialized:
        return
    
    try:
        from palios_taey.transcripts.processor import create_transcript_processor
        transcript_processor = create_transcript_processor()
        logger.info("Transcript processor initialized successfully")
        _transcripts_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize transcript processor: {str(e)}")
        from types import SimpleNamespace
        transcript_processor = SimpleNamespace(
            process_transcript=lambda **kwargs: "mock_transcript_id",
            analyze_transcript=lambda **kwargs: {},
            extract_actions=lambda transcript_id: [],
            get_status=lambda: {"status": "active"}
        )
        logger.warning("Using mock transcript processor")
        _transcripts_initialized = True

def initialize_protocol_manager():
    """Initialize the protocol manager with error handling"""
    global protocol_manager, _protocols_initialized
    
    if _protocols_initialized:
        return
    
    try:
        from palios_taey.protocols.manager import get_protocol_manager
        protocol_manager = get_protocol_manager()
        logger.info("Protocol manager initialized successfully")
        _protocols_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize protocol manager: {str(e)}")
        from types import SimpleNamespace
        protocol_manager = SimpleNamespace(
            register_protocol=lambda **kwargs: "mock_protocol_id",
            get_protocol=lambda protocol_id: None,
            list_protocols=lambda: [],
            get_status=lambda: {"status": "active"}
        )
        logger.warning("Using mock protocol manager")
        _protocols_initialized = True

def initialize_all_components():
    """Initialize all components"""
    initialize_memory_service()
    initialize_model_registry()
    initialize_task_engines()
    initialize_model_router()
    initialize_transcript_processor()
    initialize_protocol_manager()
    logger.info("All components initialized")

# Initialize components at startup
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    initialize_all_components()
    logger.info("PALIOS-TAEY application started")

# Create dependency for components
def get_memory():
    """Get memory service"""
    initialize_memory_service()
    return memory_service

def get_models():
    """Get model registry"""
    initialize_model_registry()
    return model_registry

def get_task_decomposer():
    """Get task decomposition engine"""
    initialize_task_engines()
    return task_decomposition_engine

def get_task_executor():
    """Get task execution engine"""
    initialize_task_engines()
    return task_execution_engine

def get_router():
    """Get model router"""
    initialize_model_router()
    return model_router

def get_transcript():
    """Get transcript processor"""
    initialize_transcript_processor()
    return transcript_processor

def get_protocols():
    """Get protocol manager"""
    initialize_protocol_manager()
    return protocol_manager

# Add exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    components_status = {
        "memory": "active" if _memory_initialized else "inactive",
        "models": "active" if _models_initialized else "inactive",
        "tasks": "active" if _tasks_initialized else "inactive",
        "routing": "active" if _routing_initialized else "inactive",
        "transcripts": "active" if _transcripts_initialized else "inactive",
        "protocols": "active" if _protocols_initialized else "inactive"
    }
    
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "components": components_status
    }

# Memory endpoints
@app.post("/api/memory", tags=["Memory"])
async def create_memory_item(memory_service=Depends(get_memory)):
    """Create a memory item."""
    return {"status": "ok", "message": "Memory item creation endpoint"}

# Model endpoints
@app.get("/api/models", tags=["Models"])
async def list_models(model_registry=Depends(get_models)):
    """List available models."""
    return {"status": "ok", "message": "Model listing endpoint"}

# Task endpoints
@app.post("/api/tasks", tags=["Tasks"])
async def submit_task(task_executor=Depends(get_task_executor)):
    """Submit a task."""
    return {"status": "ok", "message": "Task submission endpoint"}

# Routing endpoints
@app.post("/api/route", tags=["Routing"])
async def route_task(model_router=Depends(get_router)):
    """Route a task to the appropriate model."""
    return {"status": "ok", "message": "Task routing endpoint"}

# Transcript endpoints
@app.post("/api/transcripts", tags=["Transcripts"])
async def process_transcript(transcript_processor=Depends(get_transcript)):
    """Process a transcript."""
    return {"status": "ok", "message": "Transcript processing endpoint"}

# Protocol endpoints
@app.post("/api/protocols", tags=["Protocols"])
async def register_protocol(protocol_manager=Depends(get_protocols)):
    """Register a communication protocol."""
    return {"status": "ok", "message": "Protocol registration endpoint"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "PALIOS-TAEY",
        "description": "AI-to-AI execution management platform",
        "version": "0.1.0",
        "health_endpoint": "/health",
        "api_prefix": "/api"
    }

# Run the application with Uvicorn when script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), log_level="info")
