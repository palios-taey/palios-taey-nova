class TaskRouter:
    """Simple stub implementation of the Task Router."""
    def __init__(self, model_registry):
        self.model_registry = model_registry
    
    def analyze_task(self, task_description):
        """Stub implementation of task analysis."""
        return {
            "primary_capability": "text-generation",
            "confidence": 0.8,
            "all_capabilities": [("text-generation", 0.8)]
        }
    
    def route_task(self, task_description, model_id=None):
        """Stub implementation of task routing."""
        task_analysis = self.analyze_task(task_description)
        
        # Prepare a mock result
        return {
            "task_description": task_description,
            "analysis": task_analysis,
            "result": {
                "model_used": model_id or "claude",
                "capability": task_analysis["primary_capability"],
                "result": f"Mock result for: {task_description[:30]}...",
                "success": True
            }
        }
