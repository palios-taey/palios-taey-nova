class MemorySystem:
    """Simple stub implementation of the Memory System."""
    def __init__(self, project_id):
        self.project_id = project_id
    
    def store_memory(self, content, context_id="default_context", tier="working", metadata=None):
        """Stub implementation of memory storage."""
        if metadata is None:
            metadata = {}
        
        # Return a mock memory ID
        return "memory-" + content[:8].replace(" ", "-")
    
    def retrieve_memory(self, memory_id):
        """Stub implementation of memory retrieval."""
        return {
            "memory_id": memory_id,
            "content": "Mock memory content",
            "context_id": "default_context",
            "tier": "working",
            "metadata": {}
        }
    
    def list_memories(self, context_id="default_context", limit=10):
        """Stub implementation of memory listing."""
        return []
