"""API router for PALIOS-TAEY."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from palios_taey.core.errors import NotFoundError, ValidationError
from palios_taey.memory.models import MemoryItem, MemoryQuery, MemoryTier, MemoryUpdateRequest
from palios_taey.memory.service import MemoryService


router = APIRouter()
memory_service = MemoryService()


@router.post("/memory", response_model=MemoryItem, status_code=201)
async def create_memory_item(item: MemoryItem):
    """Create a new memory item."""
    try:
        return memory_service.create(item)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memory/{item_id}", response_model=MemoryItem)
async def get_memory_item(item_id: str):
    """Get a memory item by ID."""
    try:
        return memory_service.get(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/memory/{item_id}", response_model=MemoryItem)
async def update_memory_item(item_id: str, update: MemoryUpdateRequest):
    """Update a memory item."""
    try:
        return memory_service.update(item_id, update)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/memory/{item_id}", status_code=204)
async def delete_memory_item(item_id: str):
    """Delete a memory item."""
    try:
        memory_service.delete(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/memory", response_model=List[MemoryItem])
async def search_memory_items(
    content_type: Optional[str] = None,
    tier: Optional[MemoryTier] = None,
    tags: Optional[List[str]] = Query(None),
    limit: int = 100,
    offset: int = 0,
):
    """Search for memory items."""
    query = MemoryQuery(
        content_type=content_type,
        tier=tier,
        tags=tags,
        limit=limit,
        offset=offset,
    )
    return memory_service.search(query)


@router.post("/memory/{item_id}/tier/{tier}", response_model=MemoryItem)
async def migrate_memory_tier(item_id: str, tier: MemoryTier):
    """Migrate a memory item to a different tier."""
    try:
        return memory_service.migrate_tier(item_id, tier)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
