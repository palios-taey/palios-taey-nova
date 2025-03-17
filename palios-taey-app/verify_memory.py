"""
Memory System Verification Script

This script tests the deployed Memory System functionality.
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

# Keep track of context and memory IDs for cleanup
test_context_id = None
test_memory_ids = []

def test_health():
    """Test the health endpoint"""
    url = f"{API_URL}/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Health check: {data['status']}")
        if 'components' in data and 'memory' in data['components']:
            memory = data['components']['memory']
            logger.info(f"Memory status: {memory['status']}")
            logger.info(f"Memory mode: {memory['mode']}")
        
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def test_create_context():
    """Test creating a memory context"""
    global test_context_id
    
    url = f"{API_URL}/api/memory/create_context"
    headers = {"X-API-Key": API_KEY}
    
    context_name = f"Test Context {uuid.uuid4()}"
    
    payload = {
        "name": context_name,
        "description": "Context created for verification testing"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        test_context_id = data['context_id']
        logger.info(f"Created test context: {test_context_id}")
        return test_context_id
    except Exception as e:
        logger.error(f"Context creation failed: {str(e)}")
        return None

def test_get_context(context_id):
    """Test retrieving a memory context"""
    url = f"{API_URL}/api/memory/get_context/{context_id}"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        context = data['context']
        logger.info(f"Retrieved context: {context_id}")
        logger.info(f"Context name: {context['name']}")
        
        return True
    except Exception as e:
        logger.error(f"Context retrieval failed: {str(e)}")
        return False

def test_memory_store(context_id=None):
    """Test storing a memory item"""
    global test_memory_ids
    
    url = f"{API_URL}/api/memory/store"
    headers = {"X-API-Key": API_KEY}
    
    test_content = {
        "message": "Test memory item",
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "content": test_content,
        "context_id": context_id,
        "metadata": {
            "test_id": str(uuid.uuid4()),
            "test_type": "memory_store"
        },
        "tags": ["test", "memory", "verification"]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        memory_id = data['memory_id']
        test_memory_ids.append(memory_id)
        logger.info(f"Memory stored with ID: {memory_id}")
        return memory_id
    except Exception as e:
        logger.error(f"Memory store failed: {str(e)}")
        return None

def test_memory_retrieve(memory_id):
    """Test retrieving a memory item"""
    url = f"{API_URL}/api/memory/retrieve/{memory_id}"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        memory_item = data['memory_item']
        logger.info(f"Retrieved memory item: {memory_id}")
        logger.info(f"Content: {memory_item['content']}")
        logger.info(f"Tags: {memory_item['tags']}")
        
        return True
    except Exception as e:
        logger.error(f"Memory retrieve failed: {str(e)}")
        return False

def test_memory_query(tag="test"):
    """Test querying memory items"""
    url = f"{API_URL}/api/memory/query"
    headers = {"X-API-Key": API_KEY}
    
    # Query by tag
    payload = {
        "filters": {
            "tags": tag
        },
        "limit": 5
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Memory query returned {data['count']} results")
        return data['count']
    except Exception as e:
        logger.error(f"Memory query failed: {str(e)}")
        return 0

def run_all_tests():
    """Run all verification tests"""
    logger.info("Starting Memory System verification tests")
    
    # Test 1: Health check
    if not test_health():
        logger.error("Health check failed - aborting verification")
        return False
    
    # Test 2: Create context
    context_id = test_create_context()
    if not context_id:
        logger.error("Context creation failed - continuing with tests")
    
    # Test 3: Get context
    if context_id and not test_get_context(context_id):
        logger.error("Context retrieval failed - continuing with tests")
    
    # Test 4: Store memory
    memory_id = test_memory_store(context_id)
    if not memory_id:
        logger.error("Memory store failed - aborting verification")
        return False
    
    # Test 5: Retrieve memory
    if not test_memory_retrieve(memory_id):
        logger.error("Memory retrieve failed - aborting verification")
        return False
    
    # Test 6: Query memory
    result_count = test_memory_query()
    if result_count == 0:
        logger.warning("Memory query returned no results - possible issue")
    
    logger.info("All memory system verification tests completed successfully!")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
