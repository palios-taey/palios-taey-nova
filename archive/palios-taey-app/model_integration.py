import os
import requests
import json
from typing import Dict, List, Any, Optional

class ModelCapability:
    """Represents a specific capability of an AI model."""
    def __init__(self, name: str, description: str, confidence: float = 0.0):
        self.name = name
        self.description = description
        self.confidence = confidence  # Confidence score (0.0-1.0)
        self.performance_history = []  # Track performance
    
    def update_confidence(self, new_score: float):
        """Update confidence score based on observed performance."""
        # Simple moving average
        self.performance_history.append(new_score)
        # Only keep last 10 records
        if len(self.performance_history) > 10:
            self.performance_history = self.performance_history[-10:]
        # Update confidence score
        self.confidence = sum(self.performance_history) / len(self.performance_history)
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "confidence": self.confidence
        }

class AIModel:
    """Base class for AI model integration."""
    def __init__(self, model_id: str, name: str, description: str):
        self.model_id = model_id
        self.name = name
        self.description = description
        self.capabilities = {}  # name -> ModelCapability
        self.available = True
    
    def add_capability(self, name: str, description: str, confidence: float = 0.7):
        """Add a capability to this model."""
        self.capabilities[name] = ModelCapability(name, description, confidence)
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if model has a specific capability."""
        return capability_name in self.capabilities
    
    def get_capability_confidence(self, capability_name: str) -> float:
        """Get confidence score for a capability."""
        if not self.has_capability(capability_name):
            return 0.0
        return self.capabilities[capability_name].confidence
    
    def execute(self, task: Dict) -> Dict:
        """Execute a task - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def to_dict(self):
        return {
            "model_id": self.model_id,
            "name": self.name,
            "description": self.description,
            "capabilities": {name: cap.to_dict() for name, cap in self.capabilities.items()},
            "available": self.available
        }

class ClaudeModel(AIModel):
    """Integration with Claude API."""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("claude", "Claude", "Anthropic's Claude large language model")
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY", "")
        self.api_url = "https://api.anthropic.com/v1/messages"
        
        # Add capabilities
        self.add_capability("text-generation", "Generate high-quality text content")
        self.add_capability("reasoning", "Complex reasoning and problem-solving")
        self.add_capability("summarization", "Summarize content effectively")
        self.add_capability("creative-writing", "Generate creative content")
        self.add_capability("structured-data", "Work with structured data formats")
    
    def execute(self, task: Dict) -> Dict:
        """Execute a task using Claude API."""
        # Simple mock implementation for now
        if not task.get("prompt"):
            return {"error": "Prompt is required"}
        
        # In a real implementation, would call the Claude API
        # For now, just return a mock response
        return {
            "model": "claude",
            "result": f"Mock response for: {task['prompt'][:30]}...",
            "success": True
        }

class GrokModel(AIModel):
    """Integration with Grok API."""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("grok", "Grok", "Grok AI by xAI")
        self.api_key = api_key or os.environ.get("GROK_API_KEY", "")
        
        # Add capabilities
        self.add_capability("internet-search", "Search the internet for information")
        self.add_capability("knowledge-retrieval", "Retrieve factual knowledge")
        self.add_capability("analysis", "Analyze and interpret data")
    
    def execute(self, task: Dict) -> Dict:
        """Execute a task using Grok API."""
        # Simple mock implementation for now
        if not task.get("query"):
            return {"error": "Query is required"}
        
        # In a real implementation, would call the Grok API
        # For now, just return a mock response
        return {
            "model": "grok",
            "result": f"Mock Grok result for: {task['query'][:30]}...",
            "success": True
        }

class ModelRegistry:
    """Registry of available AI models and their capabilities."""
    def __init__(self):
        self.models = {}  # model_id -> AIModel
    
    def register_model(self, model: AIModel):
        """Register a model in the registry."""
        self.models[model.model_id] = model
    
    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get a model by ID."""
        return self.models.get(model_id)
    
    def find_best_model(self, capability: str) -> Optional[AIModel]:
        """Find the best model for a given capability."""
        best_model = None
        best_confidence = 0.0
        
        for model in self.models.values():
            if not model.available:
                continue
                
            confidence = model.get_capability_confidence(capability)
            if confidence > best_confidence:
                best_confidence = confidence
                best_model = model
        
        return best_model
    
    def execute_task(self, task: Dict) -> Dict:
        """Execute a task using the best model for the required capability."""
        capability = task.get("capability", "text-generation")
        model_id = task.get("model_id")
        
        if model_id:
            # Use specified model if available
            model = self.get_model(model_id)
            if not model or not model.available:
                return {"error": f"Model {model_id} not available"}
        else:
            # Find best model for capability
            model = self.find_best_model(capability)
            if not model:
                return {"error": f"No model available for capability: {capability}"}
        
        # Execute task with selected model
        result = model.execute(task)
        return {
            "model_used": model.model_id,
            "capability": capability,
            **result
        }
    
    def list_models(self) -> List[Dict]:
        """List all registered models."""
        return [model.to_dict() for model in self.models.values()]
