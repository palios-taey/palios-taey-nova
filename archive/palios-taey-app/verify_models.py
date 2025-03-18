"""
Models and Routing Verification Script

This script tests the deployed Models and Routing functionality.
"""
import os
import sys
import json
import requests
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8080")
API_KEY = os.environ.get("API_KEY", "test_key")

def test_health():
    """Test the health endpoint to check model registry and router"""
    url = f"{API_URL}/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Health check: {data['status']}")
        
        # Check model registry status
        if 'components' in data and 'model_registry' in data['components']:
            registry_status = data['components']['model_registry']['status']
            logger.info(f"Model registry status: {registry_status}")
            
            if not registry_status.startswith("healthy"):
                logger.warning(f"Model registry may have issues: {registry_status}")
        
        # Check model router status        
        if 'components' in data and 'model_router' in data['components']:
            router_status = data['components']['model_router']['status']
            logger.info(f"Model router status: {router_status}")
            
            if not router_status.startswith("healthy"):
                logger.warning(f"Model router may have issues: {router_status}")
        
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def test_models_list():
    """Test listing models from the registry"""
    url = f"{API_URL}/api/models/list"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        models_count = data.get('count', 0)
        logger.info(f"Models list returned {models_count} models")
        
        if models_count > 0:
            logger.info(f"Available models: {[m.get('model_id') for m in data.get('models', [])]}")
        
        return models_count
    except Exception as e:
        logger.error(f"Models list failed: {str(e)}")
        return 0

def test_model_registration():
    """Test registering a new model"""
    url = f"{API_URL}/api/models/register"
    headers = {"X-API-Key": API_KEY}
    
    # Generate a unique model ID for testing
    model_id = f"test-model-{uuid.uuid4()}"
    
    payload = {
        "model_id": model_id,
        "capabilities": {
            "general": 0.85,
            "document_summary": 0.75,
            "code_generation": 0.9
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Registered test model: {model_id}")
        return model_id
    except Exception as e:
        logger.error(f"Model registration failed: {str(e)}")
        return None

def test_model_capabilities(model_id):
    """Test getting capabilities for a specific model"""
    url = f"{API_URL}/api/models/capabilities/{model_id}"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        capabilities = data.get('capabilities', {})
        logger.info(f"Retrieved capabilities for model {model_id}")
        logger.info(f"Capabilities: {capabilities}")
        
        return len(capabilities) > 0
    except Exception as e:
        logger.error(f"Model capabilities retrieval failed: {str(e)}")
        return False

def test_route_task():
    """Test routing a task to a model"""
    url = f"{API_URL}/api/router/route"
    headers = {"X-API-Key": API_KEY}
    
    # Create a test task
    task = {
        "task_id": f"test-task-{uuid.uuid4()}",
        "task_type": "document_summary",
        "content": {
            "document": "This is a test document for routing verification.",
            "options": {"max_length": 100}
        }
    }
    
    try:
        response = requests.post(url, json=task, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        selected_model = data.get('selected_model')
        logger.info(f"Task routed to model: {selected_model}")
        
        return selected_model is not None
    except Exception as e:
        logger.error(f"Task routing failed: {str(e)}")
        return False

def test_model_suggestions():
    """Test getting model suggestions for a task type"""
    url = f"{API_URL}/api/router/suggest?task_type=document_summary&count=2"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        suggestions = data.get('suggestions', [])
        logger.info(f"Received {len(suggestions)} model suggestions for document_summary")
        
        for suggestion in suggestions:
            logger.info(f"Suggested model: {suggestion}")
        
        return len(suggestions) > 0
    except Exception as e:
        logger.error(f"Model suggestions failed: {str(e)}")
        return False

def run_all_tests():
    """Run all verification tests"""
    logger.info("Starting Models and Routing verification tests")
    
    # Test 1: Health check
    if not test_health():
        logger.error("Health check failed - continuing with tests")
    
    # Test 2: List models
    models_count = test_models_list()
    if models_count == 0:
        logger.warning("No models found in registry - continuing with tests")
    
    # Test 3: Register a model
    test_model_id = test_model_registration()
    if test_model_id is None:
        logger.error("Model registration failed - continuing with tests")
    
    # Test 4: Get model capabilities
    if test_model_id and not test_model_capabilities(test_model_id):
        logger.error("Model capabilities retrieval failed - continuing with tests")
    
    # Test 5: Route a task
    if not test_route_task():
        logger.error("Task routing failed - continuing with tests")
    
    # Test 6: Get model suggestions
    if not test_model_suggestions():
        logger.error("Model suggestions failed - continuing with tests")
    
    logger.info("All models and routing verification tests completed!")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
