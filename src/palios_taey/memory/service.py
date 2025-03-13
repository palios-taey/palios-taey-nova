"""Memory Service implementation."""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from palios_taey.core.errors import NotFoundError, ValidationError
from palios_taey.memory.models import MemoryItem, MemoryQuery, MemoryTier, MemoryUpdateRequest


class MemoryService:
    """Service for managing memory items across different tiers."""
    
    def __init__(self):
        """Initialize the memory service."""
        self._storage: Dict[str, MemoryItem] = {}
    
    def create(self, item: MemoryItem) -> MemoryItem:
        """
        Create a new memory item.
        
        Args:
            item: The memory item to create
            
        Returns:
            The created memory item
            
        Raises:
            ValidationError: If an item with the same ID already exists
        """
        if item.id in self._storage:
            raise ValidationError(f"Memory item with ID '{item.id}' already exists")
        
        self._storage[item.id] = item
        return item
    
    def get(self, item_id: str) -> MemoryItem:
        """
        Retrieve a memory item by ID.
        
        Args:
            item_id: The ID of the memory item to retrieve
            
        Returns:
            The retrieved memory item
            
        Raises:
            NotFoundError: If no item with the given ID exists
        """
        if item_id not in self._storage:
            raise NotFoundError(f"Memory item with ID '{item_id}' not found")
        
        item = self._storage[item_id]
        item.access_count += 1
        return item
    
    def update(self, item_id: str, update: MemoryUpdateRequest) -> MemoryItem:
        """
        Update a memory item.
        
        Args:
            item_id: The ID of the memory item to update
            update: The update request
            
        Returns:
            The updated memory item
            
        Raises:
            NotFoundError: If no item with the given ID exists
        """
        if item_id not in self._storage:
            raise NotFoundError(f"Memory item with ID '{item_id}' not found")
        
        item = self._storage[item_id]
        
        if update.content is not None:
            item.content = update.content
        
        if update.content_type is not None:
            item.content_type = update.content_type
        
        if update.tier is not None:
            item.tier = update.tier
        
        if update.metadata is not None:
            item.metadata = update.metadata
        
        if update.tags is not None:
            item.tags = update.tags
        
        item.updated_at = datetime.utcnow()
        return item
    
    def delete(self, item_id: str) -> None:
        """
        Delete a memory item.
        
        Args:
            item_id: The ID of the memory item to delete
            
        Raises:
            NotFoundError: If no item with the given ID exists
        """
        if item_id not in self._storage:
            raise NotFoundError(f"Memory item with ID '{item_id}' not found")
        
        del self._storage[item_id]
    
    def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Search for memory items based on query parameters.
        
        Args:
            query: The search query
            
        Returns:
            A list of matching memory items
        """
        results = list(self._storage.values())
        
        if query.content_type is not None:
            results = [item for item in results if item.content_type == query.content_type]
        
        if query.tier is not None:
            results = [item for item in results if item.tier == query.tier]
        
        if query.tags is not None and query.tags:
            results = [
                item for item in results
                if all(tag in item.tags for tag in query.tags)
            ]
        
        if query.created_after is not None:
            results = [
                item for item in results
                if item.created_at >= query.created_after
            ]
        
        if query.created_before is not None:
            results = [
                item for item in results
                if item.created_at <= query.created_before
            ]
        
        if query.metadata_filters is not None:
            results = [
                item for item in results
                if all(
                    k in item.metadata and item.metadata[k] == v
                    for k, v in query.metadata_filters.items()
                )
            ]
        
        # Apply pagination
        return results[query.offset:query.offset + query.limit]
    
    def migrate_tier(self, item_id: str, new_tier: MemoryTier) -> MemoryItem:
        """
        Migrate a memory item to a different storage tier.
        
        Args:
            item_id: The ID of the memory item to migrate
            new_tier: The target storage tier
            
        Returns:
            The migrated memory item
            
        Raises:
            NotFoundError: If no item with the given ID exists
        """
        if item_id not in self._storage:
            raise NotFoundError(f"Memory item with ID '{item_id}' not found")
        
        item = self._storage[item_id]
        item.tier = new_tier
        item.updated_at = datetime.utcnow()
        return item
