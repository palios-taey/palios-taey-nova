"""Data models for the Memory Service."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MemoryTier(str, Enum):
    """Memory storage tiers with different performance and cost characteristics."""
    
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
    ARCHIVAL = "archival"


class MemoryItem(BaseModel):
    """Base model for items stored in the memory system."""
    
    id: str = Field(..., description="Unique identifier for the memory item")
    content: Any = Field(..., description="Content of the memory item")
    content_type: str = Field(..., description="MIME type or format of the content")
    tier: MemoryTier = Field(
        default=MemoryTier.WORKING, description="Current storage tier"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the item"
    )
    access_count: int = Field(
        default=0, description="Number of times this item has been accessed"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class MemoryQuery(BaseModel):
    """Query parameters for searching the memory system."""
    
    content_type: Optional[str] = Field(
        None, description="Filter by content type"
    )
    tier: Optional[MemoryTier] = Field(
        None, description="Filter by memory tier"
    )
    tags: Optional[List[str]] = Field(
        None, description="Filter by tags (all tags must match)"
    )
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
    metadata_filters: Optional[Dict[str, Any]] = Field(
        None, description="Filter by metadata fields"
    )
    limit: int = Field(
        default=100, description="Maximum number of results to return"
    )
    offset: int = Field(
        default=0, description="Number of results to skip"
    )


class MemoryUpdateRequest(BaseModel):
    """Request model for updating a memory item."""
    
    content: Optional[Any] = Field(None, description="New content")
    content_type: Optional[str] = Field(None, description="New content type")
    tier: Optional[MemoryTier] = Field(None, description="New storage tier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
