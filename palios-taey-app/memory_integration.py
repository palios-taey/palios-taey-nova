"""
Memory System Integration for PALIOS-TAEY

This module integrates the full memory system with Firestore support
into the skeleton application, following the incremental deployment strategy.
"""
import os
import logging
import json
from flask import Flask, jsonify, request, render_template
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import core error handling from full implementation
class PaliosTaeyError(Exception):
    """Base exception for all PALIOS-TAEY errors."""
    pass

class ValidationError(PaliosTaeyError):
    """Raised when validation fails."""
    pass

class NotFoundError(PaliosTaeyError):
    """Raised when a requested resource is not found."""
    pass

class AuthorizationError(PaliosTaeyError):
    """Raised when authorization fails."""
    pass

class ConfigurationError(PaliosTaeyError):
    """Raised when there is a configuration error."""
    pass

class ExternalServiceError(PaliosTaeyError):
    """Raised when an external service request fails."""
    pass

# Core utility functions
def generate_id(prefix: str = "") -> str:
    """Generate a unique ID."""
    import uuid
    uuid_str = str(uuid.uuid4())
    return f"{prefix}{uuid_str}" if prefix else uuid_str

def to_json(obj: any) -> str:
    """Convert an object to a JSON string."""
    def default_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)
    
    return json.dumps(obj, default=default_serializer)

def from_json(json_str: str) -> any:
    """Convert a JSON string to an object."""
    return json.loads(json_str)

# Import datetime for memory system
from datetime import datetime

# Memory tier constants
TIER_EPHEMERAL = 0    # Tier 0: Ephemeral (session only)
TIER_WORKING = 1      # Tier 1: Working (days to weeks)
TIER_REFERENCE = 2    # Tier 2: Reference (months to years)
TIER_ARCHIVAL = 3     # Tier 3: Archival (indefinite)

# Memory service implementation
class MemoryService:
    """
    Unified Memory System (UMS) for PALIOS-TAEY
    
    This is a simplified integration of the full memory service
    that connects to Firestore for persistence.
    """
    
    def __init__(self, 
                 project_id: str = None, 
                 collection_prefix: str = "", 
                 use_emulator: bool = False,
                 use_mock: bool = False,
                 cache_size: int = 1000):
        """
        Initialize the Unified Memory System
        
        Args:
            project_id: Google Cloud project ID (uses default if None)
            collection_prefix: Prefix for Firestore collections (e.g., "dev_")
            use_emulator: Whether to use the Firestore emulator
            use_mock: Whether to use mock mode (in-memory only)
            cache_size: Maximum number of items to keep in memory cache
        """
        self.collection_prefix = collection_prefix
        self.cache_size = cache_size
        self.cache = {}  # Simple in-memory cache
        
        # Check for mock mode in environment variable if not explicitly provided
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Initialize Firestore (unless in mock mode)
        self.db = None
        if not self.use_mock:
            try:
                if use_emulator:
                    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
                
                # Import Firestore
                try:
                    from google.cloud import firestore
                    if project_id:
                        self.db = firestore.Client(project=project_id)
                    else:
                        self.db = firestore.Client()
                    logger.info("Firestore client initialized successfully")
                except ImportError:
                    logger.warning("Firestore client not available, falling back to mock mode")
                    self.use_mock = True
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client: {str(e)}")
                self.use_mock = True
            
        # Initialize collections (or mock collections)
        if self.use_mock:
            logger.info("Using mock mode for Memory System")
            # Initialize mock storage
            self.memory_items = {}
            self.memory_contexts = {}
            self.memory_agents = {}
            self.memory_relationships = {}
        else:
            # Collection references
            try:
                self.memory_items_collection = self._get_collection("memory_items")
                self.memory_contexts_collection = self._get_collection("memory_contexts")
                self.memory_agents_collection = self._get_collection("memory_agents")
                self.memory_relationships_collection = self._get_collection("memory_relationships")
            except Exception as e:
                logger.error(f"Failed to initialize collections: {str(e)}")
                self.use_mock = True
                # Initialize mock storage
                self.memory_items = {}
                self.memory_contexts = {}
                self.memory_agents = {}
                self.memory_relationships = {}
        
        # Initialize ephemeral memory (Tier 0)
        self.ephemeral_memory = {}
        
        # Create initial test context
        self._ensure_default_context()
        
        logger.info(f"Memory System initialized successfully in {'mock' if self.use_mock else 'Firestore'} mode")
    
    def _get_collection(self, collection_name: str) -> any:
        """
        Get a Firestore collection reference with proper prefix
        
        Args:
            collection_name: Base collection name
            
        Returns:
            Firestore collection reference
        """
        if self.use_mock:
            # In mock mode, return the appropriate dictionary
            if collection_name == "memory_items":
                return self.memory_items
            elif collection_name == "memory_contexts":
                return self.memory_contexts
            elif collection_name == "memory_agents":
                return self.memory_agents
            elif collection_name == "memory_relationships":
                return self.memory_relationships
            else:
                # Create a new mock collection
                setattr(self, collection_name, {})
                return getattr(self, collection_name)
        else:
            # In Firestore mode, return collection reference
            if self.db is None:
                raise ValueError("Firestore client not initialized")
            
            full_name = f"{self.collection_prefix}{collection_name}"
            return self.db.collection(full_name)
    
    def _ensure_default_context(self):
        """Ensure a default context exists"""
        try:
            default_context_id = "default_context"
            if self.use_mock:
                if default_context_id not in self.memory_contexts:
                    self.memory_contexts[default_context_id] = {
                        "context_id": default_context_id,
                        "name": "Default Context",
                        "description": "Default context for PALIOS-TAEY system",
                        "active_memory_ids": [],
                        "metadata": {
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                            "creator_id": "system",
                            "is_active": True
                        }
                    }
                    logger.info("Created default memory context in mock mode")
            else:
                try:
                    doc_ref = self.memory_contexts_collection.document(default_context_id)
                    doc = doc_ref.get()
                    if not doc.exists:
                        context = {
                            "context_id": default_context_id,
                            "name": "Default Context",
                            "description": "Default context for PALIOS-TAEY system",
                            "active_memory_ids": [],
                            "metadata": {
                                "created_at": datetime.now(),
                                "updated_at": datetime.now(),
                                "creator_id": "system",
                                "is_active": True
                            }
                        }
                        doc_ref.set(context)
                        logger.info("Created default memory context in Firestore")
                except Exception as e:
                    logger.error(f"Failed to create default context in Firestore: {str(e)}")
                    # Fallback to mock context
                    self.use_mock = True
                    self.memory_contexts[default_context_id] = {
                        "context_id": default_context_id,
                        "name": "Default Context",
                        "description": "Default context for PALIOS-TAEY system",
                        "active_memory_ids": [],
                        "metadata": {
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                            "creator_id": "system",
                            "is_active": True
                        }
                    }
                    logger.warning("Created default memory context in fallback mock mode")
        except Exception as e:
            logger.error(f"Error ensuring default context: {str(e)}")
    
    def store(self, 
              content: any,
              context_id: str = None,
              metadata: dict = None,
              tags: list = None,
              relationships: list = None,
              initial_tier: int = TIER_WORKING) -> str:
        """
        Store a memory item
        
        Args:
            content: Content to store (any JSON-serializable data)
            context_id: Context identifier
            metadata: Additional metadata
            tags: List of tags for categorization
            relationships: List of relationships to other memory items
            initial_tier: Initial memory tier (0-3)
            
        Returns:
            memory_id: Identifier of the stored memory item
        """
        # Generate a unique ID if not provided in metadata
        memory_id = str(uuid.uuid4())
        if metadata is not None and 'memory_id' in metadata:
            memory_id = metadata['memory_id']
        
        # Create timestamp
        now = datetime.now()
        
        # Prepare base metadata
        base_metadata = {
            "created_at": now,
            "updated_at": now,
            "creator_id": "system",
            "access_count": 0,
            "last_accessed": now,
            "importance_score": 0.5,
            "current_tier": initial_tier,
            "ttl": None
        }
        
        # Update with values from metadata if provided
        if metadata is not None:
            if "creator_id" in metadata:
                base_metadata["creator_id"] = metadata["creator_id"]
            if "importance_score" in metadata:
                base_metadata["importance_score"] = metadata["importance_score"]
        
        # Merge with provided metadata
        if metadata is not None:
            merged_metadata = {**base_metadata, **metadata}
        else:
            merged_metadata = base_metadata
            
        # Prepare the memory item
        memory_item = {
            "memory_id": memory_id,
            "content": content,
            "metadata": merged_metadata,
            "relationships": relationships or [],
            "tags": tags or [],
        }
        
        # Store according to tier
        if initial_tier == TIER_EPHEMERAL:
            # Store in ephemeral memory (Tier 0)
            self.ephemeral_memory[memory_id] = memory_item
            
            # Also add to cache
            self._add_to_cache(memory_id, memory_item)
            
            logger.debug(f"Stored memory item {memory_id} in ephemeral tier")
        else:
            # Store in persistent storage (Tiers 1-3)
            try:
                if self.use_mock:
                    # Store in mock storage
                    self.memory_items[memory_id] = memory_item
                    
                    # Add to context if provided
                    if context_id:
                        self._add_to_context(memory_id, context_id)
                    
                    # Add to cache
                    self._add_to_cache(memory_id, memory_item)
                    
                    logger.debug(f"Stored memory item {memory_id} in mock storage, tier {initial_tier}")
                else:
                    # Store in Firestore
                    self.memory_items_collection.document(memory_id).set(memory_item)
                    
                    # Add to context if provided
                    if context_id:
                        self._add_to_context(memory_id, context_id)
                    
                    # Add to cache
                    self._add_to_cache(memory_id, memory_item)
                    
                    logger.info(f"Stored memory item {memory_id} in tier {initial_tier}")
            except Exception as e:
                # Fallback to ephemeral storage in case of error
                logger.error(f"Failed to store memory item {memory_id} in persistent storage: {str(e)}")
                logger.warning(f"Falling back to ephemeral storage for {memory_id}")
                
                # Store in ephemeral memory as fallback
                self.ephemeral_memory[memory_id] = memory_item
                self._add_to_cache(memory_id, memory_item)
                
                # Re-raise exception in non-mock mode for visibility
                if not self.use_mock:
                    raise
        
        return memory_id
    
    def retrieve(self, 
                memory_id: str, 
                context_id: str = None) -> dict:
        """
        Retrieve a specific memory item
        
        Args:
            memory_id: Identifier of the memory item
            context_id: Optional context identifier
            
        Returns:
            Memory item data or None if not found
        """
        # Check cache first
        if memory_id in self.cache:
            logger.debug(f"Cache hit for memory item {memory_id}")
            memory_item = self.cache[memory_id]
            
            # Update access metadata
            self._update_access_metadata(memory_id, memory_item)
            
            return memory_item
        
        # Check ephemeral memory
        if memory_id in self.ephemeral_memory:
            logger.debug(f"Ephemeral hit for memory item {memory_id}")
            memory_item = self.ephemeral_memory[memory_id]
            
            # Update access metadata
            self._update_access_metadata(memory_id, memory_item)
            
            return memory_item
        
        # Retrieve from persistent storage
        try:
            if self.use_mock:
                # Check mock storage
                if memory_id in self.memory_items:
                    memory_item = self.memory_items[memory_id]
                    
                    # Add to cache
                    self._add_to_cache(memory_id, memory_item)
                    
                    # Update access metadata
                    self._update_access_metadata(memory_id, memory_item)
                    
                    logger.debug(f"Retrieved memory item {memory_id} from mock storage")
                    return memory_item
                else:
                    logger.warning(f"Memory item {memory_id} not found in mock storage")
                    return None
            else:
                # Retrieve from Firestore
                doc_ref = self.memory_items_collection.document(memory_id)
                doc = doc_ref.get()
                
                if not doc.exists:
                    logger.warning(f"Memory item {memory_id} not found in Firestore")
                    return None
                
                memory_item = doc.to_dict()
                
                # Add to cache
                self._add_to_cache(memory_id, memory_item)
                
                # Update access metadata
                self._update_access_metadata(memory_id, memory_item)
                
                logger.debug(f"Retrieved memory item {memory_id} from Firestore")
                return memory_item
        except Exception as e:
            logger.error(f"Failed to retrieve memory item {memory_id}: {str(e)}")
            return None
    
    def query(self,
             query_text: str = None,
             filters: dict = None,
             context_id: str = None,
             limit: int = 10,
             include_tiers: list = None) -> list:
        """
        Query memory items 
        
        Args:
            query_text: Text to search for
            filters: Dictionary of field filters
            context_id: Context to query within
            limit: Maximum number of results
            include_tiers: List of tiers to include [0,1,2,3]
            
        Returns:
            List of memory items matching query
        """
        if include_tiers is None:
            include_tiers = [TIER_EPHEMERAL, TIER_WORKING, TIER_REFERENCE, TIER_ARCHIVAL]
        
        results = []
        
        # Simple implementation for verification purposes
        if self.use_mock:
            # Search mock storage
            for memory_id, item in self.memory_items.items():
                tier = item.get("metadata", {}).get("current_tier", TIER_WORKING)
                
                # Skip if tier not included
                if tier not in include_tiers:
                    continue
                
                # Apply simple filtering
                if filters:
                    skip = False
                    for key, value in filters.items():
                        # Handle nested fields with dot notation
                        keys = key.split('.')
                        item_value = item
                        for k in keys:
                            if isinstance(item_value, dict) and k in item_value:
                                item_value = item_value[k]
                            else:
                                item_value = None
                                break
                        
                        if item_value != value:
                            skip = True
                            break
                    
                    if skip:
                        continue
                
                # Simple text search
                if query_text:
                    content_str = str(item.get("content", ""))
                    if query_text.lower() not in content_str.lower():
                        continue
                
                results.append(item)
                
                # Limit results
                if len(results) >= limit:
                    break
        else:
            try:
                # Search Firestore
                query = self.memory_items_collection
                
                # Add tier filter
                if len(include_tiers) < 4:  # If not all tiers
                    query = query.where("metadata.current_tier", "in", include_tiers)
                
                # Add other filters
                if filters:
                    for field, value in filters.items():
                        query = query.where(field, "==", value)
                
                # Execute query with limit
                docs = query.limit(limit).stream()
                
                # Process results
                for doc in docs:
                    item = doc.to_dict()
                    
                    # Simple text search
                    if query_text:
                        content_str = str(item.get("content", ""))
                        if query_text.lower() not in content_str.lower():
                            continue
                    
                    results.append(item)
            except Exception as e:
                logger.error(f"Failed to query memory items: {str(e)}")
        
        return results
    
    def _add_to_cache(self, memory_id: str, memory_item: dict) -> None:
        """Add a memory item to the cache"""
        # Add to cache
        self.cache[memory_id] = memory_item
        
        # Trim cache if needed
        if len(self.cache) > self.cache_size:
            # Remove least recently used item
            lru_id = min(self.cache.keys(), 
                        key=lambda x: self.cache[x].get("metadata", {}).get("last_accessed", 
                                                                        datetime.min))
            del self.cache[lru_id]
    
    def _update_access_metadata(self, memory_id: str, memory_item: dict) -> None:
        """Update access metadata for a memory item"""
        now = datetime.now()
        
        # Update in the object
        if "metadata" not in memory_item:
            memory_item["metadata"] = {}
        
        memory_item["metadata"]["last_accessed"] = now
        memory_item["metadata"]["access_count"] = memory_item["metadata"].get("access_count", 0) + 1
    
    def _add_to_context(self, memory_id: str, context_id: str) -> bool:
        """
        Add a memory item to a context
        
        Args:
            memory_id: Memory item identifier
            context_id: Context identifier
            
        Returns:
            Whether the operation was successful
        """
        try:
            if self.use_mock:
                # Get context from mock storage
                if context_id in self.memory_contexts:
                    context_data = self.memory_contexts[context_id]
                    active_memory_ids = context_data.get("active_memory_ids", [])
                    
                    # Add the memory ID if not already present
                    if memory_id not in active_memory_ids:
                        active_memory_ids.append(memory_id)
                        
                        # Update the context
                        context_data["active_memory_ids"] = active_memory_ids
                        context_data["metadata"]["updated_at"] = datetime.now()
                        
                        logger.debug(f"Added memory item {memory_id} to context {context_id} in mock storage")
                    
                    return True
                else:
                    logger.warning(f"Memory context {context_id} not found in mock storage")
                    return False
            else:
                # Get the context from Firestore
                context_ref = self.memory_contexts_collection.document(context_id)
                context = context_ref.get()
                
                if not context.exists:
                    logger.warning(f"Memory context {context_id} not found in Firestore")
                    return False
                
                context_data = context.to_dict()
                active_memory_ids = context_data.get("active_memory_ids", [])
                
                # Add the memory ID if not already present
                if memory_id not in active_memory_ids:
                    active_memory_ids.append(memory_id)
                    
                    # Update the context
                    context_ref.update({
                        "active_memory_ids": active_memory_ids,
                        "metadata.updated_at": datetime.now()
                    })
                    
                    logger.debug(f"Added memory item {memory_id} to context {context_id} in Firestore")
                
                return True
        except Exception as e:
            logger.error(f"Failed to add memory item to context: {str(e)}")
            return False

# Integration with Flask application
def create_app():
    """Create and configure the Flask application with memory system integration"""
    app = Flask(__name__, template_folder="templates")
    
    # Initialize memory service
    project_id = os.environ.get("PROJECT_ID", "palios-taey-dev")
    collection_prefix = os.environ.get("COLLECTION_PREFIX", "")
    use_emulator = os.environ.get("USE_FIRESTORE_EMULATOR", "False").lower() == "true"
    use_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
    
    memory_service = MemoryService(
        project_id=project_id,
        collection_prefix=collection_prefix,
        use_emulator=use_emulator,
        use_mock=use_mock
    )
    
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
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        # Check if memory service is working
        try:
            memory_status = "healthy"
            memory_mode = "mock" if memory_service.use_mock else "firestore"
        except Exception as e:
            memory_status = f"error: {str(e)}"
            memory_mode = "unknown"
        
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "components": {
                "memory": {
                    "status": memory_status,
                    "mode": memory_mode
                }
            }
        })
    
    # Memory API endpoints
    @app.route('/api/memory/store', methods=['POST'])
    @require_api_key
    def memory_store():
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            content = data.get("content")
            context_id = data.get("context_id")
            metadata = data.get("metadata")
            tags = data.get("tags")
            relationships = data.get("relationships")
            
            memory_id = memory_service.store(
                content=content,
                context_id=context_id,
                metadata=metadata,
                tags=tags,
                relationships=relationships
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
        try:
            context_id = request.args.get('context_id')
            
            memory_item = memory_service.retrieve(
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
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            query_text = data.get("query_text")
            filters = data.get("filters")
            context_id = data.get("context_id")
            limit = data.get("limit", 10)
            
            results = memory_service.query(
                query_text=query_text,
                filters=filters,
                context_id=context_id,
                limit=limit
            )
            
            return jsonify({
                "results": results,
                "count": len(results),
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Error in memory_query: {str(e)}")
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
    
    return app

# Application factory pattern
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
