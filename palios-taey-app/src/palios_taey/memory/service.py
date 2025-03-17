"""
Unified Memory System (UMS) for PALIOS-TAEY

This module implements the Unified Memory System service, providing a multi-tier
memory architecture for storing and retrieving information with consistent access
patterns regardless of persistence requirements.
"""

import os
import uuid
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Memory tier constants
TIER_EPHEMERAL = 0    # Tier 0: Ephemeral (session only)
TIER_WORKING = 1      # Tier 1: Working (days to weeks)
TIER_REFERENCE = 2    # Tier 2: Reference (months to years)
TIER_ARCHIVAL = 3     # Tier 3: Archival (indefinite)

# Default TTL values (in days)
DEFAULT_TTL = {
    TIER_EPHEMERAL: 0.5,  # 12 hours
    TIER_WORKING: 14,     # 2 weeks
    TIER_REFERENCE: 180,  # 6 months
    TIER_ARCHIVAL: None   # Indefinite
}

# Default importance thresholds for tier promotion/demotion
IMPORTANCE_THRESHOLDS = {
    "t0_to_t1": 0.3,  # Threshold to move from Tier 0 to Tier 1
    "t1_to_t2": 0.6,  # Threshold to move from Tier 1 to Tier 2
    "t2_to_t3": 0.2   # Threshold to move from Tier 2 to Tier 3 (low importance archive)
}

class UnifiedMemorySystem:
    """
    Unified Memory System (UMS) for PALIOS-TAEY
    
    A multi-tier memory service that provides consistent access patterns
    across different persistence requirements.
    """
    
    def __init__(self, 
                 project_id: Optional[str] = None, 
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
                
                # Lazy import to avoid dependency when in mock mode
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
                            "created_at": datetime.datetime.now(),
                            "updated_at": datetime.datetime.now(),
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
                                "created_at": datetime.datetime.now(),
                                "updated_at": datetime.datetime.now(),
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
                            "created_at": datetime.datetime.now(),
                            "updated_at": datetime.datetime.now(),
                            "creator_id": "system",
                            "is_active": True
                        }
                    }
                    logger.info("Created default memory context in fallback mock mode")
        except Exception as e:
            logger.error(f"Error ensuring default context: {str(e)}")
    
    def _get_collection(self, collection_name: str) -> Any:
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
    
    def store(self, 
              content: Any,
              context_id: Optional[str] = None,
              metadata: Dict[str, Any] = None,
              tags: List[str] = None,
              relationships: List[Dict[str, Any]] = None,
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
        now = datetime.datetime.now()
        
        # Prepare base metadata
        base_metadata = {
            "created_at": now,
            "updated_at": now,
            "creator_id": "system",  # Default value
            "access_count": 0,
            "last_accessed": now,
            "importance_score": 0.5,  # Default value
            "current_tier": initial_tier,
            "ttl": None
        }
        
        # Update with values from metadata if provided
        if metadata is not None:
            if "creator_id" in metadata:
                base_metadata["creator_id"] = metadata["creator_id"]
            if "importance_score" in metadata:
                base_metadata["importance_score"] = metadata["importance_score"]
        
        # Calculate TTL if applicable
        if initial_tier in DEFAULT_TTL and DEFAULT_TTL[initial_tier] is not None:
            ttl_days = DEFAULT_TTL[initial_tier]
            if metadata is not None and "ttl_days" in metadata:
                ttl_days = metadata["ttl_days"]
            base_metadata["ttl"] = now + datetime.timedelta(days=ttl_days)
        
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
            "embeddings": {}  # Will be populated separately if needed
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
                    
                    # Process relationships
                    if relationships:
                        self._store_relationships(memory_id, relationships)
                    
                    # Add to cache
                    self._add_to_cache(memory_id, memory_item)
                    
                    logger.debug(f"Stored memory item {memory_id} in mock storage, tier {initial_tier}")
                else:
                    # Store in Firestore
                    self.memory_items_collection.document(memory_id).set(memory_item)
                    
                    # Add to context if provided
                    if context_id:
                        self._add_to_context(memory_id, context_id)
                    
                    # Process relationships
                    if relationships:
                        self._store_relationships(memory_id, relationships)
                    
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
                context_id: str = None) -> Optional[Dict[str, Any]]:
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
             filters: Dict[str, Any] = None,
             embedding: List[float] = None,
             context_id: str = None,
             limit: int = 10,
             include_tiers: List[int] = None) -> List[Dict[str, Any]]:
        """
        Query memory items across tiers
        
        Args:
            query_text: Text to search for
            filters: Dictionary of field filters
            embedding: Vector embedding for similarity search
            context_id: Context to query within
            limit: Maximum number of results
            include_tiers: List of tiers to include [0,1,2,3]
            
        Returns:
            List of memory items matching query
        """
        if include_tiers is None:
            include_tiers = [TIER_EPHEMERAL, TIER_WORKING, TIER_REFERENCE, TIER_ARCHIVAL]
        
        results = []
        
        # Search ephemeral memory (Tier 0) if included
        if TIER_EPHEMERAL in include_tiers:
            for memory_id, item in self.ephemeral_memory.items():
                if self._matches_query(item, query_text, filters, context_id):
                    results.append(item)
                    
                    # Update access metadata
                    self._update_access_metadata(memory_id, item)
        
        # Search persistent storage (Tiers 1-3)
        try:
            if self.use_mock:
                # Search mock storage
                for memory_id, item in self.memory_items.items():
                    tier = item.get("metadata", {}).get("current_tier", TIER_WORKING)
                    
                    # Skip if tier not included
                    if tier not in include_tiers:
                        continue
                    
                    # Apply query filters
                    if self._matches_query(item, query_text, filters, context_id):
                        results.append(item)
                        
                        # Update access metadata
                        self._update_access_metadata(memory_id, item)
            else:
                # Search Firestore
                firestore_tiers = [t for t in include_tiers if t != TIER_EPHEMERAL]
                if firestore_tiers:
                    # Start with base query
                    query = self.memory_items_collection
                    
                    # Add tier filter
                    if len(firestore_tiers) < 3:  # If not all tiers
                        query = query.where("metadata.current_tier", "in", firestore_tiers)
                    
                    # Add context filter if provided
                    if context_id:
                        # We need to approach this differently - query the context first
                        context_doc = self.memory_contexts_collection.document(context_id).get()
                        if context_doc.exists:
                            context = context_doc.to_dict()
                            if context and 'active_memory_ids' in context:
                                # Only query for memory IDs in this context
                                memory_ids = context['active_memory_ids']
                                if memory_ids:
                                    # Firestore has a limit on "in" queries
                                    chunks = [memory_ids[i:i+10] for i in range(0, len(memory_ids), 10)]
                                    for chunk in chunks:
                                        chunk_query = query.where("memory_id", "in", chunk)
                                        
                                        # Apply text search if provided
                                        chunk_docs = chunk_query.limit(limit).stream()
                                        for doc in chunk_docs:
                                            item = doc.to_dict()
                                            if query_text and not self._text_matches(item, query_text):
                                                continue
                                            
                                            # Apply additional filters if provided
                                            if filters and not self._apply_filters(item, filters):
                                                continue
                                            
                                            results.append(item)
                                            
                                            # Add to cache
                                            self._add_to_cache(item["memory_id"], item)
                                            
                                            # Update access metadata
                                            self._update_access_metadata(item["memory_id"], item)
                    
                    # If no context filter or no memory IDs in context, use normal query
                    if not context_id or not results:
                        # Add other filters
                        if filters:
                            for field, value in filters.items():
                                if isinstance(value, dict) and 'operator' in value:
                                    # Complex filter with operator
                                    op = value['operator']
                                    filter_value = value['value']
                                    query = query.where(field, op, filter_value)
                                else:
                                    # Simple equality filter
                                    query = query.where(field, "==", value)
                        
                        # Execute query
                        docs = query.limit(limit).stream()
                        
                        for doc in docs:
                            item = doc.to_dict()
                            
                            # Apply text search filter if provided
                            if query_text and not self._text_matches(item, query_text):
                                continue
                            
                            results.append(item)
                            
                            # Add to cache
                            self._add_to_cache(item["memory_id"], item)
                            
                            # Update access metadata
                            self._update_access_metadata(item["memory_id"], item)
        except Exception as e:
            logger.error(f"Failed to query memory items: {str(e)}")
        
        # Perform embedding-based search if requested
        if embedding is not None and results:
            # This implementation would be replaced with a real vector similarity search
            # For now, we'll just add a random similarity score for demonstration
            for item in results:
                item['similarity_score'] = random.random()
            
            # Sort by similarity
            results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
        # Sort by relevance/importance and limit results
        results = sorted(results, 
                        key=lambda x: x.get("metadata", {}).get("importance_score", 0), 
                        reverse=True)[:limit]
        
        return results
    
    def update(self,
              memory_id: str,
              content: Any = None,
              metadata: Dict[str, Any] = None,
              tags: List[str] = None,
              relationships: List[Dict[str, Any]] = None) -> bool:
        """
        Update a memory item
        
        Args:
            memory_id: Identifier of the memory item
            content: New content (if None, content is not updated)
            metadata: Metadata fields to update
            tags: New tags (if None, tags are not updated)
            relationships: New relationships (if None, relationships are not updated)
            
        Returns:
            Whether the update was successful
        """
        # Retrieve the current item
        current_item = self.retrieve(memory_id)
        if not current_item:
            logger.warning(f"Cannot update memory item {memory_id} - not found")
            return False
        
        # Prepare update data
        update_data = {}
        
        # Update content if provided
        if content is not None:
            update_data["content"] = content
        
        # Update metadata if provided
        if metadata:
            if "metadata" not in update_data:
                update_data["metadata"] = current_item.get("metadata", {}).copy()
            
            for key, value in metadata.items():
                update_data["metadata"][key] = value
            
            # Always update updated_at timestamp
            update_data["metadata"]["updated_at"] = datetime.datetime.now()
        
        # Update tags if provided
        if tags is not None:
            update_data["tags"] = tags
        
        # Update relationships if provided
        if relationships is not None:
            update_data["relationships"] = relationships
            # Process relationships
            self._store_relationships(memory_id, relationships)
        
        # Apply the update based on tier
        tier = current_item.get("metadata", {}).get("current_tier", TIER_WORKING)
        
        if tier == TIER_EPHEMERAL:
            # Update in ephemeral memory
            if not update_data:
                return True  # Nothing to update
            
            # Update fields
            for key, value in update_data.items():
                if key == "metadata":
                    # Merge metadata
                    self.ephemeral_memory[memory_id]["metadata"].update(value)
                else:
                    # Replace other fields
                    self.ephemeral_memory[memory_id][key] = value
            
            # Update cache
            if memory_id in self.cache:
                for key, value in update_data.items():
                    if key == "metadata":
                        # Merge metadata
                        self.cache[memory_id]["metadata"].update(value)
                    else:
                        # Replace other fields
                        self.cache[memory_id][key] = value
            
            return True
        else:
            # Update in persistent storage
            try:
                if not update_data:
                    return True  # Nothing to update
                
                if self.use_mock:
                    # Update in mock storage
                    for key, value in update_data.items():
                        if key == "metadata":
                            # Merge metadata
                            self.memory_items[memory_id]["metadata"].update(value)
                        else:
                            # Replace other fields
                            self.memory_items[memory_id][key] = value
                    
                    # Update cache if present
                    if memory_id in self.cache:
                        for key, value in update_data.items():
                            if key == "metadata":
                                # Merge metadata
                                self.cache[memory_id]["metadata"].update(value)
                            else:
                                # Replace other fields
                                self.cache[memory_id][key] = value
                    
                    logger.debug(f"Updated memory item {memory_id} in mock storage")
                else:
                    # Update in Firestore
                    doc_ref = self.memory_items_collection.document(memory_id)
                    doc_ref.update(update_data)
                    
                    # Update cache if present
                    if memory_id in self.cache:
                        for key, value in update_data.items():
                            if key == "metadata":
                                # Merge metadata
                                self.cache[memory_id]["metadata"].update(value)
                            else:
                                # Replace other fields
                                self.cache[memory_id][key] = value
                    
                    logger.debug(f"Updated memory item {memory_id} in Firestore")
                
                return True
            except Exception as e:
                logger.error(f"Failed to update memory item {memory_id}: {str(e)}")
                return False
    
    def forget(self,
              memory_id: str,
              permanent: bool = False) -> bool:
        """
        Remove a memory item
        
        Args:
            memory_id: Identifier of the memory item
            permanent: Whether to permanently delete (True) or just archive (False)
            
        Returns:
            Whether the operation was successful
        """
        # Retrieve the current item
        current_item = self.retrieve(memory_id)
        if not current_item:
            logger.warning(f"Cannot forget memory item {memory_id} - not found")
            return False
        
        tier = current_item.get("metadata", {}).get("current_tier", TIER_WORKING)
        
        if permanent:
            # Permanently delete
            try:
                # Remove from cache
                if memory_id in self.cache:
                    del self.cache[memory_id]
                
                # Remove from ephemeral memory
                if memory_id in self.ephemeral_memory:
                    del self.ephemeral_memory[memory_id]
                
                # Remove from persistent storage
                if tier > TIER_EPHEMERAL:
                    if self.use_mock:
                        # Remove from mock storage
                        if memory_id in self.memory_items:
                            del self.memory_items[memory_id]
                        
                        # Remove relationships
                        self._delete_relationships(memory_id)
                    else:
                        # Remove from Firestore
                        self.memory_items_collection.document(memory_id).delete()
                        
                        # Remove relationships
                        self._delete_relationships(memory_id)
                
                logger.info(f"Permanently deleted memory item {memory_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete memory item {memory_id}: {str(e)}")
                return False
        else:
            # Archive instead of delete
            if tier == TIER_ARCHIVAL:
                # Already archived
                return True
            
            # Move to archival tier
            return self.update(memory_id, metadata={
                "current_tier": TIER_ARCHIVAL,
                "archived_at": datetime.datetime.now(),
                "ttl": None  # Remove TTL for archival items
            })
    
    def create_context(self,
                      name: str,
                      description: str = None,
                      initial_memory_ids: List[str] = None) -> str:
        """
        Create a new memory context
        
        Args:
            name: Context name
            description: Optional description
            initial_memory_ids: Initial memory items to include
            
        Returns:
            context_id: Identifier of the created context
        """
        context_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        context = {
            "context_id": context_id,
            "name": name,
            "description": description or "",
            "active_memory_ids": initial_memory_ids or [],
            "metadata": {
                "created_at": now,
                "updated_at": now,
                "creator_id": "system",
                "is_active": True
            }
        }
        
        try:
            if self.use_mock:
                # Store in mock storage
                self.memory_contexts[context_id] = context
                logger.info(f"Created memory context {context_id} in mock storage")
            else:
                # Store in Firestore
                self.memory_contexts_collection.document(context_id).set(context)
                logger.info(f"Created memory context {context_id} in Firestore")
            
            return context_id
        except Exception as e:
            logger.error(f"Failed to create memory context: {str(e)}")
            
            # Fallback to mock storage in case of error
            if not self.use_mock:
                self.memory_contexts[context_id] = context
                logger.warning(f"Created memory context {context_id} in fallback mock storage")
                return context_id
            
            return None
    
    def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        Get a memory context
        
        Args:
            context_id: Context identifier
            
        Returns:
            Context data
        """
        try:
            if self.use_mock:
                # Get from mock storage
                if context_id in self.memory_contexts:
                    return self.memory_contexts[context_id]
                else:
                    logger.warning(f"Memory context {context_id} not found in mock storage")
                    return None
            else:
                # Get from Firestore
                doc_ref = self.memory_contexts_collection.document(context_id)
                doc = doc_ref.get()
                
                if not doc.exists:
                    logger.warning(f"Memory context {context_id} not found in Firestore")
                    return None
                
                return doc.to_dict()
        except Exception as e:
            logger.error(f"Failed to get memory context {context_id}: {str(e)}")
            return None
    
    def add_to_context(self, memory_id: str, context_id: str) -> bool:
        """
        Add a memory item to a context
        
        Args:
            memory_id: Memory item identifier
            context_id: Context identifier
            
        Returns:
            Whether the operation was successful
        """
        return self._add_to_context(memory_id, context_id)
    
    def remove_from_context(self, memory_id: str, context_id: str) -> bool:
        """
        Remove a memory item from a context
        
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
                    
                    # Remove the memory ID
                    if memory_id in active_memory_ids:
                        active_memory_ids.remove(memory_id)
                        
                        # Update the context
                        context_data["active_memory_ids"] = active_memory_ids
                        context_data["metadata"]["updated_at"] = datetime.datetime.now()
                        
                        logger.debug(f"Removed memory item {memory_id} from context {context_id} in mock storage")
                    
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
                
                # Remove the memory ID
                if memory_id in active_memory_ids:
                    active_memory_ids.remove(memory_id)
                    
                    # Update the context
                    context_ref.update({
                        "active_memory_ids": active_memory_ids,
                        "metadata.updated_at": datetime.datetime.now()
                    })
                    
                    logger.debug(f"Removed memory item {memory_id} from context {context_id} in Firestore")
                
                return True
        except Exception as e:
            logger.error(f"Failed to remove memory item from context: {str(e)}")
            return False
    
    def _store_relationships(self, memory_id: str, relationships: List[Dict[str, Any]]) -> None:
        """
        Store relationships for a memory item
        
        Args:
            memory_id: Memory item identifier
            relationships: List of relationships
        """
        try:
            # Delete existing relationships
            self._delete_relationships(memory_id)
            
            if self.use_mock:
                # Store new relationships in mock storage
                for rel in relationships:
                    rel_id = str(uuid.uuid4())
                    rel_data = {
                        "relationship_id": rel_id,
                        "source_id": memory_id,
                        "target_id": rel.get("related_memory_id"),
                        "relationship_type": rel.get("relationship_type", "references"),
                        "strength": rel.get("strength", 0.5),
                        "created_at": datetime.datetime.now()
                    }
                    
                    # Add to mock relationships
                    self.memory_relationships[rel_id] = rel_data
                
                logger.debug(f"Stored {len(relationships)} relationships for memory item {memory_id} in mock storage")
            else:
                # Store new relationships in Firestore
                batch = self.db.batch()
                
                for rel in relationships:
                    rel_id = str(uuid.uuid4())
                    rel_data = {
                        "relationship_id": rel_id,
                        "source_id": memory_id,
                        "target_id": rel.get("related_memory_id"),
                        "relationship_type": rel.get("relationship_type", "references"),
                        "strength": rel.get("strength", 0.5),
                        "created_at": datetime.datetime.now()
                    }
                    
                    # Add to batch
                    batch.set(self.memory_relationships_collection.document(rel_id), rel_data)
                
                # Commit batch
                batch.commit()
                
                logger.debug(f"Stored {len(relationships)} relationships for memory item {memory_id} in Firestore")
        except Exception as e:
            logger.error(f"Failed to store relationships: {str(e)}")
    
    def _delete_relationships(self, memory_id: str) -> None:
        """
        Delete all relationships for a memory item
        
        Args:
            memory_id: Memory item identifier
        """
        try:
            if self.use_mock:
                # Find and delete relationships in mock storage
                rel_ids_to_delete = []
                
                for rel_id, rel in self.memory_relationships.items():
                    if rel.get("source_id") == memory_id or rel.get("target_id") == memory_id:
                        rel_ids_to_delete.append(rel_id)
                
                # Delete relationships
                for rel_id in rel_ids_to_delete:
                    del self.memory_relationships[rel_id]
                
                logger.debug(f"Deleted relationships for memory item {memory_id} from mock storage")
            else:
                # Find all relationships where this memory is the source or target
                source_query = self.memory_relationships_collection.where("source_id", "==", memory_id)
                target_query = self.memory_relationships_collection.where("target_id", "==", memory_id)
                
                # Delete in batches
                batch = self.db.batch()
                
                # Source relationships
                for doc in source_query.stream():
                    batch.delete(doc.reference)
                
                # Target relationships
                for doc in target_query.stream():
                    batch.delete(doc.reference)
                
                # Commit batch
                batch.commit()
                
                logger.debug(f"Deleted relationships for memory item {memory_id} from Firestore")
        except Exception as e:
            logger.error(f"Failed to delete relationships: {str(e)}")
    
    def _matches_query(self, item: Dict[str, Any], query_text: str = None, 
                      filters: Dict[str, Any] = None, context_id: str = None) -> bool:
        """
        Check if a memory item matches query criteria
        
        Args:
            item: Memory item to check
            query_text: Text to search for
            filters: Dictionary of field filters
            context_id: Context to match
            
        Returns:
            Whether the item matches the query
        """
        # Check text match
        if query_text and not self._text_matches(item, query_text):
            return False
        
        # Check filters
        if filters and not self._apply_filters(item, filters):
            return False
        
        # Check context
        if context_id:
            # For mock mode or simple checking, we don't verify context membership
            # In a full implementation, we would check if the item is in the context
            pass
        
        return True
    
    def _apply_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Apply filters to check if an item matches
        
        Args:
            item: Memory item to check
            filters: Dictionary of field filters
            
        Returns:
            Whether the item matches the filters
        """
        for field, value in filters.items():
            if isinstance(value, dict) and 'operator' in value:
                # Complex filter with operator
                op = value['operator']
                filter_value = value['value']
                
                # Get field value using dot notation
                field_parts = field.split('.')
                field_value = item
                for part in field_parts:
                    if isinstance(field_value, dict) and part in field_value:
                        field_value = field_value[part]
                    else:
                        field_value = None
                        break
                
                # Apply operator
                if op == "==":
                    if field_value != filter_value:
                        return False
                elif op == "!=":
                    if field_value == filter_value:
                        return False
                elif op == ">":
                    if not (field_value > filter_value):
                        return False
                elif op == ">=":
                    if not (field_value >= filter_value):
                        return False
                elif op == "<":
                    if not (field_value < filter_value):
                        return False
                elif op == "<=":
                    if not (field_value <= filter_value):
                        return False
                elif op == "in":
                    if field_value not in filter_value:
                        return False
                elif op == "not-in":
                    if field_value in filter_value:
                        return False
                elif op == "contains":
                    if not isinstance(field_value, (list, str)) or filter_value not in field_value:
                        return False
                else:
                    # Unsupported operator
                    return False
            else:
                # Simple equality filter
                field_parts = field.split('.')
                field_value = item
                for part in field_parts:
                    if isinstance(field_value, dict) and part in field_value:
                        field_value = field_value[part]
                    else:
                        field_value = None
                        break
                
                if field_value != value:
                    return False
        
        return True
    
    def _text_matches(self, item: Dict[str, Any], query_text: str) -> bool:
        """
        Check if a memory item matches a text query
        
        Args:
            item: Memory item to check
            query_text: Text to search for
            
        Returns:
            Whether the item matches the text query
        """
        query_text = query_text.lower()
        
        # Check in content
        content = item.get("content", {})
        if isinstance(content, dict):
            # Try to convert to string for searching
            content_str = json.dumps(content)
        else:
            content_str = str(content)
        
        if query_text in content_str.lower():
            return True
        
        # Check in tags
        tags = item.get("tags", [])
        for tag in tags:
            if query_text in tag.lower():
                return True
        
        # Check in relationships
        relationships = item.get("relationships", [])
        for rel in relationships:
            if "relationship_type" in rel and query_text in rel["relationship_type"].lower():
                return True
        
        return False
        
    def _add_to_cache(self, memory_id: str, memory_item: Dict[str, Any]) -> None:
        """
        Add a memory item to the cache
        
        Args:
            memory_id: Memory item identifier
            memory_item: Memory item data
        """
        # Add to cache
        self.cache[memory_id] = memory_item
        
        # Trim cache if needed
        if len(self.cache) > self.cache_size:
            # Remove least recently used item
            lru_id = min(self.cache.keys(), 
                        key=lambda x: self.cache[x].get("metadata", {}).get("last_accessed", 
                                                                        datetime.datetime.min))
            del self.cache[lru_id]
    
    def _update_access_metadata(self, memory_id: str, memory_item: Dict[str, Any]) -> None:
        """
        Update access metadata for a memory item
        
        Args:
            memory_id: Memory item identifier
            memory_item: Memory item data
        """
        now = datetime.datetime.now()
        
        # Update in the object
        if "metadata" not in memory_item:
            memory_item["metadata"] = {}
        
        memory_item["metadata"]["last_accessed"] = now
        memory_item["metadata"]["access_count"] = memory_item["metadata"].get("access_count", 0) + 1
        
        # Recalculate importance score
        self._recalculate_importance(memory_id, memory_item)
        
        # Update in storage
        tier = memory_item.get("metadata", {}).get("current_tier", TIER_WORKING)
        
        if tier == TIER_EPHEMERAL:
            # No persistence needed for ephemeral
            pass
        else:
            # Update in persistent storage
            try:
                if self.use_mock:
                    # Update in mock storage
                    if memory_id in self.memory_items:
                        self.memory_items[memory_id]["metadata"]["last_accessed"] = now
                        self.memory_items[memory_id]["metadata"]["access_count"] = memory_item["metadata"]["access_count"]
                        self.memory_items[memory_id]["metadata"]["importance_score"] = memory_item["metadata"]["importance_score"]
                else:
                    # Update in Firestore
                    self.memory_items_collection.document(memory_id).update({
                        "metadata.last_accessed": now,
                        "metadata.access_count": memory_item["metadata"]["access_count"],
                        "metadata.importance_score": memory_item["metadata"]["importance_score"]
                    })
            except Exception as e:
                logger.error(f"Failed to update access metadata: {str(e)}")
        
        # Check if tier transition is needed
        self._check_tier_transition(memory_id, memory_item)
    
    def _recalculate_importance(self, memory_id: str, memory_item: Dict[str, Any]) -> None:
        """
        Recalculate importance score for a memory item
        
        Args:
            memory_id: Memory item identifier
            memory_item: Memory item data
        """
        if "metadata" not in memory_item:
            return
        
        metadata = memory_item["metadata"]
        
        # Start with existing score or default
        current_score = metadata.get("importance_score", 0.5)
        
        # Factors to consider
        access_count = metadata.get("access_count", 0)
        relationship_count = len(memory_item.get("relationships", []))
        tag_count = len(memory_item.get("tags", []))
        explicit_importance = metadata.get("explicit_importance", None)
        
        # Check recency of access
        now = datetime.datetime.now()
        last_accessed = metadata.get("last_accessed", now)
        recency_days = (now - last_accessed).total_seconds() / 86400 if isinstance(last_accessed, datetime.datetime) else 30
        
        # Calculate new score
        new_score = current_score
        
        # Recency factor (higher for more recent)
        recency_factor = max(0, 1 - (recency_days / 30))  # 0 to 1, 1 if accessed today
        new_score = new_score * 0.7 + recency_factor * 0.3
        
        # Access count factor
        if access_count > 0:
            access_factor = min(1, access_count / 10)  # Caps at 10 accesses
            new_score = new_score * 0.8 + access_factor * 0.2
        
        # Relationship factor
        if relationship_count > 0:
            rel_factor = min(1, relationship_count / 5)  # Caps at 5 relationships
            new_score = new_score * 0.9 + rel_factor * 0.1
        
        # Tag factor
        if tag_count > 0:
            tag_factor = min(1, tag_count / 5)  # Caps at 5 tags
            new_score = new_score * 0.95 + tag_factor * 0.05
        
        # Explicit importance override
        if explicit_importance is not None:
            new_score = explicit_importance
        
        # Update the score
        memory_item["metadata"]["importance_score"] = new_score
    
    def _check_tier_transition(self, memory_id: str, memory_item: Dict[str, Any]) -> None:
        """
        Check if a memory item should transition between tiers
        
        Args:
            memory_id: Memory item identifier
            memory_item: Memory item data
        """
        if "metadata" not in memory_item:
            return
        
        metadata = memory_item["metadata"]
        current_tier = metadata.get("current_tier", TIER_WORKING)
        importance_score = metadata.get("importance_score", 0.5)
        
        # Check for transitions
        if current_tier == TIER_EPHEMERAL and importance_score >= IMPORTANCE_THRESHOLDS["t0_to_t1"]:
            # Tier 0 -> Tier 1: Important ephemeral memory becomes working memory
            self._transition_tier(memory_id, memory_item, TIER_WORKING)
        
        elif current_tier == TIER_WORKING and importance_score >= IMPORTANCE_THRESHOLDS["t1_to_t2"]:
            # Tier 1 -> Tier 2: Important working memory becomes reference memory
            self._transition_tier(memory_id, memory_item, TIER_REFERENCE)
        
        elif current_tier == TIER_REFERENCE and importance_score <= IMPORTANCE_THRESHOLDS["t2_to_t3"]:
            # Tier 2 -> Tier 3: Unimportant reference memory becomes archival
            self._transition_tier(memory_id, memory_item, TIER_ARCHIVAL)
    
    def _transition_tier(self, memory_id: str, memory_item: Dict[str, Any], new_tier: int) -> None:
        """
        Transition a memory item to a new tier
        
        Args:
            memory_id: Memory item identifier
            memory_item: Memory item data
            new_tier: New tier to transition to
        """
        current_tier = memory_item.get("metadata", {}).get("current_tier", TIER_WORKING)
        
        # Skip if already in the target tier
        if current_tier == new_tier:
            return
        
        logger.info(f"Transitioning memory item {memory_id} from tier {current_tier} to tier {new_tier}")
        
        # Update tier in the object
        memory_item["metadata"]["current_tier"] = new_tier
        memory_item["metadata"]["tier_transition_at"] = datetime.datetime.now()
        
        # Handle the transition
        if current_tier == TIER_EPHEMERAL and new_tier > TIER_EPHEMERAL:
            # Ephemeral -> Persistent: Store in persistent storage
            try:
                if self.use_mock:
                    # Store in mock storage
                    self.memory_items[memory_id] = memory_item
                    
                    # Remove from ephemeral memory
                    if memory_id in self.ephemeral_memory:
                        del self.ephemeral_memory[memory_id]
                    
                    logger.debug(f"Moved memory item {memory_id} from ephemeral to mock storage")
                else:
                    # Store in Firestore
                    self.memory_items_collection.document(memory_id).set(memory_item)
                    
                    # Remove from ephemeral memory
                    if memory_id in self.ephemeral_memory:
                        del self.ephemeral_memory[memory_id]
                    
                    logger.debug(f"Moved memory item {memory_id} from ephemeral to Firestore")
            except Exception as e:
                logger.error(f"Failed to transition memory item {memory_id} to tier {new_tier}: {str(e)}")
        else:
            # Update tier in persistent storage
            try:
                # Calculate new TTL if applicable
                ttl = None
                if new_tier in DEFAULT_TTL and DEFAULT_TTL[new_tier] is not None:
                    ttl = datetime.datetime.now() + datetime.timedelta(days=DEFAULT_TTL[new_tier])
                
                if self.use_mock:
                    # Update in mock storage
                    if memory_id in self.memory_items:
                        self.memory_items[memory_id]["metadata"]["current_tier"] = new_tier
                        self.memory_items[memory_id]["metadata"]["tier_transition_at"] = datetime.datetime.now()
                        self.memory_items[memory_id]["metadata"]["ttl"] = ttl
                    
                    logger.debug(f"Updated memory item {memory_id} tier to {new_tier} in mock storage")
                else:
                    # Update in Firestore
                    self.memory_items_collection.document(memory_id).update({
                        "metadata.current_tier": new_tier,
                        "metadata.tier_transition_at": datetime.datetime.now(),
                        "metadata.ttl": ttl
                    })
                    
                    logger.debug(f"Updated memory item {memory_id} tier to {new_tier} in Firestore")
            except Exception as e:
                logger.error(f"Failed to update memory item {memory_id} tier: {str(e)}")
    
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
                        context_data["metadata"]["updated_at"] = datetime.datetime.now()
                        
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
                        "metadata.updated_at": datetime.datetime.now()
                    })
                    
                    logger.debug(f"Added memory item {memory_id} to context {context_id} in Firestore")
                
                return True
        except Exception as e:
            logger.error(f"Failed to add memory item to context: {str(e)}")
            return False

def create_memory_system(
    project_id=None, 
    collection_prefix="", 
    use_emulator=False, 
    use_mock=False,
    cache_size=1000
) -> UnifiedMemorySystem:
    """
    Create a unified memory system instance with robust error handling
    
    Args:
        project_id: Google Cloud project ID
        collection_prefix: Collection prefix
        use_emulator: Whether to use the Firestore emulator
        use_mock: Whether to use mock mode
        cache_size: Memory cache size
        
    Returns:
        UnifiedMemorySystem instance
    """
    try:
        memory_system = UnifiedMemorySystem(
            project_id=project_id,
            collection_prefix=collection_prefix,
            use_emulator=use_emulator,
            use_mock=use_mock,
            cache_size=cache_size
        )
        return memory_system
    except Exception as e:
        logger.error(f"Error creating memory system: {str(e)}")
        # Create with mock mode as fallback
        return UnifiedMemorySystem(
            project_id=None,
            collection_prefix="",
            use_mock=True,
            cache_size=cache_size
        )    